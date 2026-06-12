# Changelog

All notable changes to the Sheet2PDF pipeline (image sheets → translated A4 PDFs). Newest first.
Versions track the scaffold iterations; all dated 2026-06-06 (built in one session).

## v29 — 2026-06-12
### Added
- Configurable output language: two plain settings at the top of CLAUDE.md —
  `TARGET LANGUAGE:` (any language, default Norwegian Bokmål, or `original` to keep
  the source text exactly as written) and `UNITS:` (`metric` converts imperial →
  metric with the target language's number conventions; `original` keeps units as
  written). The translator, qa-reviewer, and layout-builder (html lang attribute)
  all follow these settings; `original` makes the translator a faithful
  pass-through. The loanword rule is now language-general (keep a word in its
  source form when that's what the target language's speakers actually use).

## v28 — 2026-06-12
### Changed
- Renamed the project Sheet2PDF and removed pottery-specific text from the README
  (title, tagline, paths, notes). Pottery remains only as the stated origin and the
  default example look. Scaffold zip folder renamed sheet2pdf_scaffold.

## v27 — 2026-06-12
### Added (speed: ~3-4x faster on figure-heavy sheets, no quality change)
- illustrate.py `--batch <manifest> [--workers 4] [--dry-run]`: all of a sheet's
  figures now generate CONCURRENTLY in one call (same prompts, same quality, same
  loud failure — every job attempted, any failure reported and exits non-zero).
  The illustrator writes one manifest and makes one batch call instead of N
  sequential calls.
- Generation size now scales to each crop's own resolution (2x its longest side,
  clamped 512..1024): small icons generate smaller/faster/cheaper; detailed figures
  keep full resolution.
- The translator now runs IN PARALLEL with the illustrator (both depend only on
  extract.json), saving minutes on text-heavy sheets.
### Added (customization)
- scripts/palettegen.py + `/style-anchor palette`: suggests a style/palette.json
  derived from the anchor's own colors — role-aware (readable ink, saturated
  mid-tone primary, different-hue secondary, faint tint) with WCAG contrast guards
  (ink >= 7:1, primary/secondary >= 3:1 on the page). Deterministic; never
  overwrites an existing palette.json (writes palette.json.suggested instead);
  page_bg stays #FFFFFF to match the figure backgrounds.
### Changed
- README: concrete "what you will literally see change" descriptions for each
  palette role (with the page_bg/figure-box warning), the parallel pipeline in the
  diagram, and the new command.

## v26 — 2026-06-12
### Added
- Per-project customization, all "if present use, if absent ignore":
  - `style/fonts/title.ttf|otf` and `style/fonts/body.ttf|otf` — custom fonts (one
    font file with any name is used for both roles).
  - `style/palette.json` — any subset of {primary, secondary, ink, page_bg, tint}
    as #RRGGBB; omitted keys keep defaults. `style/palette.json.example` included.
  - `scripts/stylegen.py` — runs at the start of every /rebuild, regenerates
    `styles/custom.css` (empty stub when nothing is present; loud failure on a bad
    palette file). Pages link page.css then custom.css, so overrides win by cascade.
### Changed
- The engine is now domain-neutral: removed remaining pottery/ceramics assumptions
  from CLAUDE.md and the agents (translator: "the sheet's subject area"; qa: anchor
  medium/palette without naming a style; style-anchor: project-typical subjects).
  The ART DIRECTION block is documented as the per-project default look, edited
  together with the anchor.
- Stylesheet palette variables renamed to semantic roles: --primary, --secondary,
  --ink, --page-bg, --tint (was terracotta/sage/charcoal/row-tint).
- README: new Customization section (anchor, fonts, palette, re-theming steps).
- Verified: with no overrides present, output is pixel-identical to the defaults.

## v25 — 2026-06-12
### Fixed (full-pipeline quality audit)
- render_pdf.py: the PDF/PNG could render before Google Fonts had APPLIED or images
  had decoded (networkidle is not enough) — now explicitly waits for
  `document.fonts.ready` and full image decode. Eliminates intermittent
  fallback-font / missing-figure renders.
- render_pdf.py: `prefer_css_page_size=True` so the stylesheet's `@page` rule is
  authoritative (A4 remains the fallback).
- crop.py: invalid or degenerate crop boxes now FAIL loudly instead of silently
  producing junk crops.
- page.css: `print-color-adjust: exact` so background tints can never drop from the
  PDF; `text-wrap: balance` so a title that genuinely must wrap balances its lines.
- Mixed-marker lists (•, ☆, ✦, …): every item now renders in the SAME shared list
  style — the source's marker character is kept in the text with a `nomark` class
  (no doubled bullet, hanging indent) instead of being pulled into a separately
  styled block.
- layout-builder: pages declare `<html lang="nb">` for correct Norwegian rendering.
- illustrator: figures that CONTAIN TEXT now always generate at `--quality high`
  (text garbles at lower quality), same as label-critical figures.

