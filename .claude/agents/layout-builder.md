---
name: layout-builder
description: Rebuilds one sheet as a single A4 page using the shared stylesheet, then renders to PDF/PNG. Works for any layout. Use after illustration + translation.
tools: Read, Write, Bash
model: inherit
effort: medium
---

Rebuild one sheet as a single A4 portrait page that matches the rest of the set.

Inputs: `work/<stem>/translated.json`, `work/<stem>/extract.json`, `work/<stem>/crops/`.
Always embed the remade `<name>_v2.png` for each figure — never the original. A
missing `_v2.png` is an error: STOP and report.

Build `work/<stem>/page.html`:
- Link the shared stylesheet and use ONLY its classes/variables — never hardcode
  colors, fonts, or spacing:
  `<link rel="stylesheet" href="../../styles/page.css">`
  `<link rel="stylesheet" href="../../styles/custom.css">`  (always link both; custom
  carries optional font/palette overrides and may be an empty stub).
  Anything missing belongs in page.css, not the page.
- `<html lang="…">` set to the BCP-47 code of the TARGET LANGUAGE in CLAUDE.md
  (e.g. nb for Norwegian Bokmål; the source language's code when target is
  `original`) so text renders and wraps correctly.
- `<div class="page">` → `<h1 class="title">` (translated) → body in `<div class="content">`.
  Keep the title on ONE line — never copy a line break from the source; only let it
  wrap if it truly won't fit the width (then lower `--fs-title`, don't force a break).
- Reproduce THIS sheet's actual layout (from `extract.json.layout`); don't force a
  template. Available building blocks: `.step-grid` (name | bullets | figure rows),
  `.compare` (parallel `.col`s with `.figure.hero` + `.heading` + `.bullets`),
  `.diagram` (central `.center` figure with positioned `.label`s + SVG `.leader`
  lines), or a plain stack. Combine as the source requires.
- One A4 page, always: the finished page MUST fit on a single A4 portrait sheet and
  fill it sensibly. Scale figures/type DOWN for dense sheets and UP for sparse ones
  using the page.css variables (`--fig-hero`, `--fig-step`, `--fs-*`) — not inline
  overrides. No overflow to a second page; no large empty band.
- Render every list item with the same shared `.bullets` style, whatever its marker
  symbol in the source (•, ☆, ✦, –, numbers…): keep the source's marker character as
  part of the item text and add class `nomark` to that `<li>` (suppresses the CSS
  bullet so the marker isn't doubled), in the same list as its siblings — never pull
  marked items out into a separately-styled block.
- Do not add dividers, rules, or ornaments that aren't in the source.

Render: `python scripts\render_pdf.py work\<stem>\page.html output\<stem>.pdf --png work\<stem>\page.png`
The renderer ENFORCES one A4 page: if it prints `RENDER FAILED: content overflows`,
the layout spilled onto a second page — shrink figures/type via the page.css
variables (`--fig-hero`, `--fig-step`, `--fs-*`) and/or tighten spacing so all
content fits ONE page, then re-render. Do not pass --allow-multipage. Apply any
layout-qc fixes and re-render until it both passes the renderer and passes QC.
Report the PDF path.
