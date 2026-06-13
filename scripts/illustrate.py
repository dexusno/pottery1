#!/usr/bin/env python3
"""
illustrate.py - Generate or restyle a figure with gpt-image-2.

GENERATE (text-to-image, for style-anchor candidates):
    python illustrate.py --generate "<prompt>" <output_png> [--quality medium] [size]

EDIT (restyle a figure, optionally against a style reference):
    python illustrate.py <content_image> <output_png> "<prompt>" [--style-ref <png>] [--quality medium] [size]
  Content image is Image 1 (what to depict); style ref, if given, is Image 2 (how
  it looks). Reference inputs by index in the prompt.

BATCH (restyle many figures CONCURRENTLY -- much faster for multi-figure sheets):
    python illustrate.py --batch <manifest.json> [--workers 4] [--dry-run]
  manifest.json is a list of jobs:
    [{"content": "<crop.png>", "out": "<out.png>", "prompt": "<...>",
      "quality": "medium", "style_ref": "style/anchor.png", "size": null}, ...]
  Jobs run in a thread pool (default 4 workers; raise/lower for your OpenAI rate
  limits). All jobs are attempted; every failure is reported and the script exits
  non-zero if ANY job failed. --dry-run prints the plan without calling the API.

  SIZE: if omitted, it is derived from the content image -- aspect ratio matched
  (so the figure is not distorted) and the long side scaled to the crop's own
  resolution (2x the crop's longest side, clamped 512..1024, /16): small icons
  generate smaller and faster; detailed figures keep full resolution.

Notes:
- input_fidelity is LOCKED on gpt-image-2 (always high); do NOT pass it.
- quality: low (fast), medium (default), high (label-heavy / diagrams).
- No transparent background; PNG on opaque background.
- size = WxH, both divisible by 16, aspect within 1:3..3:1.

Requires OPENAI_API_KEY; gpt-image-2 needs OpenAI Org Verification.
"""
import base64
import json
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from PIL import Image
from openai import OpenAI

MAX_LONG = 1024      # target ceiling for the longest side of generated figures
MIN_LONG = 512       # pre-floor target floor for the longest side
MIN_PIX = 655_360    # gpt-image-2 hard minimum total pixel budget
MAX_PIX = 8_294_400  # gpt-image-2 hard maximum total pixel budget


def snap16(v):
    return max(256, int(round(v / 16) * 16))


def snap16_up(v):
    return int(math.ceil(v / 16) * 16)


def aspect_size(img_path):
    """Valid gpt-image-2 size: aspect matched to the image, long side scaled to
    the crop's own resolution (2x longest side, clamped MIN_LONG..MAX_LONG),
    then scaled UP if needed to satisfy the API's minimum total pixel budget
    (small/wide/tall crops would otherwise snap below it and be rejected)."""
    w, h = Image.open(img_path).size
    long_side = min(MAX_LONG, max(MIN_LONG, snap16(2 * max(w, h))))
    ratio = max(1 / 3, min(3.0, w / h))  # clamp to allowed aspect band
    if w >= h:
        W, H = long_side, snap16(long_side / ratio)
    else:
        W, H = snap16(long_side * ratio), long_side
    if W * H < MIN_PIX:
        f = (MIN_PIX / (W * H)) ** 0.5
        if W >= H:  # scale long side, derive short to keep aspect <= 3 AND pixels >= floor
            W = snap16_up(W * f)
            H = snap16_up(max(W / 3.0, MIN_PIX / W))
        else:
            H = snap16_up(H * f)
            W = snap16_up(max(H / 3.0, MIN_PIX / H))
    return f"{W}x{H}"


def write_b64(item, out_path):
    b64 = getattr(item, "b64_json", None)
    if not b64:
        print("error: no image data returned")
        sys.exit(1)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(base64.b64decode(b64))


def edit_one(client, content_path, out_path, prompt, quality, style_ref,
             size=None, mode="edit"):
    """One figure call. mode='edit' restyles the crop in place (faithful);
    mode='generate' re-interprets the subject in the anchor's style using the
    crop + anchor as references. Size is computed identically for both modes so
    figures fit the document the same way. Returns (out_path, size, seconds)."""
    content_path, out_path = Path(content_path), Path(out_path)
    size = size or aspect_size(content_path)   # same sizing for both modes
    sr = Path(style_ref) if style_ref else None
    files = [open(content_path, "rb")]
    if sr and sr.exists():
        files.append(open(sr, "rb"))
    image_arg = files if len(files) > 1 else files[0]
    # Both modes use the edit endpoint with crop + anchor as references; what
    # differs is the PROMPT the illustrator supplies (edit = faithful restyle of
    # the crop; generate = re-interpret the subject in the anchor's style). `mode`
    # is carried for logging/clarity and future divergence.
    t0 = time.time()
    try:
        resp = client.images.edit(model="gpt-image-2", image=image_arg,
                                   prompt=prompt, size=size, quality=quality)
    finally:
        for f in files:
            f.close()
    write_b64(resp.data[0], out_path)
    return out_path, size, time.time() - t0


