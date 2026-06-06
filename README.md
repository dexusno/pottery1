# Pottery → Norwegian PDF rebuild

A [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) pipeline that
rebuilds ceramics-course image sheets (handwritten notes, infographics, illustrated
guides) into clean, typeset **single-A4 PDFs**:

- all text translated to **Norwegian Bokmål** (keeping words Norwegians commonly use
  in English, and converting measurements to metric),
- every figure **regenerated in one consistent style** from the original drawing,
- on one **A4 portrait** page per source image.

## How it works

The pipeline is a team of Claude Code subagents, each with a single job, orchestrated
by the main session via the `/rebuild` command. They run in sequence, one source
image at a time, passing intermediate files through a per-image `work\<stem>\` folder.

```
extractor → crop.py → illustrator → translator → layout-builder ⇄ layout-qc → qa-reviewer
```

**extractor** — Reads one source image and records its structure to
`work\<stem>\extract.json`: the title (normalized to a single line), every text block
(verbatim, with a role and position), and every figure as a normalized crop box with
a description, a `preserve` list of the elements that must survive a restyle, and any
text inside the figure. It infers each sheet's actual layout rather than assuming a
format, and crops a coherent scene (e.g. an action and the object it acts on) as one
figure instead of splitting it.

**crop.py** — A plain script (not an agent). Cuts each crop box out of the source
image into `work\<stem>\crops\<name>.png` to feed the illustrator.

**illustrator** — Regenerates every figure in one consistent look. For each crop it
calls **gpt-image-2** in edit mode, passing the original crop as the content to
reproduce and `style\anchor.png` as the style to match. It reproduces the figure
faithfully — same elements at the same visual weight, original text kept — changing
only the rendering medium, and writes `<name>_v2.png`. Every figure is always
regenerated; the original crop is input only and is never used as an output. If the
image API errors (e.g. a missing key), the run stops loudly rather than silently
substituting the original.

**translator** — Translates `extract.json` into `work\<stem>\translated.json` as
idiomatic Bokmål — title included — keeping a word in English where that is the form
Norwegians actually use (an established anglicism), and converting any imperial
measurements to metric. Uncertain ceramics terms get a `note` flag for review.

**layout-builder** — Rebuilds the page as `work\<stem>\page.html` using only the
shared stylesheet `styles\page.css` (no hardcoded styling), choosing a structure that
matches the source (step grid, comparison columns, labeled diagram, or a simple
stack). It embeds the regenerated `_v2.png` figures, keeps the title on one line, and
scales content to fit and fill a single A4 portrait page, then renders to
`output\<stem>.pdf` and a `page.png` via headless Chromium.

**layout-qc** — A visual/typography critic that judges the rendered `page.png`: A4
fit, vertical balance, alignment/spacing, no stray decoration, consistent palette and
fonts. It writes a PASS/FAIL punch-list; the orchestrator loops layout-builder ⇄
layout-qc until it passes (max 3 rounds).

**qa-reviewer** — The correctness gate, run last. It compares the finished page and
each regenerated figure against the original image: information completeness, natural
Bokmål with metric units, figure content (same elements, nothing added, dropped, or
over-emphasized), figure style (matches the anchor's medium and palette on white),
and layout fidelity. A bad figure is sent back to the illustrator to remake (≤2
tries) and then flagged for you — the original is never substituted.

The shared rules everything obeys — hard rules, the house art direction, palette, and
fonts — live in [`CLAUDE.md`](CLAUDE.md); the shared visual design system lives in
[`styles/page.css`](styles/page.css). Agents reference these rather than inventing
their own styling, which is what keeps every page in a set looking identical.

## Commands

- `/style-anchor [count]` — generate style candidates; copy your favorite to `style/anchor.png`.
- `/rebuild` — process all pending images. `/rebuild <name…>` for specific ones (forced). `/rebuild all` for a full refresh.
- `/status` — table of done / pending / QA result / ignored.

## Requirements

- Claude Code **v2.1.154+** (for Opus 4.8) — `claude update`
- Python 3.9+:
  ```
  pip install pillow playwright openai
  playwright install chromium
  ```
- An **`OPENAI_API_KEY`** is required — figure regeneration uses **gpt-image-2**
  (which needs OpenAI Organization Verification). Without a valid key the run stops
  with an error; it does not fall back to the original drawings.

### Setup (Windows / PowerShell)

Copy `.claude/settings.json.example` to `.claude/settings.json` and replace
`sk-REPLACE_ME` with your OpenAI key. This file is gitignored, sets PowerShell as the
default shell, and injects the key into every session:
```
Copy-Item .claude/settings.json.example .claude/settings.json
```

## Usage

1. Put source images (`*.jpg` / `*.png`) in the project root.
2. Launch and select the model:
   ```
   cd D:\pottery
   claude
   /model claude-opus-4-8
   ```
3. Establish the look once: `/style-anchor`, then copy your chosen candidate to `style/anchor.png`.
4. Test one sheet, then run the set:
   ```
   /rebuild IMG_7436.JPG
   /rebuild all
   ```

Finished PDFs land in `output/`.

## Folder layout

```
D:\pottery\
  <source images>.jpg/.png      source sheets (gitignored)
  CLAUDE.md                     project brief / rules / art direction
  styles\page.css               shared design system (palette, fonts, layouts)
  style\anchor.png              approved style reference (tracked)
  scripts\                      crop.py, render_pdf.py, illustrate.py
  .claude\agents\               the six subagents
  .claude\commands\             /style-anchor, /rebuild, /status
  .claude\settings.json.example PowerShell + key template (copy to settings.json)
  work\<stem>\                  intermediates (gitignored)
  output\<stem>.pdf             deliverables (gitignored)
  ignore.txt                    optional: images to skip (gitignored)
```

## Notes

- This repo is **public**. Source images and `output/` are gitignored because the
  course sheets are the instructor's content. Track a specific file with
  `git add -f <name>`. Your real `.claude/settings.json` (with the key) is gitignored;
  only the `.example` is committed.
- `style/anchor.png` is tracked, so the look is portable across machines.
- gpt-image-2 has no transparent background; figures render on solid white (matching
  the page), and outputs carry an invisible SynthID watermark.
