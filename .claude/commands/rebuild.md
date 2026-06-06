---
description: Rebuild course images into translated Norwegian PDFs. No args = all pending; names = just those (forced); "all" = full refresh.
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

For each selected image, in order, following CLAUDE.md:
1. Delegate to the extractor subagent → work\<stem>\extract.json.
2. Run: python scripts\crop.py <image> work\<stem>\crops work\<stem>\extract.json
3. Delegate to the illustrator subagent → redraws every crop → _v2.png candidates
   (uses style\anchor.png if present; if no OPENAI_API_KEY, it reports and the
   layout-builder uses the original crops).
4. Delegate to the translator subagent → work\<stem>\translated.json.
5. Delegate to the layout-builder subagent → output\<stem>.pdf + page.png.
6. Delegate to the layout-qc subagent (visual/typography) → work\<stem>\qa_layout.md.
   If RESULT: FAIL, have the layout-builder apply the punch-list and re-render;
   repeat until PASS (max 3 iterations).
7. Delegate to the qa-reviewer subagent (content vs original) → work\<stem>\qa.md.
8. If qa-reviewer FAILs, apply fixes and redo from the failed step (max 2 retries).
   If it rejected a reimagined figure, rebuild that figure with the original crop.

Independent images may be processed in parallel, but keep each image's stages in
sequence. When done, print a summary table:
image | status (done / updated / skipped) | PDF path | QA result | translator note flags.
