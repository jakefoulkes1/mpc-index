"""Exactly three fine-print blocks carry the body ink.

The `.fine` class is apparatus: captions, provenance, footnotes, all set in
`--ink-2`. Three blocks on index.html are not apparatus but argument, and
were being read as footnotes because they were the same colour as one:

  * why the five sample sizes differ, which a reader meets before any of them
    is explained;
  * that the skill differential has not been tested against zero;
  * that no standard errors are published.

`.fine.substantive` gives those three the body ink at the fine size. This
test pins the set: it fails if one loses the class, and it fails if a fourth
block gains it, because a modifier that spreads is a modifier that means
nothing. The size must stay the fine size - a block that wanted the body
size would not be fine print.

These three are static markup rather than generated blocks (no generator
emits them: two were written in stage two, one in July), so the class is
applied in the page and enforced here.

See DECISIONS.md, 2026-09-02 (close-out).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# The opening words of each block, which is what identifies it to a reader.
EXPECTED = [
    "Why the sample sizes differ.",
    "Not yet tested: whether the skill differential is distinguishable from",
    "No standard errors are published.",
]


def blocks(html: str) -> list[str]:
    return re.findall(r'<p class="fine substantive"[^>]*>(.*?)</p>', html, re.S)


def test_exactly_the_three_intended_blocks_are_substantive():
    found = blocks((ROOT / "index.html").read_text())
    assert len(found) == len(EXPECTED), (
        f"{len(found)} blocks carry .fine.substantive, expected {len(EXPECTED)} - "
        f"the modifier marks argument, not apparatus"
    )
    for expected, body in zip(EXPECTED, found):
        assert expected in body, f"expected a block opening {expected!r}, found {body[:80]!r}"


def test_the_modifier_is_ink_at_the_fine_size():
    css = (ROOT / "site" / "site.css").read_text()
    rule = re.search(r"\.fine\.substantive\s*\{([^}]*)\}", css)
    assert rule, "site.css has no .fine.substantive rule"
    body = rule.group(1)
    assert "color: var(--ink)" in body, "the modifier must promote the colour to the body ink"
    assert "font-size" not in body, "the modifier changes colour only; the size stays fine"


def test_no_other_surface_uses_the_modifier():
    """methodology.html sets its limitations as body text already; a second
    place using the modifier would mean the two pages disagree about what
    fine print is."""
    assert "fine substantive" not in (ROOT / "methodology.html").read_text()
