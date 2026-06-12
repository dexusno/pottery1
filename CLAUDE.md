# Image sheets → translated PDF rebuild

## Output language & units (EDIT THESE TWO LINES per project)
TARGET LANGUAGE: Norwegian Bokmål
UNITS: metric

- TARGET LANGUAGE may be any language, or `original` to keep the source language
  exactly as written (no translation).
- UNITS: `metric` converts imperial measurements in body text to metric, using the
  target language's number conventions; `original` keeps units exactly as written.
The translator and qa-reviewer read these two settings.

## Models (EDIT THESE TWO LINES per project)
PREMIUM MODEL: opus
WORKFLOW MODEL: sonnet

- PREMIUM runs the judgment-heavy agents: **extractor, layout-qc, qa-reviewer**
  (careful vision and critique — where output quality is enforced).
- WORKFLOW runs the mechanical agents: **illustrator, translator, layout-builder**
  (templated prompts, translation, HTML assembly).
- Values: a model alias (`opus`, `sonnet`, `haiku`, `fable`), a full model ID
  (e.g. `claude-opus-4-8`), or `inherit` to use the session's model.
- The orchestrator passes the model EXPLICITLY on every subagent delegation per
  this mapping. Set both to `inherit` to disable tiering entirely.
- An ALIAS resolves to the LATEST model of that tier (and silently upgrades when a
  new one ships); use a full model ID to pin a version. Verify what is actually
  running via `/status` or the model+effort shown next to the spinner.

### Thinking effort
Effort (low | medium | high | xhigh | max) controls thinking depth on modern
models. It is tiered in each agent's frontmatter (`effort:` — shipped: `high` for
the premium agents, `medium` for the workflow agents); edit there to change it.
The session's own effort is set with `/effort` or `claude --effort <level>`.
A `CLAUDE_CODE_EFFORT_LEVEL` env var overrides everything, and an unsupported
level falls back to the highest the model supports.

## Goal
Rebuild each source image (handwritten notes, infographics, illustrated guides —
any subject) as a beautiful, typeset **A4 PDF** with body text translated to
the **TARGET LANGUAGE** set above, every figure reimagined in ONE consistent illustration style
defined by the project's style anchor, while preserving each sheet's layout,
structure, and the instructional meaning of every figure.

## Sheets vary
Source sheets differ widely — handwritten or typeset, dense or sparse, any layout,
any text size, portrait or landscape. These rules are general: infer each sheet's
structure from the source itself, never assume a fixed format.

## Hard rules
1. **Translate to the TARGET LANGUAGE, keeping established loanwords.** Translate
   all text — including the title/header — idiomatically into the target language.
   Keep a word in its source form when that is what speakers of the target language
   actually use (an established loanword), even if a native equivalent exists —
   judge by real-world usage. If TARGET LANGUAGE is `original`, all text is kept
   exactly as written (no translation).
2. **Single A4 page.** Every deliverable is exactly one A4 portrait PDF per source
   image, named after the source file. Content must fit on that one page and fill it
   sensibly — scale figures/type down for dense sheets, up for sparse ones (via the
   page.css variables), never overflowing to a second page or leaving it half-empty.
3. **Typeset, not handwritten.** Page text uses Fraunces (titles) + Nunito (body).
   Never imitate handwriting.
4. **Every figure is remade in one style** (see Figure policy) — never output an
   original crop.
5. **Never break an instruction.** A figure's meaning comes before its looks. For
   label-critical figures the preserve-list is law; if a redraw can't honor it after
   retries, flag it for review — do not substitute the original.

## House style (ART DIRECTION — injected verbatim into every image prompt)
This block is the project's default look and is meant to be EDITED per project,
together with `style\anchor.png` (which dominates). Change both to change the look.
"Warm hand-drawn studio-sketch illustration. Confident, slightly loose ink
linework with soft gouache/watercolor washes. Earthy ceramics-studio palette:
terracotta/rust as the primary accent, muted sage green and soft charcoal as
secondaries. Cozy, artisanal, friendly. Single subject, centered, generous margins,
on a plain solid white background. Reproduce any text that appears in the source
figure clearly, legibly, and spelled exactly as given; do not add text that isn't
there. No border, no frame."

### Palette (used for BOTH the illustrations and the page)
Semantic roles, defined once in `styles\page.css`:
- `--primary`   (titles, headings, accents)        default #B85C38
- `--secondary` (sub-headings, step names)         default #8C9A7B
- `--ink`       (body text, linework)              default #3A3330
- `--page-bg`   (page + figure background)         default #FFFFFF
- `--tint`      (alternating row shading)          default #ECEFE6

### Fonts
Defaults via Google Fonts: titles "Fraunces", body "Nunito" (system-ui fallback).

