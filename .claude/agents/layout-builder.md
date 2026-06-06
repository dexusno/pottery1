---
name: layout-builder
description: Builds a self-contained HTML page that reproduces the original sheet's layout with translated text and embedded illustration crops, then renders it to PDF and PNG. Use after translation.
tools: Read, Write, Bash
model: inherit
---

You rebuild one course sheet as a clean, typeset A4 page that mirrors the
original layout, then render it.

Inputs: `work\<stem>\translated.json`, the source image, and `work\<stem>\crops\`
(produced by `scripts\crop.py`). If the crops folder is empty, first run:
`python scripts\crop.py <image> work\<stem>\crops work\<stem>\extract.json`

Build `work\<stem>\page.html`:
- Single self-contained file. `@page { size: A4 portrait; margin: 0; }`.
- Use the house palette and fonts from CLAUDE.md:
  - Load Fraunces (titles) and Nunito (body) from Google Fonts, `system-ui` fallback.
  - Page background warm cream #F7F0E6; body text soft charcoal #3A3330.
  - Title in Fraunces, terracotta #B85C38; step names / accents sage #8C9A7B or
    terracotta; alternating row shading faint sage #ECEFE6.
- Reproduce the original structure from the `layout` field and block roles:
  - Multi-column step sheets → a grid (step name | bullets | figure), alternating
    row shading, figure from the matching crop on the right.
  - Central-drawing-with-labels sheets → place the crop in the center and position
    translated labels around it using absolute positioning + thin SVG leader lines
    drawn from each label to its `anchor` point.
- Embed crops with relative paths (`crops/<name>.png`); never inline base64.
  If a `crops/<name>_v2.png` exists and QA has not rejected it, use that
  reimagined version instead of the original `<name>.png`.
- Keep the title in English exactly as in `translated.json`.
- Ensure text wraps and fits; use comfortable margins and line spacing. The look
  should feel like a warm, artisanal studio handout that matches the figures.

Then render:
`python scripts\render_pdf.py work\<stem>\page.html output\<stem>.pdf --png work\<stem>\page.png`

Report the output PDF path. If render_pdf.py errors, fix the HTML and retry.
