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

from pipeline.site_context import UPCOMING_MEETINGS
from pipeline.site_figures import clip, score

ROOT = Path(__file__).resolve().parents[2]
INDEX_HTML = ROOT / "index.html"
METHODOLOGY_HTML = ROOT / "methodology.html"
LADDER = ROOT / "data" / "ladder_v1.json"
LOCK = ROOT / "data" / "predictions" / "lock-2026-07.json"
BUILD_INFO = ROOT / "data" / "build_info.json"
INFERENCE = ROOT / "data" / "inference_v1.json"
TRACK = ROOT / "data" / "track_record.json"
CONTEXT = ROOT / "data" / "site_context.json"

LADDER_MODELS = ("L0", "L1", "L2", "L3", "L4")
# Mirrors MODEL_GLOSS in pipeline/build_fallbacks.py: labels, not data.
MODEL_GLOSS = {
    "L0": "always-hold",
    "L1": "market pricing",
    "L2": "market modelled",
    "L3": "market + tone + skew",
    "L4": "member simulation",
}


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
        # Rounding policy: scores to 4 d.p., a true minus sign, never a hyphen.
        skill = "&mdash;" if s.get("skill_vs_l1") is None else score(s["skill_vs_l1"])
        expected = (
            f"<td><strong>{model}</strong>"
            f'<span class="model-gloss">{MODEL_GLOSS[model]}</span></td>'
            f"<td>{score(s['mean_brier'])}</td>"
            f"<td>{score(s['mean_log_score'])}</td><td>{skill}</td><td>{s['n']}</td>"
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
    assert f"evaluated from {gb_date(ladder['eval_start'])} onwards" in text
    assert f"n&nbsp;=&nbsp;{ladder['n_scheduled']}" in text
    assert f"{ladder['n_specials']} special meetings" in text
    assert clip(ladder["log_score_probability_clip"]) in text


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
    # JS renders fmtUTCStamp(iso): the site's date format, to the second, UTC.
    utc = datetime.fromisoformat(iso).astimezone(timezone.utc)
    expected = f"{utc.day} {utc.strftime('%B')} {utc.year}, {utc.strftime('%H:%M:%S')} UTC"
    assert expected in block, f"the built-in lock timestamp does not read {expected!r}"

    for label in ("cut", "hold", "hike"):
        value = m0[f"p_{label}"]
        assert f'<span class="n">{value * 100:.0f}%</span><span class="l">{label}</span>' in block, (
            f"the built-in p_{label} no longer matches the locked file"
        )
        assert f'<span class="seg-{label}" style="width:{value * 100:.1f}%">' in block

    assert f"{m0['assumed_move_bp']:g}bp two-state assumption" in block
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


def test_verify_box_links_to_the_tag(index_html):
    """The verification path - now consolidated into one box near the top of
    the page - points at the tag named by the prediction file, and offers the
    git command that reads the call as it stood when it was locked."""
    block = region(index_html, "verify")
    tag = LOCK.stem  # lock-2026-07
    assert f"https://github.com/jakefoulkes1/mpc-index/releases/tag/{tag}" in block
    assert f"git show {tag}:data/predictions/{LOCK.name}" in block
    assert "https://github.com/jakefoulkes1/mpc-index<" in block or \
        'href="https://github.com/jakefoulkes1/mpc-index"' in block, \
        "the verification box should also link the repository itself"


def test_call_card_still_cites_the_tag_and_says_what_its_figures_are_as_at(index_html):
    """The card keeps the tag as a citation, and says which vintage its own
    figures are: a locked file is never edited, so where the site has since
    recomputed a figure on a larger corpus the two legitimately differ."""
    lock = json.loads(LOCK.read_text())
    block = region(index_html, "call")
    tag = LOCK.stem
    assert f"releases/tag/{tag}" in block
    assert f"Figures as at the lock date ({gb_date(lock['lock_timestamp'])})." in block


# ---------------------------------------------------------------- spec 3


def test_spec3_fallback_matches_json(index_html):
    """The built-in Spec 3 line carries the JSON's own figures, rounded to the
    published precision: coefficients and t to 2 places, p to 4. The full
    precision is one link away, and the sentence says so."""
    from pipeline.site_figures import figures

    inf = json.loads(INFERENCE.read_text())
    f = figures()
    block = region(index_html, "spec3")

    full = inf["full_sample"]["spec3_surprise_on_lagged_index"]
    assert f"{full['newey_west_maxlags']} lags" in block
    assert f"n={full['n']}" in block
    assert f"<strong>{f['spec3_coef']}</strong>" in block
    assert f"t = {f['spec3_t']}" in block
    assert f"<strong>p = {f['spec3_p']}</strong>" in block
    assert gb_date(frag_start := inf["fragility_check_subsample"]["start_date"]) in block
    assert f"n={f['frag_n']}" in block
    assert f"coefficient {f['frag_coef']}" in block
    assert f"p = {f['frag_p']}" in block
    assert f"LR = {f['spec2_lr']}" in block
    assert f"p = {f['spec2_p']}" in block
    assert "data/inference_v1.json" in block, "the page must name the file holding full precision"


# ----------------------------------------------------------- track record


def test_track_record_fallback_matches_json(index_html):
    """Every locked row is reproduced from data/track_record.json."""
    track = json.loads(TRACK.read_text())
    block = region(index_html, "track")
    locked = [r for r in track["records"] if r["kind"] == "locked"]
    assert locked, "no locked record to build a fallback from"

    for r in locked:
        m0 = r["m0_market_only"]
        brier = "&mdash;" if r["brier_m0"] is None else score(r["brier_m0"])
        expected = (
            f'<td>{gb_date(r["meeting_announcement"])}</td>'
            f'<td><span class="track-badge locked">Locked</span></td>'
            f'<td>{r["point_call"] or "&mdash;"}</td>'
            f'<td>{m0["p_cut"] * 100:.0f}%</td>'
            f'<td>{m0["p_hold"] * 100:.0f}%</td>'
            f'<td>{m0["p_hike"] * 100:.0f}%</td>'
            f'<td>{r["outcome"] or "&mdash;"}</td><td>{brier}</td>'
        )
        assert expected in block, (
            f"the built-in track-record row for {r['filename']} no longer matches the JSON"
        )


def test_track_record_fallback_shows_locked_rows_only(index_html):
    """No rehearsal or dry run in the static table.

    The show-rehearsals toggle is JavaScript. With scripting off it cannot
    hide anything, so shipping those rows statically would contradict the
    default-off promise the toggle makes.
    """
    block = region(index_html, "track")
    for kind in ("dryrun", "rehearsal", "other"):
        assert f"kind-{kind}" not in block, f"static track table leaks a {kind} row"


# --------------------------------------------------- scored call / next up


def test_call_card_fallback_outcome_matches_lock_file(index_html):
    """When the locked file has been scored, the card shows its outcome and
    Brier - both read from the file, neither recomputed here."""
    lock = json.loads(LOCK.read_text())
    if lock["outcome"] is None or lock["scores"] is None:
        pytest.skip("lock-2026-07.json is not scored yet")

    block = region(index_html, "call")
    brier = lock["scores"]["m0_market_only"]["brier_score"]
    assert f'<span class="oc-v">{lock["outcome"]}</span>' in block
    assert f'<span class="oc-v">{score(brier)}</span>' in block
    assert "SCORED" in block, "a scored call must say so in the badge"

    hit = lock["point_call"] == lock["outcome"]
    assert ("matched" if hit else "missed") in block


def test_call_card_fallback_next_announcement_comes_from_the_calendar(index_html):
    """The next announcement is the first meeting in the Bank's published
    calendar (pipeline/site_context.py) after this call's own - never a
    hand-typed date, and never read off the clock."""
    lock = json.loads(LOCK.read_text())
    block = region(index_html, "call")

    later = sorted(m for m in UPCOMING_MEETINGS if m > lock["meeting_announcement"])
    assert later, "the calendar lists no meeting after the locked call's"
    assert f"<strong>{gb_date(later[0])}</strong>" in block, (
        f"the built-in next announcement is not {gb_date(later[0])}, "
        f"the next meeting in data/site_context.json"
    )


def test_call_card_heading_is_not_a_stale_forward_notice(index_html):
    """A locked call names its own meeting. "Next announcement" in the heading
    was wrong the morning after the announcement it named."""
    block = region(index_html, "call")
    heading = re.search(r'id="call-heading"[^>]*>(.*?)</p>', block, re.S)
    assert heading, "no call heading in the fallback"
    assert "Next announcement" not in heading.group(1)


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


# ---------------------------------------------- prediction file on display


def test_prediction_file_on_display_is_the_newest_lock_and_the_js_reads_it(index_html):
    """The call card carries the prediction file it was built from as a data
    attribute, derived from data/predictions/ by the generator, and the
    JavaScript reads that attribute rather than a hand-edited constant - so
    lock day has no "edit line 465" step."""
    from pipeline.site_figures import prediction_file

    block = region(index_html, "call")
    assert f'data-prediction-file="{prediction_file()}"' in block
    assert "dataset.predictionFile" in index_html
    assert "const PREDICTION_FILE = 'data/predictions/" not in index_html


def test_byline_and_meta_come_from_the_author_record():
    """Footer byline, meta author and the share-card alt text are generated
    from AUTHOR / the catalogue on both pages - no page carries its own copy."""
    from pipeline.site_figures import AUTHOR, figures

    f = figures()
    for path in (INDEX_HTML, METHODOLOGY_HTML):
        html = path.read_text()
        byline = region(html, "byline")
        assert AUTHOR["name"] in byline and AUTHOR["affiliation"] in byline
        assert f'href="mailto:{AUTHOR["email"]}"' in byline
        assert f'content="{AUTHOR["name"]}"' in region(html, "metaauthor")
        assert f"{f['corpus_start_month']} to {f['corpus_end_month']}" in region(html, "ogalt")
