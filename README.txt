SHEET2PDF — image sheets -> translated A4 PDFs (scaffold v30)
v30: model tiering. Edit two lines in CLAUDE.md:
  PREMIUM MODEL: opus     (extractor, layout-qc, qa-reviewer — the judgment work)
  WORKFLOW MODEL: sonnet  (illustrator, translator, layout-builder — the plumbing)
Aliases, full model IDs, or `inherit` (both inherit = no tiering). The orchestrator
passes the model explicitly on each delegation; verify in the trace on first run.
Restart Claude Code after updating.
