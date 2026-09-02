"""Parity test: the built-in (no-JavaScript) text of every section must
agree with what the JavaScript renders from the same data.

Every JS-rendered section of index.html ships with a static fallback
generated from the same JSON by pipeline/build_fallbacks.py. The two are
written by different languages with different formatting habits, and they
have disagreed before: on 2026-08-30 the built-in call card read "25.0bp"
where the script rendered "25bp". This test renders the page both ways in a
real browser and diffs the text of every figure-bearing element.

The browser's time zone is deliberately set west of Greenwich: a bare ISO
date parsed as UTC midnight is the previous evening in California, which is
how a date-only string can render a day early - the fmtDate() fix of
2026-09-02.

Needs Playwright with Chromium (pip install playwright; playwright install
chromium). Skips cleanly when either is absent - CI does not install a
browser, so this is a local guard; run it before every publish. Serves the
repository from an ephemeral localhost port; no live network calls.

See DECISIONS.md, 2026-09-02.
"""
import http.server
import re
import socketserver
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

# Every element whose text the JavaScript rewrites from a data file.
IDS = [
    "call-card", "content", "ladder-tbody", "ladder-meta", "ladder-schema",
    "spec3-line", "track-tbody", "ois-h", "ois-sub", "ois-rows",
    "rate-latest", "rate-asof", "gilt-h", "gilt-latest", "gilt-asof",
    "context-note", "episodes-list", "build-note", "gen-note", "build-stamp",
]
STATUS_IDS = [
    "call-status", "status", "chart-status", "context-status",
    "ladder-status", "inference-status", "track-status", "episodes-status",
]


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, *args):  # noqa: D102 - silence the request log
        pass


@pytest.fixture(scope="module")
def site_url():
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", 0), _Quiet)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()


def normalise(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace(" ", " ")).strip()


def capture(browser, url: str, js: bool) -> dict[str, str]:
    ctx = browser.new_context(
        java_script_enabled=js,
        timezone_id="America/Los_Angeles",
        viewport={"width": 1100, "height": 900},
    )
    page = ctx.new_page()
    page.goto(f"{url}/index.html", wait_until="networkidle")
    if js:
        page.wait_for_function(
            "ids => ids.every(id => { const el = document.getElementById(id); "
            "return el && el.style.display === 'none'; })",
            arg=STATUS_IDS,
            timeout=15000,
        )
    # Closed <details> hide their content from innerText; open them so the
    # comparison covers the context panel and the expanders.
    page.evaluate("() => document.querySelectorAll('details').forEach(d => d.open = true)")
    out = {}
    for id_ in IDS:
        out[id_] = page.eval_on_selector(f"#{id_}", "el => el.innerText")
    ctx.close()
    return out


def test_static_fallbacks_and_javascript_render_the_same_text(site_url):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("playwright not installed (pip install playwright; playwright install chromium)")

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception as e:  # noqa: BLE001 - a missing browser is a skip, not a failure
            pytest.skip(f"chromium not available: {e}")
        try:
            static = capture(browser, site_url, js=False)
            scripted = capture(browser, site_url, js=True)
        finally:
            browser.close()

    diffs = {
        id_: (normalise(static[id_]), normalise(scripted[id_]))
        for id_ in IDS
        if normalise(static[id_]) != normalise(scripted[id_])
    }
    assert not diffs, "static fallback and JavaScript disagree:\n" + "\n".join(
        f"#{k}\n  static:   {a[:300]!r}\n  scripted: {b[:300]!r}" for k, (a, b) in diffs.items()
    )