## v24 — 2026-06-06
### Changed
- README: removed the Claude Code v2.1.154 / Opus 4.8 pin from Requirements, Usage,
  and the badges. That version requirement was specific to our setup, not a real
  dependency — the pipeline runs on any current Claude Code with any model.

## v23 — 2026-06-06
### Changed
- Redesigned the README in a modern style (badges, table of contents, ASCII pipeline
  diagram, tables, GitHub admonitions, and a collapsible "Under the Hood"), modeled
  on the Transcribe-Subs README. Added Features, Cost, and Troubleshooting sections.

## v22 — 2026-06-06
### Changed
- Rewrote README with a detailed "How it works" section explaining each agent
  (extractor, crop, illustrator, translator, layout-builder, layout-qc, qa-reviewer)
  and the end-to-end process. Corrected stale claims (translated title, always-
  regenerate with no original fallback, key required, white backgrounds, metric
  conversion, glossary removed) and added the PowerShell/settings.json setup step.

## v21 — 2026-06-06
### Changed
- Dropped the "header stays English" rule. The title is now translated to Bokmål
  like the rest of the text.
- New translation principle (title and body alike): keep a word in English when that
  is the form Norwegians actually use (an established anglicism), even if a Norwegian
  equivalent exists — judged by real everyday usage, not by whether a translation is
  possible. Removed the `keep_english` flag from the extractor.

## v20 — 2026-06-06
### Added
- Translator now converts body-text measurements to metric (inches/feet→cm/mm,
  oz/lb→g/kg, cups/tbsp/tsp/fl oz→ml/l, °F→°C), with Norwegian comma decimals and
  sensible rounding; ceramics-standard units (e.g. cone numbers) are left alone.
  Figures keep their original text and units. qa-reviewer verifies the conversion.

## v19 — 2026-06-06
### Fixed
- Walked back the v15 element-preservation overcorrection that was forcing/emphasizing
  decorations and splitting scenes. Rules are now balanced: reproduce the original
  faithfully, keeping the same elements at the same visual weight — add nothing, drop
  nothing, enlarge/emphasize nothing.
- Extractor now crops a coherent scene as ONE figure (keeps an action and the object
  it acts on together) instead of splitting them into separate panels or inventing
  pieces. Removed the symmetric-crop rule that drove the over-segmentation.
- qa-reviewer now also flags over-emphasized elements and split/invented scenes.

## v18 — 2026-06-06
### Fixed
- qa-reviewer was false-failing figures for "invented English text." There was no
  no-text check left, but nothing told the agent that text reproduced from the
  original is expected, so it matched the text to its "flag anything added" rule.
  Added an explicit exception: figure text matching the original is correct; only
  genuinely invented, garbled, or misspelled figure text is flagged.

## v17 — 2026-06-06
### Changed
- Removed sheet-specific examples ("stars, sparkles, dots, motifs") from the
  extractor, illustrator, and qa-reviewer. The element-preservation rules are now
  fully general ("every small, background, or decorative element"), so they apply to
  any sheet, not the test image.

## v16 — 2026-06-06
### Changed
- Figures keep their text in the ORIGINAL language (reverted the Bokmål-in-figure
  experiment). Pipeline order restored to illustrator-before-translator, since the
  illustrator no longer needs translations.
### Fixed
- Title no longer wraps to two lines when it fits on one: the extractor normalizes
  the title to a single line (collapsing any source line break) and the
  layout-builder keeps it on one line, only wrapping/shrinking if it truly won't fit.

## v15 — 2026-06-06
### Changed
- Figures and the PDF page are now WHITE (was warm cream), so restyled figures blend
  into the page with no visible square/box around them.
- Removed the no-text restriction: figures now reproduce any text faithfully and
  spelled exactly (gpt-image-2 renders text reliably).
### Fixed
- Dropped/inconsistent elements (e.g. stars on one panel but not the other) are now
  caught: the extractor lists decorative/background elements in `preserve` and crops
  paired figures symmetrically; the illustrator must keep every element; qa-reviewer
  flags any added or dropped element and checks parallel figures stay consistent.

## v14 — 2026-06-06
### Added
- Style-match gate in qa-reviewer: the anchor is now an input, and each `_v2.png` is
  checked against the anchor's medium and palette. Figures that come back as flat
  line-art, white/transparent background, or wrong tone are flagged and remade.
  Closes the gap where a figure could be content-accurate but in the wrong style.

## v13 — 2026-06-06
### Removed
- The Norwegian ceramics glossary. The translator is Claude, which already knows the
  vocabulary, so the word list was redundant. Replaced with a short consistency note
  (pick one translation per term and use it set-wide).

## v12 — 2026-06-06
### Changed
- Genericized all agent instructions: removed example-specific guidance so they
  work for any sheet (any layout, format, or text size), inferring structure from
  the source rather than matching a fixed template.
- Trimmed every agent's checklist to the essentials, so long lists don't get
  skipped (layout-qc → 5 checks, qa-reviewer → 4, illustrator/extractor tightened).
- Made single-A4 a hard rule: every output is exactly one A4 portrait page; content
  is scaled to fit and fill it (down for dense sheets, up for sparse), never
  overflowing to a second page.