def run_batch(client, manifest_path, workers, dry_run):
    try:
        jobs = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"BATCH FAILED: manifest not found: {manifest_path}")
        sys.exit(1)
    except Exception as e:
        print(f"BATCH FAILED: manifest is not valid JSON: {e}")
        sys.exit(1)
    if not isinstance(jobs, list) or not jobs:
        print("BATCH FAILED: manifest must be a non-empty JSON list of jobs")
        sys.exit(1)
    for i, j in enumerate(jobs):
        for key in ("content", "out", "prompt"):
            if key not in j:
                print(f"BATCH FAILED: job {i} missing required key '{key}'")
                sys.exit(1)
        if not Path(j["content"]).is_file():
            print(f"BATCH FAILED: job {i} content file not found: {j['content']}")
            sys.exit(1)  # caught BEFORE any API spend
    if dry_run:
        print(f"plan: {len(jobs)} job(s), {workers} worker(s)")
        for j in jobs:
            size = j.get("size") or aspect_size(j["content"])
            print(f"  {j['content']} -> {j['out']}  "
                  f"(mode={j.get('mode', 'edit')}, size={size}, "
                  f"quality={j.get('quality', 'medium')}, "
                  f"style_ref={j.get('style_ref') or '-'})")
        return
    failures = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(edit_one, client, j["content"], j["out"], j["prompt"],
                            j.get("quality", "medium"), j.get("style_ref"),
                            j.get("size"), j.get("mode", "edit")): j for j in jobs}
        for fut in as_completed(futs):
            j = futs[fut]
            try:
                out_path, size, secs = fut.result()
                print(f"[ok]   {Path(out_path).name}  ({size}, "
                      f"{j.get('quality', 'medium')}, {secs:.1f}s)")
            except SystemExit:
                failures.append((j["out"], "no image data returned"))
                print(f"[FAIL] {Path(j['out']).name}: no image data returned")
            except Exception as e:
                failures.append((j["out"], str(e)))
                print(f"[FAIL] {Path(j['out']).name}: {e}")
    if failures:
        print(f"GENERATION FAILED (batch): {len(failures)} of {len(jobs)} job(s) failed")
        sys.exit(1)
    print(f"batch complete: {len(jobs)} figure(s) regenerated")


def pop_flag(rest, flag, default=None):
    if flag in rest:
        i = rest.index(flag)
        return rest[i + 1], rest[:i] + rest[i + 2:]
    return default, rest


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(2)
    if args[0] == "--batch":
        rest = args[1:]
        if not rest:
            print("usage: python illustrate.py --batch <manifest.json> [--workers 4] [--dry-run]")
            sys.exit(2)
        workers_s, rest = pop_flag(rest, "--workers", "4")
        dry = "--dry-run" in rest
        rest = [a for a in rest if a != "--dry-run"]
        client = None if dry else OpenAI()
        run_batch(client, rest[0], max(1, int(workers_s)), dry)
        return

    client = OpenAI()

    if args[0] == "--generate":
        rest = args[1:]
        if len(rest) < 2:
            print('usage: python illustrate.py --generate "<prompt>" <output_png> [--quality medium] [size]')
            sys.exit(2)
        quality, rest = pop_flag(rest, "--quality", "medium")
        prompt, out_path = rest[0], Path(rest[1])
        size = rest[2] if len(rest) > 2 else "1024x1024"
        try:
            resp = client.images.generate(model="gpt-image-2", prompt=prompt, size=size, quality=quality)
        except Exception as e:
            print(f"GENERATION FAILED (generate): {e}")
            sys.exit(1)
        write_b64(resp.data[0], out_path)
        print(f"generated -> {out_path}  (size={size}, quality={quality})")
        return

    if len(args) < 3:
        print('usage: python illustrate.py <content_image> <output_png> "<prompt>" [--style-ref <png>] [--quality medium] [size]')
        sys.exit(2)
    content_path, out_path, prompt = Path(args[0]), Path(args[1]), args[2]
    rest = args[3:]
    style_ref_s, rest = pop_flag(rest, "--style-ref")
    quality, rest = pop_flag(rest, "--quality", "medium")
    size = rest[0] if rest else aspect_size(content_path)  # auto-match crop shape

    files = [open(content_path, "rb")]
    style_ref = Path(style_ref_s) if style_ref_s else None
    if style_ref and style_ref.exists():
        files.append(open(style_ref, "rb"))
    image_arg = files if len(files) > 1 else files[0]

    try:
        resp = client.images.edit(model="gpt-image-2", image=image_arg, prompt=prompt, size=size, quality=quality)
    except Exception as e:
        print(f"GENERATION FAILED (edit): {e}")
        sys.exit(1)
    write_b64(resp.data[0], out_path)
    for f in files:
        f.close()
    ref = f" + style {style_ref.name}" if style_ref and style_ref.exists() else ""
    print(f"illustrated {content_path.name}{ref} -> {out_path}  (size={size}, quality={quality})")


if __name__ == "__main__":
    main()
