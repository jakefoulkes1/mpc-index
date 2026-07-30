"""Contract test: the figures hard-coded into the static HTML must still
match the JSON they were generated from.

index.html ships with the current ladder table and the locked call's key
figures built into the markup, so a reader whose fetch fails - or who has
JavaScript off entirely - sees real numbers instead of "Loading...". That
fallback is a copy, and copies rot. This test regenerates every fallback
string from the JSON, using the same formatting rules index.html's own JS
uses, and asserts each one appears inside the fallback markers.

If this fails, the fix is to regenerate the fallback markup from the JSON -
never to retype a figure by hand. See DECISIONS.md, 2026-07-30.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
INDEX_HTML = ROOT / "index.html"
METHODOLOGY_HTML = ROOT / "methodology.html"
LADDER = ROOT / "data" / "ladder_v1.json"
LOCK = ROOT / "data" / "predictions" / "lock-2026-07.json"
BUILD_INFO = ROOT / "data" / "build_info.json"

LADDER_MODELS = ("L0", "L1", "L2", "L3", "L4")


def region(html: str, name: str) -> str:
    """The markup between <!-- fallback:NAME --> and <!-- /fallback:NAME -->."""
    match = re.search(
        rf"<!--\s*fallback:{name}\b.*?-->(.*?)<!--\s*/fallback:{name}\s*-->",
        html,
        re.S,
    )
    assert match, f"index.html has no <!-- fallback:{name} --> region"
    return match.group(1)


def gb_date(iso: str) -> str:
    """The site's fmtDate: en-GB day, full month, year."""
    d = datetime.fromisoformat(iso[:10])
    return f"{d.day} {d.strftime('%B')} {d.year}"


@pytest.fixture(scope="module")
def index_html() -> str:
    return INDEX_HTML.read_text()


# ---------------------------------------------------------------- ladder


def test_ladder_fallback_rows_match_json(index_html):
    """Every cell of the built-in ladder table matches data/ladder_v1.json."""
    ladder = json.loads(LADDER.read_text())
    scores = ladder["headline_scores_scheduled_only"]
    block = region(index_html, "ladder")

    for model in LADDER_MODELS:
        s = scores[model]
        skill = "&mdash;" if s.get("skill_vs_l1") is None else f"{s['skill_vs_l1']:.4f}"
        expected = (
            f"<td>{model}</td><td>{s['mean_brier']}</td>"
            f"<td>{s['mean_log_score']}</td><td>{skill}</td><td>{s['n']}</td>"
        )
        assert expected in block, (
            f"index.html's built-in ladder row for {model} no longer matches "
            f"data/ladder_v1.json; expected {expected!r}"
        )


def test_ladder_fallback_schema_and_meta_match_json(index_html):
    """The schema tag and the n / specials / clip line are the JSON's own."""
    ladder = json.loads(LADDER.read_text())

    assert f'id="ladder-schema">({ladder["schema"]})<' in index_html

    meta = re.search(r'id="ladder-meta"[^>]*>(.*?)</p>', index_html, re.S)
    assert meta, "index.html has no #ladder-meta paragraph"
    text = meta.group(1)
    assert gb_date(ladder["eval_start"]) in text
    assert f"n={ladder['n_scheduled']}" in text
    assert f"{ladder['n_specials']} special meeting(s)" in text
    assert str(ladder["log_score_probability_clip"]) in text


# ------------------------------------------------------------- call card


