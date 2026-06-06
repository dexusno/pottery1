# Pottery → Norwegian PDF rebuild

A [Claude Code](https://docs.claude.com/en/docs/claude-code/overview) pipeline that
rebuilds ceramics-course image sheets (handwritten notes, infographics, illustrated
guides) into clean, typeset **A4 PDFs**:

- body text translated to **Norwegian Bokmål** (the main title stays in English),
- every figure reimagined in one consistent **warm studio-sketch** style,
- while **preserving each figure's instructional meaning** — labeled diagrams fall
  back to the original drawing rather than risk an inaccurate redraw.

## How it works

A team of Claude Code subagents, orchestrated by the main session:

```
extractor → crop → illustrator → translator → layout-builder ⇄ layout-qc → qa-reviewer
```

| Agent | Job |
|---|---|
| `extractor` | Reads the image; captures text + figure regions with a `preserve` list. |
| `illustrator` | Redraws each figure in the house style via gpt-image-2, against `style/anchor.png`. |
| `translator` | Translates text to Bokmål (title unchanged); flags uncertain ceramics terms. |
| `layout-builder` | Rebuilds the page as HTML, renders to PDF/PNG. |
| `layout-qc` | Visual/typography critic; demands alignment/spacing fixes in a loop. |
| `qa-reviewer` | Checks content/accuracy against the original; strict on labeled figures. |

The full brief — hard rules, art direction, palette, fonts, and the Norwegian
ceramics glossary — lives in [`CLAUDE.md`](CLAUDE.md).

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
- `OPENAI_API_KEY` in the environment, for figure reimagining via **gpt-image-2**
  (requires OpenAI Organization Verification). Reimagining is optional — without a
  key the pipeline runs and keeps the original drawings.
  
- Copy `.claude/settings.json.example` to `.claude/settings.json` and replace
   sk-REPLACE_ME with your OpenAI API key (this file is gitignored).
   On Windows PowerShell: Copy-Item .claude/settings.json.example .claude/settings.json

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
   /rebuild IMG_7450.JPG
   /rebuild all
   ```

Finished PDFs land in `output/`.

## Folder layout

```
D:\pottery\
  <source images>.jpg/.png      source sheets (gitignored)
  CLAUDE.md                     project brief / rules / glossary
  style\anchor.png              approved style reference (tracked)
  scripts\                      crop.py, render_pdf.py, illustrate.py
  .claude\agents\               the six subagents
  .claude\commands\             /style-anchor, /rebuild, /status
  work\<stem>\                  intermediates (gitignored)
  output\<stem>.pdf             deliverables (gitignored)
  ignore.txt                    optional: images to skip (gitignored)
```

## Notes

- This repo is **public**. Source images and `output/` are gitignored because the
  course sheets are the instructor's content. Track a specific file with
  `git add -f <name>`.
- `style/anchor.png` is tracked, so the look is portable across machines.
- gpt-image-2 has no transparent background; figures render on warm cream and
  outputs carry an invisible SynthID watermark.
