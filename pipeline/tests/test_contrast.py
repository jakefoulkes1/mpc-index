"""Accessibility floor for the colour tokens, verified rather than assumed.

Reads the light and dark token sets out of site/site.css and checks every
text-on-ground pair used by the pages against WCAG 2.1: at least 4.5:1 for
body-size text and 3:1 for large text and graphical marks. The pairs are
listed here by hand against the stylesheet, which is the point: a token
changed in the CSS is re-checked on the next run.

Run as a script for the full table, plus the hawk/dove and rate/gilt pairs
under simulated protanopia and deuteranopia (Machado, Oliveira and
Fernandes 2009, severity 1.0), which is how "check every pair under
colour-blindness simulation" was done for DECISIONS.md 2026-09-02:

    python -m pipeline.tests.test_contrast
"""
import re
from pathlib import Path

import pytest

CSS = Path(__file__).resolve().parents[2] / "site" / "site.css"

# (foreground token, background token, minimum ratio, what it is)
PAIRS = [
    ("--ink", "--paper", 4.5, "body text"),
    ("--ink-2", "--paper", 4.5, "secondary text: captions, fine print, axis labels"),
    ("--accent", "--paper", 4.5, "the Locked badge in the track record; the lock marker's legend"),
    ("--ink", "--stamp", 4.5, "call card text"),
    ("--ink-2", "--stamp", 4.5, "call card secondary text"),
    ("--accent", "--stamp", 4.5, "call card badge, point call, lead probability (display size)"),
    ("--hawk", "--paper", 4.5, "hawkish reading, hike legend"),
    ("--dove", "--paper", 4.5, "dovish reading, cut legend"),
    ("--rate", "--paper", 3.0, "Bank Rate axis labels (small, graphical)"),
    ("--gilt", "--paper", 3.0, "gilt sparkline"),
    ("--paper", "--hawk", 3.0, "labels inside the hike segment of the OIS bar"),
    ("--paper", "--dove", 3.0, "labels inside the cut segment of the OIS bar"),
    ("--ink", "--rule", 3.0, "labels inside the hold segment of the OIS bar"),
]


def tokens(css: str) -> dict[str, dict[str, str]]:
    """The light set from `:root {`, the dark set from `:root[data-theme="dark"] {`."""
    def block(selector: str) -> str:
        m = re.search(re.escape(selector) + r"\s*\{(.*?)\}", css, re.S)
        assert m, f"site.css has no {selector} block"
        return m.group(1)

    def parse(body: str) -> dict[str, str]:
        return dict(re.findall(r"(--[a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{6})", body))

    light = parse(block(":root"))
    dark = {**light, **parse(block(':root[data-theme="dark"]'))}
    return {"light": light, "dark": dark}


def srgb_to_linear(c: float) -> float:
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgb(hexcode: str) -> tuple[float, float, float]:
    h = hexcode.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def luminance(hexcode: str) -> float:
    r, g, b = (srgb_to_linear(c) for c in rgb(hexcode))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg: str, bg: str) -> float:
    l1, l2 = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_every_token_pair_clears_its_wcag_floor(theme):
    t = tokens(CSS.read_text())[theme]
    failures = []
    for fg, bg, floor, what in PAIRS:
        ratio = contrast(t[fg], t[bg])
        if ratio < floor:
            failures.append(f"{theme}: {fg} on {bg} = {ratio:.2f}:1 < {floor}:1 ({what})")
    assert not failures, "\n".join(failures)


def test_both_themes_define_the_same_tokens():
    t = tokens(CSS.read_text())
    assert set(t["light"]) == set(t["dark"])
    for name in ("--paper", "--stamp", "--ink", "--ink-2", "--rule", "--accent", "--hawk", "--dove", "--rate", "--gilt"):
        assert name in t["light"], f"{name} missing from :root"


# ---- colour-vision simulation, for the report --------------------------

MACHADO = {
    "protanopia": [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
    "deuteranopia": [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]],
}


def simulate(hexcode: str, kind: str) -> str:
    lin = [srgb_to_linear(c) for c in rgb(hexcode)]
    m = MACHADO[kind]
    out = [sum(m[i][j] * lin[j] for j in range(3)) for i in range(3)]

    def to_srgb(v: float) -> int:
        v = min(1.0, max(0.0, v))
        v = v * 12.92 if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
        return round(v * 255)

    return "#%02x%02x%02x" % tuple(to_srgb(v) for v in out)


def report() -> None:
    t = tokens(CSS.read_text())
    for theme in ("light", "dark"):
        print(f"\n{theme}")
        for fg, bg, floor, what in PAIRS:
            ratio = contrast(t[theme][fg], t[theme][bg])
            print(f"  {ratio:5.2f}:1  (floor {floor})  {fg} on {bg}  - {what}")
        for a, b in (("--hawk", "--dove"), ("--rate", "--gilt"), ("--hawk", "--ink"), ("--dove", "--ink")):
            print(f"  pair {a} / {b}: normal {contrast(t[theme][a], t[theme][b]):.2f}:1", end="")
            for kind in ("protanopia", "deuteranopia"):
                sa, sb = simulate(t[theme][a], kind), simulate(t[theme][b], kind)
                print(f"; {kind} {sa}/{sb} {contrast(sa, sb):.2f}:1", end="")
            print()


if __name__ == "__main__":
    report()