def test_call_card_fallback_figures_match_lock_file(index_html):
    """Announcement, timestamp, probabilities and index readings are the
    locked file's own values, formatted the way the JS formats them."""
    lock = json.loads(LOCK.read_text())
    block = region(index_html, "call")
    m0 = lock["m0_market_only"]

    assert gb_date(lock["meeting_announcement"]) in block

    iso = lock["lock_timestamp"]
    assert f'datetime="{iso}"' in block, "the built-in lock timestamp is not the locked file's"
    # JS renders new Date(iso).toUTCString().
    utc = datetime.fromisoformat(iso).astimezone(timezone.utc)
    assert utc.strftime("%a, %d %b %Y %H:%M:%S GMT") in block

    for label in ("cut", "hold", "hike"):
        value = m0[f"p_{label}"]
        assert f'<span class="n">{value * 100:.0f}%</span><span class="l">{label}</span>' in block, (
            f"the built-in p_{label} no longer matches the locked file"
        )
        assert f'<span class="seg-{label}" style="width:{value * 100:.1f}%">' in block

    assert f"{m0['assumed_move_bp']}bp two-state assumption" in block
    assert lock["index_current_doc_id"] in block
    assert f"<strong>{lock['index_current']:.3f}</strong>" in block
    assert f"<strong>{lock['index_trailing_mean']:.3f}</strong>" in block
    assert f"{lock['index_trailing_n']}-document mean" in block


def test_call_card_fallback_point_call_and_rationale_match_lock_file(index_html):
    """The call itself and Jake's rationale are reproduced verbatim - this is
    the one piece of hand-written prose on the page, and a fallback that
    quietly paraphrased it would be worse than no fallback at all."""
    lock = json.loads(LOCK.read_text())
    block = region(index_html, "call")

    assert f'<span class="pt-call">{lock["point_call"]}</span>' in block

    body = re.search(r'id="call-rationale-body"[^>]*>(.*?)</p>', block, re.S)
    assert body, "the built-in call card has no rationale paragraph"
    # Only the house-style entities differ from the JSON's own characters.
    rendered = (
        body.group(1)
        .replace("&mdash;", "—")
        .replace("&minus;", "−")
        .replace("&amp;", "&")
        .strip()
    )
    assert rendered == lock["rationale"].strip(), (
        "the built-in rationale is not character-for-character the locked file's"
    )


def test_call_card_fallback_links_to_the_tag(index_html):
    """The verification path points at the tag named by the prediction file."""
    block = region(index_html, "call")
    tag = LOCK.stem  # lock-2026-07
    assert f"https://github.com/jakefoulkes1/mpc-index/releases/tag/{tag}" in block
    assert f"git show {tag}:data/predictions/{LOCK.name}" in block


# ------------------------------------------------------------ build info


@pytest.mark.parametrize("path", [INDEX_HTML, METHODOLOGY_HTML])
def test_build_info_fallback_matches_json(path):
    """Both footers' static "last updated" stamps match data/build_info.json.

    methodology.html runs no JavaScript, so its stamp is only ever as fresh
    as the last run of pipeline/build_build_info.py - which is exactly why
    it is asserted here rather than trusted.
    """
    info = json.loads(BUILD_INFO.read_text())
    block = region(path.read_text(), "buildinfo")
    assert gb_date(info["last_commit_iso"]) in block, (
        f"{path.name}'s built-in last-updated date is not data/build_info.json's; "
        f"re-run python -m pipeline.build_build_info and update the footer"
    )
    assert info["last_commit_short_sha"] in block
    assert info["last_commit_sha"][:7] in block


# --------------------------------------------------------- no dead states


def test_no_section_can_sit_on_loading_without_a_timeout(index_html):
    """Every fetch goes through fetchJSON, which is time-boxed, and every
    failure path calls failSection. Guards the P0 promise that no section
    sits on "Loading..." for ever."""
    assert "const FETCH_TIMEOUT_MS = 8000;" in index_html
    assert "new AbortController()" in index_html
    # No bare fetch( calls left outside the helper. The helper's own call is
    # the single exception, identified by the abort signal it passes.
    bare = [
        line.strip()
        for line in index_html.split("\n")
        if re.search(r"(?<![A-Za-z])fetch\(", line)
        and "fetchJSON" not in line
        and "signal: ctrl.signal" not in line
    ]
    assert not bare, f"these fetches bypass the timeout helper: {bare}"

    # Every status element the JS writes into has a failure path.
    for status_id in (
        "call-status", "status", "chart-status", "context-status",
        "ladder-status", "inference-status", "track-status", "episodes-status",
    ):
        assert f"failSection('{status_id}'" in index_html, (
            f"#{status_id} has no failure state"
        )
