# Pottery → Norwegian PDF rebuild

> Rebuild English ceramics-course image sheets into clean, typeset **Norwegian A4 PDFs** — text translated, every figure repainted by AI in one consistent hand.

[![Built with Claude Code](https://img.shields.io/badge/built%20with-Claude%20Code-B85C38)](https://docs.claude.com/en/docs/claude-code/overview)
[![Model](https://img.shields.io/badge/model-Claude%20Opus%204.8-B85C38)](https://docs.claude.com/en/docs/claude-code/overview)
[![Images](https://img.shields.io/badge/figures-gpt--image--2-412991)](https://platform.openai.com/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows-blue)](#setup)
[![Output](https://img.shields.io/badge/output-single%20A4%20PDF-success)](#)

A team of [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) subagents turns a folder of course sheets into a matching set of handouts. Each sheet becomes **one A4 portrait PDF**: the body is translated to **Norwegian Bokmål** (with measurements converted to **metric**), and every figure is **regenerated in a single consistent style** from the original drawing — so a set of sheets that started as a mix of handwriting, clip-art, and infographics ends up looking like it came from one designer.

---

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
  - [The pipeline](#the-pipeline)
  - [The agents](#the-agents)
  - [The shared design system](#the-shared-design-system)
- [Cost](#cost)
- [Requirements](#requirements)
- [Setup](#setup)
- [Usage](#usage)
- [Commands](#commands)
- [Under the Hood](#under-the-hood)
- [Folder Layout](#folder-layout)
- [Troubleshooting](#troubleshooting)
- [Notes](#notes)

---

## Features

- **One consistent look** — every figure is repainted in the style of a single approved anchor image, so the whole set matches.
- **Faithful, not invented** — figures reproduce the original's content exactly (same elements, same visual weight); only the rendering medium changes.
- **Norwegian Bokmål** — all text translated idiomatically, keeping words Norwegians actually use in English, with imperial measurements converted to metric.
- **Single A4, always** — content is scaled to fit and fill exactly one A4 portrait page.
- **Layout-aware** — infers each sheet's structure (steps, comparison columns, labeled diagram) instead of forcing a template.
- **Two quality gates** — a visual/typography critic and a correctness reviewer that checks the rebuild against the original, figure by figure.
- **Reproducible** — the look lives in a tracked style anchor and a shared stylesheet, portable across machines.

---

## How It Works

A team of Claude Code subagents, each with one job, orchestrated by the main session through the `/rebuild` command. They run in sequence, one source image at a time, passing intermediates through a per-image `work\<stem>\` folder.

### The pipeline

```
Source sheet (.jpg / .png)
  │
  ▼
[1] extractor       ─── reads the image → structure (title, text, figure crops) as JSON
  │
  ▼
[2] crop.py         ─── cuts each figure region out of the source image
  │
  ▼
[3] illustrator     ─── repaints every figure in the anchor's style via gpt-image-2
  │
  ▼
[4] translator      ─── text → Bokmål, keep common anglicisms, convert units to metric
  │
  ▼
[5] layout-builder  ─── rebuilds the page from the shared CSS → A4 PDF + preview PNG
  │   ⇅   layout-qc loop (max 3 rounds)
[6] layout-qc       ─── visual/typography critic: A4 fit, balance, alignment
  │
  ▼
[7] qa-reviewer     ─── correctness gate vs the original: info, figures, style, layout
  │
  ▼
Polished A4 PDF (Norwegian)
```

### The agents

**`extractor`** — Reads one source image and records its structure to `extract.json`: the title (normalized to a single line), every text block (verbatim, with a role and position), and every figure as a normalized crop box with a description, a `preserve` list of elements that must survive a restyle, and any text inside the figure. It infers the sheet's actual layout and crops a coherent scene as **one** figure rather than splitting it.

**`crop.py`** — A plain script (not an agent). Cuts each crop box out of the source into `crops\<name>.png` to feed the illustrator.

**`illustrator`** — Regenerates **every** figure. For each crop it calls **gpt-image-2** in edit mode with the original crop as the content to reproduce and `style\anchor.png` as the style to match, writing `<name>_v2.png`. It reproduces the figure faithfully — same elements at the same visual weight, original text kept — changing only the medium. The original crop is input only and is never used as output. If the API errors (e.g. missing key), the run **stops loudly** instead of substituting the original.

**`translator`** — Translates `extract.json` into `translated.json` as idiomatic Bokmål — title included — keeping a word in English where that is the form Norwegians actually use (an established anglicism), and converting imperial measurements to metric. Uncertain ceramics terms get a `note` flag.

**`layout-builder`** — Rebuilds the page as `page.html` using **only** the shared stylesheet (no hardcoded styling), choosing a structure that matches the source. It embeds the regenerated `_v2.png` figures, keeps the title on one line, and scales content to fit and fill a single A4 portrait page, then renders the PDF + a preview PNG via headless Chromium.

**`layout-qc`** — A visual/typography critic that judges the rendered PNG: A4 fit, vertical balance, alignment, no stray decoration, consistent palette/fonts. It writes a PASS/FAIL punch-list; the orchestrator loops layout-builder ⇄ layout-qc until it passes (max 3).

**`qa-reviewer`** — The correctness gate, run last. It compares the finished page and each figure against the original: information completeness, natural Bokmål with metric units, figure content (same elements, nothing added/dropped/over-emphasized), figure style (matches the anchor on white), and layout fidelity. A bad figure is sent back to be remade (≤2 tries) and then flagged — the original is never substituted.

### The shared design system

The rules every agent obeys live in two files, so no agent invents its own styling — this is what keeps a set uniform:

- **[`CLAUDE.md`](CLAUDE.md)** — hard rules, the house art direction (injected into every image prompt), palette, and fonts.
- **[`styles/page.css`](styles/page.css)** — the visual system: palette variables, fonts, and the layout primitives (`.step-grid`, `.compare`, `.diagram`) the layout-builder composes.

---

## Cost

Figure regeneration uses the **gpt-image-2** API (everything else — Claude Code, the layout, the QC — is part of your Claude subscription).

| Item | Approx. cost |
|---|---|
| One regenerated figure (~1024², medium quality) | ~$0.04 |
| A typical sheet (2–4 figures) | ~$0.08–0.16 |
| A 20-sheet set | ~$2–4 |

> [!NOTE]
> These are rough estimates based on gpt-image-2 pricing observed in 2026 and will vary with image size and quality (label-heavy figures use `high`). Always check [OpenAI's current pricing](https://platform.openai.com/) before processing a large set. Every figure is regenerated on each `/rebuild`, so re-running a set re-incurs cost.

---

## Requirements

| Component | Required | Notes |
|---|---|---|
| **Claude Code v2.1.154+** | Yes | For Opus 4.8 — `claude update` |
| **Python 3.9+** | Yes | `pip install pillow playwright openai` then `playwright install chromium` |
| **OpenAI API key** | Yes | For gpt-image-2; needs OpenAI **Organization Verification**. Without a valid key the run stops with an error — it does **not** fall back to the original drawings. |
| **A style anchor** | Yes | One approved reference image at `style/anchor.png` (create with `/style-anchor`) |

---

## Setup

This project runs on Windows with PowerShell as the shell.

Copy the settings template and add your key:

```powershell
Copy-Item .claude/settings.json.example .claude/settings.json
notepad .claude/settings.json      # replace sk-REPLACE_ME with your OpenAI key
```

This file sets PowerShell as the default shell and injects `OPENAI_API_KEY` into every Claude Code session.

> [!IMPORTANT]
> Your real `.claude/settings.json` is gitignored — only the `.example` (placeholder key) is committed. Never put your key in `.claude/settings.json` *and* commit it; the repo is public.

---

## Usage

1. Put source images (`*.jpg` / `*.png`) in the project root.
2. Launch Claude Code and select the model:
   ```powershell
   cd D:\pottery
   claude
   /model claude-opus-4-8
   ```
3. Establish the look once: run `/style-anchor`, then copy your favourite candidate to `style/anchor.png`.
4. Test one sheet, then run the set:
   ```
   /rebuild IMG_7436.JPG
   /rebuild all
   ```

Finished PDFs land in `output/`.

---

## Commands

| Command | What it does |
|---|---|
| `/style-anchor [count]` | Generate style candidates; copy your favourite to `style/anchor.png`. |
| `/rebuild` | Process all pending images. |
| `/rebuild <name…>` | Process specific images (forced re-run). |
| `/rebuild all` | Full refresh of the whole set. |
| `/status` | Table of done / pending / QA result / ignored. |

---

## Under the Hood

<details>
<summary><strong>Click to expand — the design decisions behind the pipeline</strong></summary>

### Why every figure is always regenerated

Earlier versions cached or reused figures and could fall back to the original crop when generation failed. That quietly served stale, un-styled figures and made it impossible to tell whether the model had actually run. The pipeline now **always** regenerates every figure and **never** substitutes the original — and a generation failure (missing key, unverified org, rate limit) **stops the run loudly** rather than hiding behind the original. The cure for a failure is to fix it, not to mask it.

### A restyle, never a new drawing

The original crop is the content guide; the anchor is the style. The illustrator is told to reproduce the crop exactly — same shapes, counts, arrangement, and every element at the **same visual weight** — changing only the medium. An over-eager "preserve every decorative detail" instruction once caused the model to enlarge incidental elements and split scenes into extra panels; the rule was rebalanced to "add nothing, drop nothing, emphasize nothing."

### One anchor locks the whole set

A single approved reference at `style/anchor.png` is passed to gpt-image-2 on every figure, so the entire set shares one hand. Change the anchor and the whole look changes.

### Two gates, two jobs

`layout-qc` judges the page as a **design** (does it look good on A4?) in a fix-and-re-render loop. `qa-reviewer` judges the page as a **rebuild** (is it true to the original?) — including a style-match check that flags any figure that came back flat or off-palette. Splitting craft from correctness keeps each check focused.

### Lean, general agents

LLM agents skip items when handed a long checklist, and the sheets vary widely. So each agent is kept short and its rules are written generally — no instruction is tied to a specific test sheet. Agents infer structure from the source rather than matching a template.

### White backgrounds

Figures and the page are both white. Matching the model's output to an exact cream hex was unreliable and left visible boxes around each figure; white-on-white blends seamlessly.

### gpt-image-2 specifics

The edit endpoint preserves content well; quality is `high` for label-heavy figures and `medium` otherwise; `input_fidelity` is omitted (requesting it fails); there is no transparent background (figures render on solid white); sizes are aspect-matched to each crop. Outputs carry an invisible SynthID watermark.

</details>

---

## Folder Layout

```
D:\pottery\
  <source images>.jpg/.png        source sheets (gitignored)
  CLAUDE.md                       project brief / rules / art direction
  styles\page.css                 shared design system (palette, fonts, layouts)
  style\anchor.png                approved style reference (tracked)
  scripts\                        crop.py, render_pdf.py, illustrate.py
  .claude\agents\                 the six subagents
  .claude\commands\               /style-anchor, /rebuild, /status
  .claude\settings.json.example   PowerShell + key template (copy to settings.json)
  work\<stem>\                    intermediates (gitignored)
  output\<stem>.pdf               deliverables (gitignored)
  ignore.txt                      optional: images to skip (gitignored)
```

---

## Troubleshooting

**Run stops with "GENERATION FAILED" / no key**
`OPENAI_API_KEY` isn't reaching the session. Confirm `.claude/settings.json` exists with your real key, restart Claude Code, and check `echo $env:OPENAI_API_KEY`.

**gpt-image-2 returns an authorization/verification error**
The API requires OpenAI **Organization Verification**. Complete it in your OpenAI account.

**Figures come back as flat line-art or on a white box that doesn't match**
Your `style/anchor.png` is the culprit — the model matches the anchor. Regenerate it with `/style-anchor` until you get a warm gouache/ink sample, then re-copy it to `style/anchor.png`.

**Bash errors / backslash path failures**
PowerShell isn't the default shell. Ensure `.claude/settings.json` has `"defaultShell": "powershell"` and `"CLAUDE_CODE_USE_POWERSHELL_TOOL": "1"`, then restart.

**A figure's text is garbled**
gpt-image-2 sometimes mangles text when restyling; `qa-reviewer` flags it for a remake. Persistent cases are flagged for you to handle in the image step.

---

## Notes

- This repo is **public**. Source images and `output/` are gitignored because the course sheets are the instructor's content. Track a specific file with `git add -f <name>`.
- `style/anchor.png` is tracked, so the look is portable across machines.
- gpt-image-2 outputs carry an invisible SynthID watermark.