### Optional per-project overrides (if present use, if absent ignore)
`scripts\stylegen.py` runs at the start of every /rebuild and regenerates
`styles\custom.css` from whatever exists under `style\`:
- `style\fonts\title.ttf|otf` and/or `style\fonts\body.ttf|otf` — custom fonts
  (a single font file with any name is used for BOTH roles).
- `style\palette.json` — any subset of {"primary","secondary","ink","page_bg",
  "tint"} as #RRGGBB (see style\palette.json.example). Omitted keys keep defaults.
`/style-anchor palette` suggests a palette.json derived from the anchor's own
colors (role-aware, contrast-guarded; never overwrites an existing palette.json).
Every page links `page.css` then `custom.css`, so overrides win by cascade; with
nothing present, custom.css is an empty stub and the defaults apply unchanged.
The layout-builder never hardcodes colors, fonts, or spacing, so every page in a
set is identical in style.

## Figure policy (every figure is remade)
Every figure is restyled into the house look by repainting the original crop with
gpt-image-2 (Image 1 = the crop = ground truth for WHAT is drawn; Image 2 =
`style\anchor.png` = HOW it looks). It is a restyle, never a new invention. The
extractor flags how strict to be:
- **Decorative / illustrative** (`label_critical: false`): restyle freely; keep the
  same subject and any meaningful counts. quality `medium`.
- **Label-critical** (`label_critical: true`): the `preserve` list is law — same
  elements, counts, order, arrangement, orientation. quality `high`. Content
  fidelity beats stylistic match; if the anchor pulls the composition off, weight
  the prompt toward Image 1 or drop the style ref for that figure.

The original crop is ONLY the input/reference to the image model (img2img). It is
NEVER used as an output figure. Every figure on every page is a model-made
`_v2.png` restyle of its original crop.

ALWAYS regenerate: each `/rebuild` makes a fresh `_v2.png` for every crop. There is
NO reuse path and no "use the original instead" path. The anchor defines the style;
the original crop is the guide for what the figure must convey. If a generation
fails (missing key, org not verified, rate limit), the run STOPS and reports the
error — it must be fixed, not hidden behind the original.

Figure size matches the source automatically: illustrate.py reads each crop and
picks a gpt-image-2 size with the same aspect ratio, so figures are never distorted.

If qa-reviewer judges a remade figure inaccurate vs the original, the illustrator
REMAKES it (retry, high quality, tighter preserve, up to 2 times). If it still
fails, the page is left FLAGGED for review — the original is never substituted.

## Style anchor (locks the whole set to one look)
A single approved reference image at `style\anchor.png` defines the look. The
illustrator passes it to gpt-image-2 as a second reference on every call, so all
figures share one hand. Create/choose it once with `/style-anchor` (generates
candidates → you copy your favorite to `style\anchor.png`). If `style\anchor.png`
is absent, the illustrator still applies the ART DIRECTION text (less locked).
`OPENAI_API_KEY` is REQUIRED — without it the run stops with an error rather than
producing un-styled original crops.

Image generation uses **gpt-image-2** via `scripts\illustrate.py`. Requires
`OPENAI_API_KEY`; gpt-image-2 is gated behind OpenAI Organization Verification.
gpt-image-2 has no transparent background, so figures render on solid white.

## Folder layout (project root = D:\pottery)
- Source images at the **project root**: `*.jpg`, `*.jpeg`, `*.png`.
- `styles\page.css` — the SHARED stylesheet every page links (palette, fonts,
  spacing, layout classes). The page look is defined here, not per page.
- `style\anchor.png` — the approved style reference (plus `anchor_*.png` candidates).
- `work\<stem>\` — `extract.json`, `translated.json`, `crops\` (with `_v2.png`
  reimagined versions), `page.html`, `page.png`, `qa.md`.
- `output\<stem>.pdf` — the finished deliverable.
- `ignore.txt` (optional) — filenames to skip on a no-arg `/rebuild`; `#` = comment.
- `scripts\crop.py`, `scripts\render_pdf.py`, `scripts\illustrate.py`.

## Pipeline (one image at a time)
1. **extractor** reads the image → `work\<stem>\extract.json` (text + crops, each
   crop with `depicts`, `label_critical`, and a `preserve` list).
2. **crop**: `python scripts\crop.py <image> work\<stem>\crops work\<stem>\extract.json`.
3. **illustrator ∥ translator** — run in PARALLEL (each needs only extract.json):
   - illustrator redraws every crop in the house style against `style\anchor.png`
     → `work\<stem>\crops\<name>_v2.png`, in ONE concurrent batch
     (`illustrate.py --batch`, default 4 workers). gpt-image-2 `quality: high` for
     label-critical or text-bearing figures, `medium` otherwise; size auto-matched
     to each crop's aspect and resolution.
   - translator → `work\<stem>\translated.json`.
4. **layout-builder** → `page.html` (house palette + fonts, embedding the `_v2.png`
   figures), then
   `python scripts\render_pdf.py work\<stem>\page.html output\<stem>.pdf --png work\<stem>\page.png`.
5. **layout-qc** (visual/typography critic) inspects `page.png` → `qa_layout.md`.
   On FAIL, the layout-builder applies the punch-list and re-renders; repeat until
   PASS (max 3 iterations).
6. **qa-reviewer** compares source vs `page.png` for content/accuracy →
   `work\<stem>\qa.md`; strict drift check on label-critical figures. On FAIL, fix
   and re-render.

The main session is the orchestrator. Run `/rebuild` to process the folder.

## Selecting which images to process
- A finished `output\<stem>.pdf` marks an image done; skipped on a plain run.
- `/rebuild` → all pending root images, minus `ignore.txt`.
- `/rebuild <name...>` → only those, forced.
- `/rebuild all` → full refresh.

- `/status` → done/pending, QA result, ignored.
- `/style-anchor` → generate style candidates to choose from.

## Translation consistency
Translate idiomatically into the target language using its established terms for
the sheet's subject area. Where a term has
more than one valid translation, pick one and use it consistently across the whole
set. If a term has no settled equivalent in the target language, choose the
clearest option and
add a `note` field in `translated.json` so it can be reviewed.
