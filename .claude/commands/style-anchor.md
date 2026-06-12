---
description: Generate style-anchor candidates (the look for the whole set), optionally guided by a text description. Also `/style-anchor palette` to derive a palette from the anchor.
argument-hint: [count] [subject/style guidance…]
---

If $ARGUMENTS contains `palette`: run `python scripts/palettegen.py`, show its
output, and STOP (it suggests a style/palette.json derived from the anchor's
colors; never overwrites an existing palette.json — writes .suggested instead).

Create the style anchor that locks every figure to one look.

Parse $ARGUMENTS: a leading number = how many candidates (default 3); ALL remaining
text = the user's guidance for the candidates (subject matter and/or style notes).

1. Ensure the `style\` folder exists.
2. Pick the candidate subjects:
   - If guidance was given, follow it — it may name the subject ("a watering can
     and seed packets"), steer the style ("more ink, less wash"), or both.
   - If no guidance: choose simple, neutral subjects typical of this project's
     source sheets (look at them), so only the STYLE is being judged.
3. For each candidate, run:
   `python scripts\illustrate.py --generate "<ART DIRECTION from CLAUDE.md, verbatim>. <guidance, if any>. Subject: <subject>. No text or labels." style\anchor_<n>.png`
4. List the candidate paths and tell me to open them and copy my favorite to
   `style\anchor.png` (the illustrator passes that file on every figure call).

Do not run /rebuild. This only produces candidates for me to choose from.
