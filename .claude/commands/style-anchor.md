---
description: Generate warm studio-sketch style-anchor candidates so you can pick the look for the whole document set.
argument-hint: [count]
---

If $ARGUMENTS contains `palette`: run `python scripts/palettegen.py`, show its
output, and STOP (it suggests a style/palette.json derived from the anchor's
colors; never overwrites an existing palette.json — writes .suggested instead).

Create the style anchor that locks every figure to one look.

1. Ensure the `style\` folder exists.
2. Generate $ARGUMENTS candidate images (default 3 if empty) using the ART
   DIRECTION block from CLAUDE.md verbatim, each on a neutral subject typical of
   this project's sheets so
   only the STYLE is being judged. Suggested subjects: "a potter's hands centering
   the style is easy to judge (pick simple, representative subjects).
   For each, run:
   `python scripts\illustrate.py --generate "<ART DIRECTION>. Subject: <subject>. No text or labels." style\anchor_<n>.png`
3. List the candidate paths and tell me to open them and copy my favorite to
   `style\anchor.png` (that file is what the illustrator uses on every figure).

Do not run /rebuild. This only produces candidates for me to choose from.
