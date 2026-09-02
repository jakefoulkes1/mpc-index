"""Link check for every published surface.

Offline (pytest): every internal anchor on index.html, methodology.html and
README.md resolves to an element id or heading on the page it points at, and
every relative file link points at a file that exists in the repository.

Manual (network): the external URLs - the GitHub tag and commit pages, the
Bank of England source documents, the methodology page's cited news
releases - are listed and checked with their status codes when run as

    python -m pipeline.tests.test_links --external

which pytest never does: the suite makes no live network calls. Record the
output in DECISIONS.md when a pass depends on it (2026-09-02).
"""
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SURFACES = ("index.html", "methodology.html", "README.md")


def _strip_scripts(raw: str) -> str:
    raw = re.sub(r"<script\b.*?</script>", " ", raw, flags=re.S)
    return re.sub(r"<style\b.*?</style>", " ", raw, flags=re.S)


def hrefs(surface: str) -> list[str]:
    raw = (ROOT / surface).read_text()
    if surface.endswith(".md"):
        found = re.findall(r"\]\(([^)\s]+)\)", raw) + re.findall(r"<(https?://[^>]+)>", raw)
    else:
        found = re.findall(r'href="([^"]+)"', _strip_scripts(raw))
        found += re.findall(r'content="(https?://[^"]+)"', raw)
    return [h for h in found if not h.startswith(("data:", "mailto:"))]


def github_slug(heading: str) -> str:
    """GitHub's heading-anchor rule: lowercase, drop punctuation, spaces to hyphens."""
    s = re.sub(r"[`*_]", "", heading).strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    return re.sub(r"\s", "-", s)


def anchors(target: str) -> set[str]:
    raw = (ROOT / target).read_text()
    if target.endswith(".md"):
        return {github_slug(h) for h in re.findall(r"^#{1,6}\s+(.*)$", raw, flags=re.M)}
    return set(re.findall(r'\sid="([^"$]+)"', raw))


def split(href: str) -> tuple[str, str | None]:
    path, _, frag = href.partition("#")
    return path, (frag or None)


@pytest.mark.parametrize("surface", SURFACES)
def test_internal_anchors_resolve(surface):
    for href in hrefs(surface):
        if href.startswith(("http://", "https://")):
            continue
        path, frag = split(href)
        target = surface if not path else path
        assert (ROOT / target).exists(), f"{surface} links to {href!r} but {target} does not exist"
        if frag:
            assert frag in anchors(target), (
                f"{surface} links to {href!r} but {target} has no anchor {frag!r}"
            )


@pytest.mark.parametrize("surface", SURFACES)
def test_relative_file_links_exist(surface):
    for href in hrefs(surface):
        if href.startswith(("http://", "https://", "#")):
            continue
        path, _ = split(href)
        assert (ROOT / path).exists(), f"{surface} links to {href!r} but {path} is not in the repository"


def external_urls() -> list[str]:
    seen: list[str] = []
    for surface in SURFACES:
        for href in hrefs(surface):
            if href.startswith(("http://", "https://")) and href not in seen:
                seen.append(href)
    return seen


def test_the_tag_and_source_document_are_linked():
    """The two links a sceptical reader needs most: the lock tag and the Bank's
    own copy of the latest minutes."""
    import json

    from pipeline.site_figures import AUTHOR, prediction_file

    tag = Path(prediction_file()).stem
    urls = external_urls()
    assert f"{AUTHOR['repo']}/releases/tag/{tag}" in urls
    latest = json.loads((ROOT / "data/index.json").read_text())["documents"][-1]["source_url"]
    assert latest in urls


def check_external() -> int:
    """Fetch every external URL and print its status. Network; manual only.

    Uses requests (already a project dependency) rather than urllib, because
    the macOS system Python ships without a CA bundle and fails every HTTPS
    verification; requests carries certifi.
    """
    import requests

    worst = 0
    for url in external_urls():
        try:
            code = requests.get(url, headers={"User-Agent": "mpc-index link check"}, timeout=20).status_code
        except Exception as e:  # noqa: BLE001 - report, don't raise
            code = f"error: {e}"
        print(f"{code}\t{url}")
        if not isinstance(code, int) or code >= 400:
            worst = 1
    return worst


if __name__ == "__main__":
    if "--external" in sys.argv:
        sys.exit(check_external())
    print("\n".join(external_urls()))
