---
description: Rebuild image sheets into translated A4 PDFs (target language set in CLAUDE.md). No args = all pending; names = just those (forced); "all" = full refresh.
argument-hint: [image names | all]
---

Decide the target set from $ARGUMENTS:
- EMPTY → every image (*.jpg, *.jpeg, *.png) in the project root that does NOT
  already have output\<stem>.pdf, minus any filename listed in ignore.txt.
- "all" → every root image, regardless of existing output and regardless of
  ignore.txt (a forced full refresh).
- one or more NAMES (space- or comma-separated, with or without extension) →
  ONLY those images, forced (reprocess even if a PDF exists). ignore.txt does
  not apply to explicitly named images.

Always ignore files under work\, output\, scripts\, and .claude\.
If ignore.txt exists at the root, treat each non-empty line that does not start
with # as a filename to skip (applies to the no-arg run only).

MODELS: read PREMIUM MODEL and WORKFLOW MODEL from CLAUDE.md. On EVERY subagent
delegation below, pass the model parameter explicitly: extractor, layout-qc, and
qa-reviewer get the PREMIUM model; illustrator, translator, and layout-builder get
the WORKFLOW model. (`inherit` = pass no model parameter.)

Before the first image: run `python scripts/stylegen.py` (regenerates
styles/custom.css from optional style/fonts and style/palette.json; writes an
empty stub when no overrides are present). If it fails, STOP and report.

For each selected image, in order, following CLAUDE.md:
1. Delegate to the extractor subagent → work\<stem>\extract.json.
2. Run: python scripts\crop.py <image> work\<stem>\crops work\<stem>\extract.json
3. Delegate to the illustrator AND translator subagents IN PARALLEL (invoke both in
   one message — each depends only on extract.json/crops, not on the other):
   - illustrator → regenerates a fresh _v2.png for EVERY crop from its original
     (img2img restyle vs style\anchor.png, one concurrent batch, original figure
     text kept). Always regenerate — there is no reuse path.
   - translator → work\<stem>\translated.json.
   Wait for BOTH before continuing. If the illustrator reports any failed
   generation (e.g. missing OPENAI_API_KEY), STOP and report — never fall back to
   the original crops.
4. Delegate to the layout-builder subagent → output\<stem>.pdf + page.png.
5. Delegate to the layout-qc subagent (visual/typography) → work\<stem>\qa_layout.md.
   If RESULT: FAIL, have the layout-builder apply the punch-list and re-render;
   repeat until PASS (max 3 iterations).
6. Delegate to the qa-reviewer subagent (content vs original) → work\<stem>\qa.md.
7. If qa-reviewer FAILs, apply fixes and redo from the failed step (max 2 retries).
   If it rejected a reimagined figure as inaccurate, send that figure back to the
   illustrator to REMAKE (retry, high quality, tighter preserve) up to 2 times;
   if it still fails, leave qa as FAIL and surface the figure to the user — never
   substitute the original crop into the page.

Independent images may be processed in parallel, but keep each image's stages in
sequence. When done, print a summary table:
image | status (done / updated / skipped) | PDF path | QA result | translator note flags.
