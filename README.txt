SHEET2PDF — image sheets -> translated A4 PDFs (scaffold v36)
v36: the recurring 2-page bug is FIXED. render_pdf.py now enforces a single A4 page
(deletes the PDF and fails loudly on real overflow; --allow-multipage to override),
and layout-builder/layout-qc/qa-reviewer all enforce single-page too.
NEW DEPENDENCY: pip install pypdf --break-system-packages
Restart Claude Code after updating.
