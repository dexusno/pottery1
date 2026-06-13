# Sheet2PDF — image sheets → translated A4 PDFs

> Rebuild image sheets — handwritten notes, infographics, illustrated guides, any subject — into clean, typeset **A4 PDFs in the language of your choice** (or the original): text translated, every figure repainted by AI in one consistent hand.

[![Built with Claude Code](https://img.shields.io/badge/built%20with-Claude%20Code-B85C38)](https://docs.claude.com/en/docs/claude-code/overview)
[![Images](https://img.shields.io/badge/figures-gpt--image--2-412991)](https://platform.openai.com/)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows-blue)](#setup)
[![Output](https://img.shields.io/badge/output-single%20A4%20PDF-success)](#)

A team of [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) subagents turns a folder of course sheets into a matching set of handouts. Each sheet becomes **one A4 portrait PDF**: the body is translated to your **TARGET LANGUAGE** (default Norwegian Bokmål; measurements optionally converted to **metric**), and every figure is **regenerated in a single consistent style** from the original drawing — so a set of sheets that started as a mix of handwriting, clip-art, and infographics ends up looking like it came from one designer.

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
- [Customization](#customization)
- [Commands](#commands)
- [Under the Hood](#under-the-hood)
- [Folder Layout](#folder-layout)
- [Troubleshooting](#troubleshooting)
- [Notes](#notes)

---

## Features

- **One consistent look** — every figure is repainted in the style of a single approved anchor image, so the whole set matches.
- **Faithful, not invented** — figures reproduce the original's content exactly (same elements, same visual weight); only the rendering medium changes.
- **Any target language — or none** — set `TARGET LANGUAGE` in `CLAUDE.md` to any language (default: Norwegian Bokmål) or to `original` to keep the source text untouched. Translation is idiomatic, keeps established loanwords, and a separate `UNITS` setting controls imperial→metric conversion.
- **Single A4, always** — content is scaled to fit and fill exactly one A4 portrait page.
- **Layout-aware** — infers each sheet's structure (steps, comparison columns, labeled diagram) instead of forcing a template.
- **Fast on dense sheets** — figures generate concurrently (a 25-figure sheet drops from ~1 hour to ~15–20 minutes), generation size scales to each figure's printed size, and translation runs while figures generate.
- **Two quality gates** — a visual/typography critic and a correctness reviewer that checks the rebuild against the original, figure by figure.
- **Reproducible** — the look lives in a tracked style anchor and a shared stylesheet, portable across machines.
- **Domain-neutral** — works for any subject: drop in your sheets, set a style anchor (and optionally fonts/palette, below) and the pipeline produces a matching set. Originally built for a ceramics course; that look ships as the default.

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
[3] illustrator  ──┐    repaints every figure via gpt-image-2 — ONE concurrent
  │ (in parallel)  │    batch (default 4 workers), size matched to each crop
[4] translator   ──┘    text → TARGET LANGUAGE (or kept original), units per UNITS
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
Polished A4 PDF (target language)
```

### The agents

**`extractor`** — Reads one source image and records its structure to `extract.json`: the title (normalized to a single line), every text block (verbatim, with a role and position), and every figure as a normalized crop box with a description, a `preserve` list of elements that must survive a restyle, and any text inside the figure. It infers the sheet's actual layout and crops a coherent scene as **one** figure rather than splitting it.

**`crop.py`** — A plain script (not an agent). Cuts each crop box out of the source into `crops\<name>.png` to feed the illustrator.

**`illustrator`** — Regenerates **every** figure. For each crop it calls **gpt-image-2** in edit mode with the original crop as the content to reproduce and `style\anchor.png` as the style to match, writing `<name>_v2.png` — all figures generate **concurrently** in one batch (default 4 workers; tune for your OpenAI rate limits). It reproduces the figure faithfully — same elements at the same visual weight, original text kept — changing only the medium. The original crop is input only and is never used as output. If the API errors (e.g. missing key), the run **stops loudly** instead of substituting the original.

**`translator`** — Translates `extract.json` into `translated.json` per the `TARGET LANGUAGE` and `UNITS` settings in `CLAUDE.md`: idiomatic translation (title included) keeping established loanwords, with optional imperial→metric conversion — or a faithful pass-through when the target is `original`. Uncertain domain terms get a `note` flag.

**`layout-builder`** — Rebuilds the page as `page.html` using **only** the shared stylesheet (no hardcoded styling), choosing a structure that matches the source. It embeds the regenerated `_v2.png` figures, keeps the title on one line, and scales content to fit and fill a single A4 portrait page, then renders the PDF + a preview PNG via headless Chromium.

**`layout-qc`** — A visual/typography critic that judges the rendered PNG: A4 fit, vertical balance, alignment, no stray decoration, consistent palette/fonts. It writes a PASS/FAIL punch-list; the orchestrator loops layout-builder ⇄ layout-qc until it passes (max 3).

**`qa-reviewer`** — The correctness gate, run last. It compares the finished page and each figure against the original: information completeness, translation per the language/units settings, figure content (same elements, nothing added/dropped/over-emphasized), figure style (matches the anchor on white), and layout fidelity. A bad figure is sent back to be remade (≤2 tries) and then flagged — the original is never substituted.

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
| **Claude Code** | Yes | Any current version — run `claude update` to stay up to date |
| **Python 3.9+** | Yes | `pip install pillow playwright openai pypdf` then `playwright install chromium` |
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
2. Launch Claude Code:
   ```powershell
   cd D:\<your-project>
   claude
   ```
   A more capable model gives better figure and layout judgment, but any model works.
3. Establish the look once: run `/style-anchor`, then copy your favourite candidate to `style/anchor.png`.
4. Test one sheet, then run the set:
   ```
   /rebuild IMG_7436.JPG
   /rebuild all
   ```

Finished PDFs land in `output/`.

---

## Customization

**Language:** set the two lines at the top of `CLAUDE.md` — `TARGET LANGUAGE:` (any language, or `original` to skip translation entirely) and `UNITS:` (`metric` or `original`).

**Models (cost vs quality):** two more lines in `CLAUDE.md` — `PREMIUM MODEL:` and `WORKFLOW MODEL:`. The premium model runs the three judgment-heavy agents (**extractor**, **layout-qc**, **qa-reviewer** — careful vision and critique, where quality is enforced); the workflow model runs the mechanical three (**illustrator**, **translator**, **layout-builder** — templated prompts, translation, HTML assembly). Defaults: `opus` / `sonnet`, which keeps the premium eye on the gates while the plumbing runs cheap. Values can be a model alias (`opus`, `sonnet`, `haiku`, `fable`), a full model ID, or `inherit` to follow the session's model (set both to `inherit` to disable tiering). The orchestrator passes the model explicitly on every delegation — the most reliable mechanism — and each delegation in the session trace shows which model ran, so you can verify the tiering on your first run. Two details worth knowing: an **alias resolves to the latest model of that tier** and silently upgrades when a new one ships — use a full model ID to pin a version (check what's running with `/status` or the model+effort label next to the spinner). And **thinking depth is controlled by effort** (`low`–`max`), tiered per agent in the frontmatter (`effort: high` ships on the three premium agents, `effort: medium` on the workflow three); set the session's own effort with `/effort`. Note that the figures' art quality is unaffected by any of this: it comes from gpt-image-2 and your anchor.

Everything else below is about the look.

Everything that defines the look lives under `style\` and follows one rule: **if present use it, if absent ignore it** (the defaults apply unchanged).

| File | Controls | Behavior |
|---|---|---|
| `style\anchor.png` | Illustration style | Passed to gpt-image-2 on every figure; swap it (via `/style-anchor`) and the whole set's art changes. Size-independent — any reasonable PNG/JPG works; ~1024 px is the sweet spot (it rides along on every figure call, so a huge file slows and costs more per figure). |
| `style\fonts\title.ttf` / `.otf` | Title font | Used for titles/headings instead of the default (Fraunces). |
| `style\fonts\body.ttf` / `.otf` | Body font | Used for body text instead of the default (Nunito). A single font file with any name is used for **both** roles. |
| `style\palette.json` | Colors | Any subset of the five roles below; omitted keys keep their defaults. See `style\palette.json.example`. |

The palette roles (all `#RRGGBB`):

```json
{
  "primary":   "#B85C38",
  "secondary": "#8C9A7B",
  "ink":       "#3A3330",
  "page_bg":   "#FFFFFF",
  "tint":      "#ECEFE6"
}
```

What each role literally changes on the page:

| Role | What you will see change |
|---|---|
| `primary` | The big page title, section headings, and accent marks. |
| `secondary` | Step names, sub-headings, and small markers. |
| `ink` | All body text and bullet lines. Keep it dark — it has to read at print size. |
| `page_bg` | The paper color behind **everything, including figures**. Keep it `#FFFFFF` unless you also change the figure background in CLAUDE.md's CONSTRAINTS line — figures are generated on white, so a non-white page puts a visible white box around every figure. |
| `tint` | The faint shading on alternating rows in step tables. Keep it very close to `page_bg` — it should be barely visible. |

**Don't want to pick colors by hand?** Run `/style-anchor palette` — it derives a suggested `palette.json` from the anchor image's own colors (role-aware: it picks a readable ink, a saturated mid-tone primary, a different-hue secondary, and guards text contrast). It never overwrites an existing `palette.json`; if one exists it writes `palette.json.suggested` for you to review. The suggestion is a starting point — edit it to taste.

At the start of every `/rebuild`, `scripts\stylegen.py` regenerates `styles\custom.css` from whatever is present (an empty stub when nothing is). Pages link `page.css` then `custom.css`, so overrides win by cascade. To re-theme an entire project for a different subject: replace the anchor, optionally drop in fonts and a palette, edit the ART DIRECTION block in `CLAUDE.md`, and `/rebuild all`.

---

## Commands

| Command | What it does |
|---|---|
| `/style-anchor [count] [guidance…]` | Generate style candidates; optional text guides subject and/or style (e.g. `/style-anchor 4 garden tools, more ink less wash`). Copy your favourite to `style/anchor.png`. |
| `/style-anchor palette` | Suggest a `style/palette.json` from the anchor's colors (never overwrites an existing one). |
| `/rebuild` | Process all pending images. |
| `/rebuild <name…>` | Process specific images (forced re-run). |
| `/rebuild all` | Full refresh of the whole set. |
| `/rebuild … --generate` | Re-interpret each figure in the anchor's style (refined redraw) instead of faithfully restyling the original. Looser; best for decorative/illustrative sheets, not label-critical diagrams. Sizing/layout stay tight either way. |
| `/progress` | Table of done / pending / QA result / ignored. (Named to avoid shadowing Claude Code's built-in `/status`.) |

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
D:\<your-project>\
  <source images>.jpg/.png        source sheets (gitignored)
  CLAUDE.md                       project brief / rules / art direction
  styles\page.css                 shared design system (palette, fonts, layouts)
  style\anchor.png                approved style reference (tracked)
  scripts\                        crop.py, render_pdf.py, illustrate.py
  .claude\agents\                 the six subagents
  .claude\commands\               /style-anchor, /rebuild, /progress
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
Your `style/anchor.png` is the culprit — the model matches the anchor. Regenerate it with `/style-anchor` until you get a sample in your intended style, then re-copy it to `style/anchor.png`.

**Bash errors / backslash path failures**
PowerShell isn't the default shell. Ensure `.claude/settings.json` has `"defaultShell": "powershell"` and `"CLAUDE_CODE_USE_POWERSHELL_TOOL": "1"`, then restart.

**A figure's text is garbled**
gpt-image-2 sometimes mangles text when restyling; `qa-reviewer` flags it for a remake. Persistent cases are flagged for you to handle in the image step.

---

## Notes

- This repo is **public**. Source images and `output/` are gitignored — source sheets often belong to someone else (a course, a client), so they stay local by default. Track a specific file with `git add -f <name>`.
- `style/anchor.png` is tracked, so the look is portable across machines.
- gpt-image-2 outputs carry an invisible SynthID watermark.
