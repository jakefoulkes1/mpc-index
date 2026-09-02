"""No process commentary may reach a published surface.

Between 2 September 2026's stage two and its close-out, the pages carried
HTML comments recording that some prose had been written under a bypassed
approval gate and was awaiting review. That is a note between the author and
the assistant, not something a reader of a working paper should find in the
source. The record of it belongs in DECISIONS.md, which is where it stayed.

This guard fails if the process vocabulary comes back on any surface a reader
can fetch - both pages, the README, the published episodes and their source
markdown - in markup or in comments. It also covers the stylesheet and the
theme script, which ship to the reader too.

Draft markers are guarded separately by test_no_draft_markers.py.

See DECISIONS.md, 2026-09-02 (close-out).
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SURFACES = [
    ROOT / "index.html",
    ROOT / "methodology.html",
    ROOT / "README.md",
    ROOT / "site" / "site.css",
    ROOT / "site" / "theme.js",
    ROOT / "data" / "annotations.json",
    *sorted((ROOT / "site" / "annotations").glob("*.md")),
]
# Lower-cased, so "Approval gate" and "Post-hoc" are caught too.
FORBIDDEN = ("approval gate", "bypass", "post-hoc", "awaiting review", "[verify]")


@pytest.mark.parametrize("path", SURFACES, ids=lambda p: str(p.relative_to(ROOT)))
def test_no_process_commentary_on_any_published_surface(path):
    text = path.read_text().lower()
    found = [phrase for phrase in FORBIDDEN if phrase in text]
    assert not found, (
        f"{path.relative_to(ROOT)} carries process commentary {found} - it belongs in "
        f"DECISIONS.md, not on a page a reader fetches"
    )
