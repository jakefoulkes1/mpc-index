"""No placeholder may reach a published surface.

The site carried "Draft — JF to revise" badges and <!-- DRAFT: JF to revise -->
comments through August 2026 by design: prose written by the assistant was
marked for the author. Stage 2 of the September pass replaced every one of
them. This test fails the suite if any marker comes back, on any surface a
reader can see: both pages, the README, the published episodes and their
source markdown.

The `.draft-note` CSS rule was the project's device for the badge; a
surface that uses the class is a surface with a draft on it.

See DECISIONS.md, 2026-09-02 (Stage 2).
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SURFACES = [
    ROOT / "index.html",
    ROOT / "methodology.html",
    ROOT / "README.md",
    ROOT / "data" / "annotations.json",
    *sorted((ROOT / "site" / "annotations").glob("*.md")),
]
MARKERS = ("JF to revise", "DRAFT", 'class="draft-note"', "TODO(Jake)")


@pytest.mark.parametrize("path", SURFACES, ids=lambda p: str(p.relative_to(ROOT)))
def test_no_draft_marker_on_any_published_surface(path):
    text = path.read_text()
    found = [m for m in MARKERS if m in text]
    assert not found, f"{path.relative_to(ROOT)} carries draft marker(s) {found}"
