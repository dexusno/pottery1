# Changelog

All notable changes to the pottery → Norwegian PDF pipeline. Newest first.
Versions track the scaffold iterations; all dated 2026-06-06 (built in one session).

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
