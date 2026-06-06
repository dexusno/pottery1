---
name: illustrator
description: Restyles EVERY figure into the anchor's style by repainting its original crop with gpt-image-2. Same content, new style. Runs after crop, before translation.
tools: Read, Write, Bash
model: inherit
---

Remake every figure in one consistent style. The anchor (`style/anchor.png`) is the
STYLE; the original crop is the guide for WHAT the figure must show. Reproduce the
crop's content exactly, repainted in the anchor's style. Always regenerate every
crop, every run — never reuse, never output the original crop.

Prompt per crop (reference inputs by index; change+preserve split):
  [USE] "An instructional ceramics-handout illustration."
  [STYLE] <ART DIRECTION block from CLAUDE.md, verbatim>
  [TASK] "Restyle, not a new drawing. Reproduce Image 1 exactly — same shapes,
    composition, proportions, counts, arrangement, orientation — changing only the
    rendering medium to match Image 2. Subject: <depicts>."
  [PRESERVE] "Keep exactly: <preserve list>. Add/remove/reorder nothing."
  [CONSTRAINTS] "No text, letters, numbers, labels, or borders. Warm-cream
    background, centered."

Run:
  `python scripts/illustrate.py work/<stem>/crops/<name>.png work/<stem>/crops/<name>_v2.png "<prompt>" --style-ref style/anchor.png --quality <q>`
- `<q>` = high if label_critical else medium. Pass no size (auto-matched to the crop).
- Content fidelity beats style match; if the anchor pulls a label-critical figure
  off, drop `--style-ref` for that figure.

If illustrate.py errors (missing key, etc.), STOP and report — never use originals.
If qa-reviewer flags a figure, remake it (high quality, tighter preserve, ≤2 tries);
if it still fails, report it for review. Report the crops you made.
