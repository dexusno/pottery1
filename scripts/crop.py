#!/usr/bin/env python3
"""
crop.py - Extract illustration regions from a source image.

Usage:
    python crop.py <source_image> <out_dir> <spec_json>

<spec_json> is a JSON file (or inline JSON string) shaped like:
    {
      "crops": [
        {"name": "step_setup", "box": [0.72, 0.10, 0.98, 0.20]},
        {"name": "step_center", "box": [0.72, 0.21, 0.98, 0.33]}
      ]
    }

Each "box" is [left, top, right, bottom] as fractions (0..1) of the
source image width/height. A small margin is added automatically so
hand-estimated boxes don't clip the artwork. Outputs <out_dir>/<name>.png.
"""
import json
import os
import sys
from PIL import Image

MARGIN = 0.01  # 1% padding around each box, clamped to image edges


def load_spec(arg):
    if os.path.isfile(arg):
        with open(arg, "r", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(arg)


def main():
    if len(sys.argv) != 4:
        print("usage: python crop.py <source_image> <out_dir> <spec_json>")
        sys.exit(2)

    src_path, out_dir, spec_arg = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out_dir, exist_ok=True)

    img = Image.open(src_path).convert("RGBA")
    w, h = img.size
    spec = load_spec(spec_arg)

    results = []
    for crop in spec.get("crops", []):
        name = crop["name"]
        left, top, right, bottom = crop["box"]
        if not (0.0 <= left < right <= 1.0 and 0.0 <= top < bottom <= 1.0):
            print(f"CROP FAILED: '{name}' has an invalid box {crop['box']} "
                  "(need 0 <= left < right <= 1 and 0 <= top < bottom <= 1)")
            sys.exit(1)
        if (right - left) < 0.02 or (bottom - top) < 0.02:
            print(f"CROP FAILED: '{name}' box {crop['box']} is degenerately small")
            sys.exit(1)
        left = max(0.0, left - MARGIN)
        top = max(0.0, top - MARGIN)
        right = min(1.0, right + MARGIN)
        bottom = min(1.0, bottom + MARGIN)
        px = (int(left * w), int(top * h), int(right * w), int(bottom * h))
        out_path = os.path.join(out_dir, name + ".png")
        img.crop(px).save(out_path)
        results.append({"name": name, "path": out_path, "px": px})
        print(f"cropped {name} -> {out_path}  px={px}")

    with open(os.path.join(out_dir, "_crops.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
