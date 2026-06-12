#!/usr/bin/env python3
"""
palettegen.py - Suggest a style/palette.json from the colors of style/anchor.png.

Role-aware, not "top 5 colors": each palette role has a job, so clusters are
chosen for function and guarded for legibility:
  primary    most saturated mid-tone cluster (titles/headings) - darkened until
             it has >= 3:1 contrast on the page background
  secondary  next saturated cluster with a clearly different hue
  ink        darkest cluster (body text) - darkened until >= 7:1 contrast
  page_bg    always #FFFFFF (figures are generated on white; a non-white page
             shows boxes around them unless the figure background is changed too)
  tint       page_bg mixed with 12% of secondary (faint row shading)

Deterministic for a given anchor. Never overwrites an existing palette.json:
if one exists, writes style/palette.json.suggested instead.

Usage: python scripts/palettegen.py   (run from the project root)
"""
import colorsys
import json
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ANCHOR = ROOT / "style" / "anchor.png"
TARGET = ROOT / "style" / "palette.json"
SUGGESTED = ROOT / "style" / "palette.json.suggested"


def luminance(rgb):
    def chan(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(rgb_a, rgb_b):
    la, lb = luminance(rgb_a), luminance(rgb_b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def darken_until(rgb, bg, ratio):
    rgb = list(rgb)
    for _ in range(40):
        if contrast(rgb, bg) >= ratio:
            break
        rgb = [int(c * 0.92) for c in rgb]
    return tuple(rgb)


def hue_dist(h1, h2):
    d = abs(h1 - h2)
    return min(d, 1.0 - d)


def hexs(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def main():
    if not ANCHOR.is_file():
        print("PALETTEGEN FAILED: style/anchor.png not found - create the anchor first (/style-anchor)")
        sys.exit(1)

    img = Image.open(ANCHOR).convert("RGB").resize((150, 150))
    q = img.quantize(colors=10, method=Image.MEDIANCUT)
    counts = sorted(q.getcolors(150 * 150), reverse=True)  # (count, idx)
    pal = q.getpalette()
    clusters = []
    for count, idx in counts:
        rgb = tuple(pal[idx * 3: idx * 3 + 3])
        h, s, v = colorsys.rgb_to_hsv(*(c / 255.0 for c in rgb))
        clusters.append({"rgb": rgb, "h": h, "s": s, "v": v,
                         "lum": luminance(rgb), "n": count})

    white = (255, 255, 255)

    # ink: darkest cluster, guarded to >= 7:1 on white
    ink = darken_until(min(clusters, key=lambda c: c["lum"])["rgb"], white, 7.0)

    # primary: most saturated mid-tone cluster, guarded to >= 3:1 on white
    mid = [c for c in clusters if 0.12 <= c["lum"] <= 0.65 and c["s"] >= 0.25]
    pool = mid or sorted(clusters, key=lambda c: -c["s"])[:3]
    prim_c = max(pool, key=lambda c: c["s"])
    primary = darken_until(prim_c["rgb"], white, 3.0)

    # secondary: a different-hue cluster; score favors hue distance from primary
    # over raw saturation, so e.g. a muted green beats a vivid same-family brown
    others = [c for c in clusters if c is not prim_c and c["s"] >= 0.08
              and c["lum"] <= 0.75]
    others = [c for c in others if hue_dist(c["h"], prim_c["h"]) >= 20 / 360]
    if others:
        sec_c = max(others, key=lambda c: c["s"] * (0.3 + hue_dist(c["h"], prim_c["h"])))["rgb"]
    else:  # fallback: a muted, darker take on the second most saturated cluster
        rest = [c for c in clusters if c is not prim_c]
        base = max(rest, key=lambda c: c["s"])["rgb"]
        sec_c = tuple(int(c * 0.8) for c in base)
    secondary = darken_until(sec_c, white, 3.0)

    # tint: 12% of secondary mixed into white
    tint = tuple(int(255 - (255 - c) * 0.12) for c in secondary)

    palette = {"primary": hexs(primary), "secondary": hexs(secondary),
               "ink": hexs(ink), "page_bg": "#FFFFFF", "tint": hexs(tint)}

    out = SUGGESTED if TARGET.exists() else TARGET
    out.write_text(json.dumps(palette, indent=2) + "\n", encoding="utf-8")

    for k, v in palette.items():
        print(f"{k:9s} {v}")
    if out is SUGGESTED:
        print(f"wrote {out.relative_to(ROOT)}  (existing palette.json left untouched - "
              "review and copy over it if you like the suggestion)")
    else:
        print(f"wrote {out.relative_to(ROOT)}  (edit it to taste; /rebuild applies it)")


if __name__ == "__main__":
    main()
