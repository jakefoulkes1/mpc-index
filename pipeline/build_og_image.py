"""Builds og-image.png: the 1200x630 share card both pages point at.

Site layer, additive: reads data/index.json and the newest lock-* file
read-only, writes one png at the repo root, touches no existing schema and
nothing under data/predictions/.

The picture is the real series - the same A&BG net index the site charts -
drawn straight from data/index.json, so a share card can never show a shape
the page does not. Nothing is smoothed, resampled or invented; if the file
is missing a field the script raises rather than drawing something plausible.

Drawn in the site's paper theme (tokens as in site/site.css, light) with the
site's own typeface: the self-hosted Source Serif 4 woff2 files are decoded
with fontTools for Pillow, so the card and the page match on any machine that
has the repository. If fontTools is unavailable the script falls back to a
system serif and says so; that is cosmetic, not a data problem.

Run:  python -m pipeline.build_og_image
"""
import io
import json
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from pipeline.site_figures import AUTHOR, prediction_file

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "data" / "index.json"
FONT_DIR = ROOT / "site" / "fonts"
OUT = ROOT / "og-image.png"

W, H = 1200, 630

# Same tokens as site/site.css (light), so the card and the page match.
PAPER = (252, 251, 249)
STAMP = (245, 240, 230)
INK = (28, 27, 25)
INK_2 = (87, 83, 77)
RULE = (216, 211, 203)
ACCENT = (138, 90, 18)

FALLBACK_SERIF = [
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/Library/Fonts/Georgia.ttf",
]


def _woff2_bytes(name: str) -> bytes | None:
    """Decode a woff2 from site/fonts into TTF bytes Pillow can read."""
    path = FONT_DIR / name
    if not path.exists():
        return None
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        return None
    font = TTFont(str(path))
    font.flavor = None
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()


def load_font(name: str, size: int):
    data = _woff2_bytes(name)
    if data is not None:
        return ImageFont.truetype(io.BytesIO(data), size)
    for path in FALLBACK_SERIF:
        if Path(path).exists():
            print(f"  note: {name} not decodable here; using {Path(path).name}")
            return ImageFont.truetype(path, size)
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
    lock = json.loads((ROOT / prediction_file()).read_text())

    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    f_title = load_font("SourceSerif4Display-Regular.woff2", 62)
    f_lede = load_font("SourceSerif4-It.woff2", 27)
    f_label = load_font("SourceSerif4-Regular.woff2", 20)
    f_small = load_font("SourceSerif4-Regular.woff2", 17)

    pad = 64

    d.text((pad, 58), "MPC Communication Index", font=f_title, fill=INK)
    d.text(
        (pad, 146),
        "Does Bank of England tone predict the next rate move?",
        font=f_lede,
        fill=INK_2,
    )
    d.line([(pad, 200), (W - pad, 200)], fill=RULE, width=1)

    # ---- the series ----
    plot_top, plot_bottom = 236, H - 132
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

    # Neutral reference line, labelled in the left margin.
    y_neutral = y_of(neutral)
    neutral_label = f"neutral ({neutral:.1f})"
    d.text(
        (plot_left - 14 - d.textlength(neutral_label, font=f_small), y_neutral - 9),
        neutral_label,
        font=f_small,
        fill=INK_2,
    )
    for x in range(plot_left, plot_right, 12):
        d.line([(x, y_neutral), (x + 6, y_neutral)], fill=RULE, width=2)

    points = [(x_of(doc["published"]), y_of(float(doc["abg_net_index"]))) for doc in docs]
    d.line(points, fill=INK, width=2, joint="curve")

    # The one accent mark: the locked call's meeting, a diamond.
    locked = next((doc for doc in docs if doc["published"] == lock["meeting_announcement"]), None)
    if locked is not None:
        cx, cy = x_of(locked["published"]), y_of(float(locked["abg_net_index"]))
        d.polygon([(cx, cy - 9), (cx + 8, cy), (cx, cy + 9), (cx - 8, cy)], fill=ACCENT, outline=PAPER)

    d.text((plot_left, plot_bottom + 14), docs[0]["published"][:7], font=f_small, fill=INK_2)
    end = docs[-1]["published"][:7]
    d.text(
        (plot_right - d.textlength(end, font=f_small), plot_bottom + 14),
        end,
        font=f_small,
        fill=INK_2,
    )

    # ---- footer strip ----
    d.line([(pad, H - 84), (W - pad, H - 84)], fill=RULE, width=1)
    d.text(
        (pad, H - 62),
        f"A&BG net index, {len(docs)} MPC documents. Calls locked before the announcement, scored after.",
        font=f_label,
        fill=INK_2,
    )
    byline = f"{AUTHOR['name']}, {AUTHOR['affiliation']}"
    d.text((pad, H - 34), byline, font=f_small, fill=INK_2)
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
