"""Screenshots and print-to-PDF of both pages, for looking at - not a test.

Serves the repository root on http://localhost:8000 (or the port given),
then captures index.html and methodology.html:

  * full-page PNGs at 380px, 768px and 1280px, in the light and dark
    colour schemes, with JavaScript on;
  * the same at 1280px with JavaScript OFF, so every section's static
    fallback can be checked by eye (never "Loading...");
  * print-to-PDF at A4 and Letter.

Output goes under qa/<label>/ (gitignored). Needs Playwright with Chromium:
    pip install playwright && playwright install chromium

Run:  python -m pipeline.tests.screenshots [--label stage1] [--port 8000]
"""
import argparse
import http.server
import socketserver
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAGES = ("index.html", "methodology.html")
WIDTHS = (380, 768, 1280)
SCHEMES = ("light", "dark")


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, *args):  # noqa: D102
        pass


def serve(port: int):
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", port), _Quiet)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def capture(out: Path, port: int) -> list[Path]:
    from playwright.sync_api import sync_playwright

    base = f"http://localhost:{port}"
    written: list[Path] = []
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for page_name in PAGES:
            stem = page_name.removesuffix(".html")
            for scheme in SCHEMES:
                for width in WIDTHS:
                    ctx = browser.new_context(
                        viewport={"width": width, "height": 900},
                        color_scheme=scheme,
                        device_scale_factor=2,
                    )
                    pg = ctx.new_page()
                    pg.goto(f"{base}/{page_name}", wait_until="networkidle")
                    pg.wait_for_timeout(300)
                    path = out / f"{stem}-{width}-{scheme}.png"
                    pg.screenshot(path=str(path), full_page=True)
                    written.append(path)
                    ctx.close()
            # JavaScript off: the static fallbacks, as a reader without
            # scripting (or a crawler) sees them.
            ctx = browser.new_context(
                viewport={"width": 1280, "height": 900}, java_script_enabled=False,
                color_scheme="light", device_scale_factor=2,
            )
            pg = ctx.new_page()
            pg.goto(f"{base}/{page_name}", wait_until="networkidle")
            path = out / f"{stem}-1280-light-nojs.png"
            pg.screenshot(path=str(path), full_page=True)
            written.append(path)
            ctx.close()
            # Print to PDF, both paper sizes. Chromium's PDF printing applies
            # the page's @media print rules and fires beforeprint.
            ctx = browser.new_context(viewport={"width": 1280, "height": 900})
            pg = ctx.new_page()
            pg.goto(f"{base}/{page_name}", wait_until="networkidle")
            pg.emulate_media(media="print")
            for paper in ("A4", "Letter"):
                path = out / f"{stem}-{paper}.pdf"
                pg.pdf(path=str(path), format=paper, print_background=True,
                       margin={"top": "18mm", "bottom": "18mm", "left": "16mm", "right": "16mm"})
                written.append(path)
            ctx.close()
        browser.close()
    return written


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--label", default="latest", help="subdirectory under qa/")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    httpd = serve(args.port)
    try:
        written = capture(ROOT / "qa" / args.label, args.port)
    finally:
        httpd.shutdown()
    for path in written:
        print(f"  {path.relative_to(ROOT)}  ({path.stat().st_size // 1024} KB)")
    print(f"{len(written)} files under qa/{args.label}/")


if __name__ == "__main__":
    main()
