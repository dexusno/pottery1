#!/usr/bin/env python3
"""
render_pdf.py - Render a self-contained HTML file to PDF (and optional PNG).

Usage:
    python render_pdf.py <input_html> <output_pdf> [--png <output_png>]

Uses headless Chromium via Playwright, which gives faithful CSS/SVG output
and works cleanly on Windows. The HTML should set its own @page size
(A4 portrait by default in the templates). A PNG can also be emitted so the
QA agent can visually diff the rebuild against the original image.

ENFORCES SINGLE PAGE: every deliverable must be exactly one A4 page. If the
rendered PDF has more than one page, this FAILS LOUDLY (deletes the bad PDF and
exits non-zero) so a spilled/overflowing layout can never silently ship. Pass
--allow-multipage to override (rare; not for handouts).
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright


def pdf_page_count(pdf_path):
    """Count pages in a PDF. Tries pypdf; falls back to counting /Type /Page."""
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        import re
        data = Path(pdf_path).read_bytes()
        n = len(re.findall(rb"/Type\s*/Page[^s]", data))
        return n if n else 1


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print("usage: python render_pdf.py <input_html> <output_pdf> [--png <output_png>]")
        sys.exit(2)

    in_html = Path(args[0]).resolve()
    out_pdf = Path(args[1]).resolve()
    out_png = None
    if "--png" in args:
        out_png = Path(args[args.index("--png") + 1]).resolve()
    allow_multipage = "--allow-multipage" in args

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    if out_png:
        out_png.parent.mkdir(parents=True, exist_ok=True)

    url = in_html.as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 794, "height": 1123},  # A4 at 96dpi
            device_scale_factor=2,                      # crisp PNG for layout QC
        )
        page = context.new_page()
        page.goto(url, wait_until="networkidle")
        # Don't trust networkidle alone: wait until web fonts are APPLIED and every
        # image is fully decoded, or the PDF can render in fallback fonts / without
        # figures. This is the difference between "usually fine" and "always right".
        page.evaluate("document.fonts.ready")
        page.evaluate(
            """async () => {
                const imgs = Array.from(document.images);
                await Promise.all(imgs.map(img => img.complete
                    ? (img.decode ? img.decode().catch(() => {}) : Promise.resolve())
                    : new Promise(res => { img.onload = img.onerror = res; })));
            }"""
        )
        page.pdf(
            path=str(out_pdf),
            print_background=True,
            prefer_css_page_size=True,  # the page's own @page rule is authoritative
            format="A4",                # fallback only if the HTML omits @page
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        # Measure how far real content extends vs one A4 page, in the same CSS px
        # the layout uses. Sub-pixel rounding can nudge a visually-full page just
        # past the boundary; we only fail when content genuinely spills.
        overflow = page.evaluate(
            """() => {
                const doc = document.documentElement;
                const pageH = 1123;            // A4 height at 96dpi (matches viewport)
                const contentH = Math.max(doc.scrollHeight, document.body.scrollHeight);
                return { contentH, pageH, pages: Math.ceil(contentH / pageH),
                         overBy: contentH - pageH };
            }"""
        )
        if out_png:
            page.screenshot(path=str(out_png), full_page=True)
        browser.close()

    # Enforce single-page output (the bug class where one stray block spills onto
    # page 2). Allow a small tolerance so sub-pixel rounding doesn't false-fail a
    # visually-full page; fail when content overflows by more than ~8mm (~30px).
    n_pages = pdf_page_count(out_pdf)
    spills = overflow["overBy"] > 30
    if n_pages > 1 and spills and not allow_multipage:
        try:
            out_pdf.unlink()
        except OSError:
            pass
        print(f"RENDER FAILED: content overflows onto {n_pages} pages "
              f"(content is {overflow['contentH']}px vs one A4 page "
              f"{overflow['pageH']}px, over by {overflow['overBy']}px). Must be ONE "
              f"A4 page — shrink figures/type (page.css --fig-*/--fs-*) or reduce "
              f"content to fit, then re-render. (--allow-multipage to override.)")
        sys.exit(1)
    note = "1 page" if not spills else f"{n_pages} pages (allowed)"
    print(f"pdf  -> {out_pdf}  ({note})")
    if out_png:
        print(f"png  -> {out_png}")


if __name__ == "__main__":
    main()
