"""Date-integrity guard for DECISIONS.md: no entry header may be dated in
the future. Added with the 2026-07-13 erratum, after 29 header dates turned
out to have been written from an assumed session cadence rather than the
system clock (see the erratum entry in DECISIONS.md and the date rule in
CLAUDE.md).

"Today" is the author's date, Europe/London - the clock `date` reads when
an entry is written. CI runs on UTC, which on 16 September 2026 at 23:25
rejected an entry dated 17 September that was correct on the author's
clock; comparing in the runner's zone is a false alarm, not a guard.
"""
import datetime as dt
import re
from pathlib import Path
from zoneinfo import ZoneInfo

DECISIONS_PATH = Path(__file__).resolve().parents[2] / "DECISIONS.md"
# Entry headers look like "## 2026-07-11 — era corpus, ..." - the TOC's own
# "## Table of contents" header deliberately doesn't match.
HEADER_DATE_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2}) ", re.MULTILINE)


def test_no_decisions_entry_is_dated_in_the_future():
    text = DECISIONS_PATH.read_text()
    dates = [dt.date.fromisoformat(d) for d in HEADER_DATE_RE.findall(text)]
    assert dates, "no dated entry headers parsed - file layout changed?"
    today = dt.datetime.now(ZoneInfo("Europe/London")).date()
    future = [d.isoformat() for d in dates if d > today]
    assert not future, (
        f"DECISIONS.md entries dated in the future (Europe/London date {today}): "
        f"{future} - dates must come from running `date`, per CLAUDE.md"
    )
