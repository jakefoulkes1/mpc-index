"""The status line and the track record's pending row are generated, and
move on by themselves.

Status line (replaces the "Beta" badge, DECISIONS.md 2026-09-02): the count
of locked calls from data/track_record.json, the corpus size from
data/index.json, the next lock date from the Bank's calendar
(pipeline/site_context.py) under the announcement-minus-two convention, and
the build stamp from data/build_info.json - on both pages, from one
generator.

Pending row: the next meeting in the calendar after the newest locked call
appears in the track record with its lock date and no call, probabilities,
outcome or score. Once a lock-* file for that meeting exists, the newest
lock moves and so does the row - tested here in both states through the
calendar function the generator uses.
"""
import json
import re
from pathlib import Path

from pipeline.site_context import UPCOMING_MEETINGS
from pipeline.site_figures import figures, lock_date_for, next_meeting_after

ROOT = Path(__file__).resolve().parents[2]
PAGES = ("index.html", "methodology.html")


def region(html: str, name: str) -> str:
    m = re.search(rf"<!--\s*fallback:{name}\b.*?-->(.*?)<!--\s*/fallback:{name}\s*-->", html, re.S)
    assert m, f"no fallback:{name} region"
    return m.group(1)


def test_status_line_on_both_pages_states_the_record_the_calendar_and_the_corpus():
    f = figures()
    track = json.loads((ROOT / "data/track_record.json").read_text())
    locked = sum(1 for r in track["records"] if r["kind"] == "locked")
    index_n = len(json.loads((ROOT / "data/index.json").read_text())["documents"])
    for page in PAGES:
        html = (ROOT / page).read_text()
        status = region(html, "status")
        assert f"{locked} locked call" in status, f"{page}: status line does not count the locked calls"
        assert f"next lock {f['next_lock_date']}" in status
        assert f"{index_n} documents" in status
        assert "Beta" not in html, f"{page} still carries the Beta badge"


def test_build_stamp_in_the_status_line_matches_build_info_on_both_pages():
    info = json.loads((ROOT / "data/build_info.json").read_text())
    for page in PAGES:
        stamp = region((ROOT / page).read_text(), "buildstamp")
        assert stamp.startswith("site built "), f"{page}: {stamp!r}"
        assert info["last_commit_short_sha"] in stamp
        assert info["last_commit_sha"] in stamp


def test_next_lock_is_the_calendar_meeting_after_the_newest_lock_minus_two_days():
    f = figures()
    locks = sorted((ROOT / "data/predictions").glob("lock-*.json"))
    newest = json.loads(locks[-1].read_text())["meeting_announcement"]
    nxt = next_meeting_after(newest)
    assert nxt in UPCOMING_MEETINGS and nxt > newest
    assert f["next_lock_date"] == _gb(lock_date_for(nxt))
    assert f["next_meeting"] == _gb(nxt)


def test_pending_row_moves_on_when_the_next_lock_exists():
    """Both states of the rule the generator applies. With July the newest
    lock, September is pending; with September locked, November is."""
    assert next_meeting_after("2026-07-30") == "2026-09-17"
    assert next_meeting_after("2026-09-17") == "2026-11-05"
    assert lock_date_for("2026-09-17") == "2026-09-15"
    assert lock_date_for("2026-11-05") == "2026-11-03"


def test_pending_row_in_the_static_track_table_carries_no_figures():
    f = figures()
    block = region((ROOT / "index.html").read_text(), "track")
    rows = re.findall(r'<tr class="kind-pending">(.*?)</tr>', block, re.S)
    assert len(rows) == 1, "exactly one pending row"
    row = rows[0]
    assert f["next_meeting"] in row
    assert f"locks {f['next_lock_date']}" in row
    cells = re.findall(r"<td>(.*?)</td>", row, re.S)
    assert cells[2:] == ["&mdash;"] * 6, "a pending row has no call, probabilities, outcome or score"
    assert "%" not in row


def test_javascript_keeps_the_pending_row_and_never_hides_it():
    html = (ROOT / "index.html").read_text()
    assert "querySelectorAll('tr.kind-pending')" in html
    assert "pending.forEach(tr => tbody.appendChild(tr))" in html
    assert "!tr.classList.contains('kind-pending')" in html


def _gb(iso: str) -> str:
    from pipeline.site_figures import gb_date

    return gb_date(iso)
