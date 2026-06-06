# Pottery course sheets → Norwegian PDF rebuild

## Goal
Rebuild each source image (handwritten notes, infographics, illustrated guides
for a ceramics course) as a beautiful, typeset **A4 PDF** with body text
translated to **Norwegian Bokmål**, every figure reimagined in ONE consistent
"warm studio sketch" illustration style, while preserving each sheet's layout,
structure, and the instructional meaning of every figure.

## Sheets vary
Source sheets differ widely — handwritten or typeset, dense or sparse, any layout,
any text size, portrait or landscape. These rules are general: infer each sheet's
structure from the source itself, never assume a fixed format.

## Hard rules
1. **Header stays English.** The main page title/header is kept verbatim in English.
   Everything else (steps, bullets, labels, captions) is translated to Bokmål.
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
"Warm hand-drawn studio-sketch illustration. Confident, slightly loose ink
linework with soft gouache/watercolor washes. Earthy ceramics-studio palette:
terracotta/rust as the primary accent, muted sage green and soft charcoal as
secondaries. Cozy, artisanal, friendly. Single subject, centered, generous margins,
on a plain solid white background. Reproduce any text that appears in the source
figure clearly, legibly, and spelled exactly as given; do not add text that isn't
there. No border, no frame."

### Palette (used for BOTH the illustrations and the page)
- Terracotta / rust (primary accent, titles): #B85C38
- White (page + figure background):           #FFFFFF
- Sage green (secondary accent):              #8C9A7B
- Soft charcoal (body text, linework):        #3A3330
- Faint sage tint (alternating row shading):  #ECEFE6

### Fonts (Google Fonts)
- Titles / headers: "Fraunces" (warm, characterful)
- Body / bullets / labels: "Nunito" (clean), system-ui fallback

The palette and fonts above are implemented once in `styles\page.css`; the
layout-builder links that file and never hardcodes colors, fonts, or spacing, so
every page is identical in style.

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
3. **illustrator** redraws every crop in the house style against `style\anchor.png`
   → `work\<stem>\crops\<name>_v2.png` candidates. Uses gpt-image-2 with
   `quality: high` for label-critical figures, `medium` otherwise; references the
   inputs by index and restates each crop's preserve list (per gpt-image-2 docs).
4. **translator** → `work\<stem>\translated.json` (title unchanged).
5. **layout-builder** → `page.html` (house palette + fonts, preferring approved
   `_v2.png`), then
   `python scripts\render_pdf.py work\<stem>\page.html output\<stem>.pdf --png work\<stem>\page.png`.
6. **layout-qc** (visual/typography critic) inspects `page.png` → `qa_layout.md`.
   On FAIL, the layout-builder applies the punch-list and re-renders; repeat until
   PASS (max 3 iterations).
7. **qa-reviewer** compares source vs `page.png` for content/accuracy →
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
Translate into idiomatic Bokmål using established ceramics terms. Where a term has
more than one valid translation, pick one and use it consistently across the whole
set. If a term has no settled Norwegian equivalent, choose the clearest option and
add a `note` field in `translated.json` so it can be reviewed.