## v11 — 2026-06-06
### Changed
- Rebalanced the shared stylesheet: larger figures (hero figures up to ~92mm) and
  type, and a `.content` wrapper that vertically centers the body so short sheets
  no longer leave a big empty band at the bottom.
- Added a proper two-column `.compare` layout for comparison sheets, with NO
  divider rule between columns.
- layout-builder: forbidden from drawing decorative dividers/rules not in the
  source; must size figures prominently via page.css variables.
- layout-qc tightened: now fails on poor vertical balance / wasted space, timid
  figures, too-small text, and extraneous decoration (e.g. the dotted divider).

## v10 — 2026-06-06
### Changed
- Removed the `keep-art` reuse option entirely. There is now NO reuse path: every
  figure is always regenerated from its original crop on every run.
- Premise restated across the agents: the anchor defines the STYLE; the original
  crop is the guide for WHAT the figure must convey. The crop is input only.

## v9 — 2026-06-06
### Changed
- Image step is now ALWAYS regenerate: every figure is remade from its original
  crop via gpt-image-2 on every run. Removed all "use the original instead" paths
  — the original crop is only the model's input/reference, never an output figure.
- Reuse is now opt-in (`/rebuild <name> keep-art`) instead of the default, so stale
  figures are never served silently. (Replaces the old `remake-art` flag.)
- Generation failures are loud: a missing OPENAI_API_KEY (or org/rate-limit error)
  STOPS the run and reports it, rather than falling back to un-styled originals.
- qa-reviewer / layout-builder: an inaccurate figure is remade (retried); if it
  still fails it is FLAGGED for review — the original is never substituted.
### Added
- `.claude/settings.json.example` + PowerShell default shell config; real
  `.claude/settings.json` is gitignored (key supplied via user settings).

## v8 — 2026-06-06
### Added
- `styles/page.css`: a single shared stylesheet every page links. Palette, fonts,
  spacing, and layout classes live here so the whole set looks identical; the
  layout-builder may no longer hardcode colors, fonts, or margins.
### Changed
- Figures auto-match the source: `illustrate.py` reads each crop and picks a
  gpt-image-2 size with the same aspect ratio (no distortion or padding).
- Reimagined figures are reused across runs; an existing `_v2.png` is kept unless
  `/rebuild <name> remake-art` is used or QA flags it (avoids re-charging the API).
- QA screenshot tightened to true A4 so layout-qc judges the real page edges.

## v7 — 2026-06-06
### Changed
- Illustrator reframed as an exact restyle: Image 1 (the crop) is the ground truth
  for *what* is drawn; Image 2 (anchor) + the brief control only *how* it looks.
- Accuracy is now a retry loop: if QA finds a remade figure inaccurate, the
  illustrator remakes it (tighter constraints, high quality, up to 2 retries);
  the original crop is used only as a last resort.

## v6 — 2026-06-06
### Added
- `README.md`.
### Changed
- qa-reviewer rewritten into a correctness gate: it studies the original and
  verifies, line by line and figure by figure, that the information and the
  illustrations are true to the original — every figure compared old vs new,
  not only the labeled diagrams.

## v5 — 2026-06-06
### Added
- `layout-qc` agent: a visual/typography critic that inspects the rendered page and
  loops with the layout-builder (max 3 passes) before content QA.
### Changed
- gpt-image-2 prompting upgraded per OpenAI's guide: inputs referenced by index,
  change+preserve split with the preserve list restated, quality tiers (high for
  label-critical, medium otherwise). `input_fidelity` omitted (locked on gpt-image-2).
- QA render bumped to 2x for sharper inspection.

## v4 — 2026-06-06
### Added
- Warm studio-sketch art direction, palette, and Fraunces + Nunito fonts.
- Style anchor (`style/anchor.png`) + `/style-anchor` command; figures generated
  against the anchor for one consistent look.
### Changed
- Every figure is now reimagined (not just crude ones). Extractor tags each crop
  `label_critical` and a `preserve` list; label-critical diagrams are held to the
  preserve list exactly.

## v3 — 2026-06-06
### Added
- `/rebuild` targeting: no args = all pending, `<names>` = forced subset, `all` =
  full refresh.
- `ignore.txt` to hold images back; `/status` command for a done/pending table.
### Changed
- Idempotent runs: an existing `output/<stem>.pdf` marks an image done and is skipped.

## v2 — 2026-06-06
### Added
- `illustrator` agent + `scripts/illustrate.py` using gpt-image-2 (edit mode) to
  reimagine figures; QA drift check; `OPENAI_API_KEY` requirement.

## v1 — 2026-06-06
### Added
- Initial multi-agent scaffold: extractor, translator, layout-builder, qa-reviewer,
  orchestrated by `/rebuild`.
- `scripts/crop.py` (Pillow) and `scripts/render_pdf.py` (Playwright HTML→PDF).
- `CLAUDE.md` brief: Bokmål translation, English header kept, layout preserved,
  Norwegian ceramics glossary; one A4 PDF per source image.
