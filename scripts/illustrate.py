#!/usr/bin/env python3
"""
illustrate.py - Generate or restyle a figure with gpt-image-2.

GENERATE (text-to-image, for style-anchor candidates):
    python illustrate.py --generate "<prompt>" <output_png> [--quality medium] [size]

EDIT (restyle a figure, optionally against a style reference):
    python illustrate.py <content_image> <output_png> "<prompt>" [--style-ref <png>] [--quality medium] [size]
  Content image is Image 1 (what to depict); style ref, if given, is Image 2 (how
  it looks). Reference inputs by index in the prompt.

  SIZE: if omitted in EDIT mode, it is derived from the content image's aspect
  ratio (snapped to a valid gpt-image-2 size) so the figure is not distorted.

Notes:
- input_fidelity is LOCKED on gpt-image-2 (always high); do NOT pass it.
- quality: low (fast), medium (default), high (label-heavy / diagrams).
- No transparent background; PNG on opaque background.
- size = WxH, both divisible by 16, aspect within 1:3..3:1.

Requires OPENAI_API_KEY; gpt-image-2 needs OpenAI Org Verification.
"""
import base64
import sys
from pathlib import Path
from PIL import Image
from openai import OpenAI

LONG = 1024  # longest side of generated figures


def aspect_size(img_path):
    """Pick a valid gpt-image-2 size matching the image's aspect ratio."""
    w, h = Image.open(img_path).size
    ratio = w / h
    ratio = max(1 / 3, min(3.0, ratio))  # clamp to allowed aspect band

    def snap(v):
        return max(256, int(round(v / 16) * 16))

    if w >= h:
        W, H = LONG, snap(LONG / ratio)
    else:
        W, H = snap(LONG * ratio), LONG
    return f"{W}x{H}"


def write_b64(item, out_path):
    b64 = getattr(item, "b64_json", None)
    if not b64:
        print("error: no image data returned")
        sys.exit(1)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(base64.b64decode(b64))


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
