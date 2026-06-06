#!/usr/bin/env python3
"""
render_pdf.py - Render a self-contained HTML file to PDF (and optional PNG).

Usage:
    python render_pdf.py <input_html> <output_pdf> [--png <output_png>]

Uses headless Chromium via Playwright, which gives faithful CSS/SVG output
and works cleanly on Windows. The HTML should set its own @page size
(A4 portrait by default in the templates). A PNG can also be emitted so the
QA agent can visually diff the rebuild against the original image.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright


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
        page.pdf(
            path=str(out_pdf),
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        print(f"pdf  -> {out_pdf}")
        if out_png:
            page.screenshot(path=str(out_png), full_page=True)
            print(f"png  -> {out_png}")
        browser.close()


if __name__ == "__main__":
    main()
