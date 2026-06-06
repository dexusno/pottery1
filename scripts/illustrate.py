#!/usr/bin/env python3
"""
illustrate.py - Generate or restyle a figure with gpt-image-2.

GENERATE (text-to-image, for style-anchor candidates):
    python illustrate.py --generate "<prompt>" <output_png> [--quality medium] [size]

EDIT (restyle a figure, optionally against a style reference):
    python illustrate.py <content_image> <output_png> "<prompt>" [--style-ref <png>] [--quality medium] [size]
  Content image is Image 1 (what to depict); the style ref, if given, is Image 2
  (how it should look). Write prompts that reference inputs by index, e.g.
  "redraw the subject of Image 1 in the style of Image 2".

Notes (from the gpt-image-2 docs):
- input_fidelity is LOCKED for gpt-image-2 (always high); do NOT pass it.
- quality: low (fast/cheap), medium (default), high (dense text / label-heavy /
  diagrams). Use high for label-critical figures.
- No transparent background; output is PNG on an opaque background.
- size defaults to 1024x1024 (W and H divisible by 16).

Requires OPENAI_API_KEY; gpt-image-2 is gated behind OpenAI Org Verification.
"""
import base64
import sys
from pathlib import Path
from openai import OpenAI


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
        val = rest[i + 1]
        return val, rest[:i] + rest[i + 2:]
    return default, rest


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(2)
    client = OpenAI()  # reads OPENAI_API_KEY

    if args[0] == "--generate":
        rest = args[1:]
        if len(rest) < 2:
            print('usage: python illustrate.py --generate "<prompt>" <output_png> [--quality medium] [size]')
            sys.exit(2)
        quality, rest = pop_flag(rest, "--quality", "medium")
        prompt = rest[0]
        out_path = Path(rest[1])
        size = rest[2] if len(rest) > 2 else "1024x1024"
        resp = client.images.generate(model="gpt-image-2", prompt=prompt, size=size, quality=quality)
        write_b64(resp.data[0], out_path)
        print(f"generated -> {out_path}  (size={size}, quality={quality})")
        return

    # EDIT mode
    if len(args) < 3:
        print('usage: python illustrate.py <content_image> <output_png> "<prompt>" [--style-ref <png>] [--quality medium] [size]')
        sys.exit(2)
    content_path = Path(args[0])
    out_path = Path(args[1])
    prompt = args[2]
    rest = args[3:]
    style_ref_s, rest = pop_flag(rest, "--style-ref")
    quality, rest = pop_flag(rest, "--quality", "medium")
    size = rest[0] if rest else "1024x1024"

    files = [open(content_path, "rb")]
    style_ref = Path(style_ref_s) if style_ref_s else None
    if style_ref and style_ref.exists():
        files.append(open(style_ref, "rb"))

    image_arg = files if len(files) > 1 else files[0]
    resp = client.images.edit(model="gpt-image-2", image=image_arg, prompt=prompt, size=size, quality=quality)
    write_b64(resp.data[0], out_path)
    for f in files:
        f.close()
    ref_note = f" + style {style_ref.name}" if style_ref and style_ref.exists() else ""
    print(f"illustrated {content_path.name}{ref_note} -> {out_path}  (size={size}, quality={quality})")


if __name__ == "__main__":
    main()
