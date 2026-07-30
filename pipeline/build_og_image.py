"""Builds og-image.png: the 1200x630 share card both pages point at.

Site layer, additive: reads data/index.json read-only, writes one NEW png at
the repo root, touches no existing schema and nothing under data/predictions/.

The picture is the real series - the same A&BG net index the site charts -
drawn straight from data/index.json, so a share card can never show a shape
the page does not. Nothing is smoothed, resampled or invented; if the file
is missing a field the script raises rather than drawing something plausible.

Run:  python -m pipeline.build_og_image
"""
import json
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "data" / "index.json"
OUT = ROOT / "og-image.png"

W, H = 1200, 630

# Same tokens as the site's stylesheet, so the card and the page match.
BG = (15, 17, 21)
PANEL_LINE = (42, 47, 58)
TEXT = (232, 230, 225)
MUTED = (154, 160, 171)
FAINT = (134, 141, 153)
ACCENT = (201, 163, 78)

# Serif first (the site's headline face), then a sans for the small print.
# Whichever of these exists on the build machine wins; if none do, Pillow's
# own scalable default is used. The card is decoration, so a font
# substitution is a cosmetic difference, not a data problem - but it is
# recorded here so a rebuild on another machine is not a surprise.
SERIF_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/Library/Fonts/Georgia.ttf",
]
SANS_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]


def load_font(candidates: list[str], size: int):
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default(size=size)


def load_series() -> tuple[list[dict], float]:
    """Published documents in date order, plus the neutral value.

    Raises on a missing field rather than skipping it: a share card built
    from a partially-parsed index would be a quiet misrepresentation.
    """
    data = json.loads(INDEX_PATH.read_text())
    if "neutral_value" not in data:
        raise KeyError("data/index.json has no neutral_value")
    docs = []
    for doc in data["documents"]:
        if not doc.get("published"):
            continue
        if "abg_net_index" not in doc:
            raise KeyError(f"{doc.get('doc_id', '?')} has no abg_net_index")
        docs.append(doc)
    docs.sort(key=lambda d: d["published"])
    if len(docs) < 2:
        raise ValueError("need at least 2 published documents to draw a series")
    return docs, float(data["neutral_value"])


def build() -> Image.Image:
    docs, neutral = load_series()

    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    f_title = load_font(SERIF_CANDIDATES, 64)
    f_lede = load_font(SERIF_CANDIDATES, 27)
    f_label = load_font(SANS_CANDIDATES, 19)
    f_small = load_font(SANS_CANDIDATES, 17)

    pad = 64

    # Accent rule at the top, matching the site's locked-call border.
    d.rectangle([0, 0, W, 6], fill=ACCENT)

    d.text((pad, 62), "MPC Communication Index", font=f_title, fill=TEXT)
    d.text(
        (pad, 148),
        "Does Bank of England tone predict the next rate move?",
        font=f_lede,
        fill=MUTED,
    )

    # ---- the series ----
    plot_top, plot_bottom = 236, H - 132
    # Left gutter reserved for the neutral label, so nothing overprints the
    # series - at share-card size an overlap reads as a rendering fault.
    gutter = 104
    plot_left, plot_right = pad + gutter, W - pad

    def to_ts(iso: str) -> int:
        y, m, dd = (int(p) for p in iso[:10].split("-"))
        return date(y, m, dd).toordinal()

    t0, t1 = to_ts(docs[0]["published"]), to_ts(docs[-1]["published"])
    values = [float(doc["abg_net_index"]) for doc in docs]
    v_lo, v_hi = min(values + [neutral]), max(values + [neutral])
    span = (v_hi - v_lo) or 1.0
    v_lo -= span * 0.12
    v_hi += span * 0.12

    def x_of(iso: str) -> float:
        return plot_left + (plot_right - plot_left) * ((to_ts(iso) - t0) / (t1 - t0))

    def y_of(v: float) -> float:
        return plot_bottom - (plot_bottom - plot_top) * ((v - v_lo) / (v_hi - v_lo))

    # Neutral reference line, labelled - the whole chart is read against it.
    # The label sits in the left margin and the dashes start clear of it, so
    # neither overprints the series.
    y_neutral = y_of(neutral)
    neutral_label = f"neutral ({neutral:g})"
    d.text(
        (plot_left - 14 - d.textlength(neutral_label, font=f_small), y_neutral - 9),
        neutral_label,
        font=f_small,
        fill=FAINT,
    )
    for x in range(plot_left, plot_right, 12):
        d.line([(x, y_neutral), (x + 6, y_neutral)], fill=PANEL_LINE, width=2)

    points = [(x_of(doc["published"]), y_of(float(doc["abg_net_index"]))) for doc in docs]
    d.line(points, fill=ACCENT, width=3, joint="curve")
    d.ellipse(
        [points[-1][0] - 7, points[-1][1] - 7, points[-1][0] + 7, points[-1][1] + 7],
        fill=ACCENT,
    )

    # End labels only: a share card is read at thumbnail size.
    d.text((plot_left, plot_bottom + 14), docs[0]["published"][:7], font=f_small, fill=FAINT)
    end = docs[-1]["published"][:7]
    d.text(
        (plot_right - d.textlength(end, font=f_small), plot_bottom + 14),
        end,
        font=f_small,
        fill=FAINT,
    )

    # ---- footer strip ----
    d.line([(pad, H - 84), (W - pad, H - 84)], fill=PANEL_LINE, width=1)
    d.text(
        (pad, H - 62),
        f"A&BG net index  ·  {len(docs)} MPC documents  ·  calls locked before "
        f"the announcement, scored after",
        font=f_label,
        fill=MUTED,
    )
    url = "jakefoulkes1.github.io/mpc-index"
    d.text(
        (W - pad - d.textlength(url, font=f_small), H - 34),
        url,
        font=f_small,
        fill=ACCENT,
    )
    return img


def main() -> None:
    img = build()
    img.save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB, {W}x{H})")


if __name__ == "__main__":
    main()
