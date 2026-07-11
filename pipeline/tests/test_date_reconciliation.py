import csv
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Known, individually-logged 1-day gaps between our `published` field
# (meeting_end + 1 day, a uniform rule applied to every document) and the
# voting sheet's own announcement date, which is not always meeting_end + 1
# (weekend/holiday slippage for 3 regular meetings; the 19 March 2020
# special was announced same-day, not the next day). See DECISIONS.md.
MAX_DAY_TOLERANCE = 1


def _load_corpus_dates() -> set[str]:
    data = json.loads((ROOT / "data" / "index.json").read_text())
    return {d["published"] for d in data["documents"] if d["published"]}


def _load_votes_dates() -> set[str]:
    with open(ROOT / "data" / "votes.csv") as fh:
        return {row["meeting_date"] for row in csv.DictReader(fh)}


def test_corpus_and_voting_record_dates_match_one_to_one_within_tolerance():
    corpus_dates = {dt.date.fromisoformat(d) for d in _load_corpus_dates()}
    votes_dates = {dt.date.fromisoformat(d) for d in _load_votes_dates()}

    unmatched_corpus = []
    for c in corpus_dates:
        if not any(abs((c - v).days) <= MAX_DAY_TOLERANCE for v in votes_dates):
            unmatched_corpus.append(c)
    unmatched_votes = []
    for v in votes_dates:
        if not any(abs((c - v).days) <= MAX_DAY_TOLERANCE for c in corpus_dates):
            unmatched_votes.append(v)

    assert unmatched_corpus == [], f"corpus dates with no voting-sheet match within {MAX_DAY_TOLERANCE} day(s): {unmatched_corpus}"
    assert unmatched_votes == [], f"voting-sheet dates with no corpus match within {MAX_DAY_TOLERANCE} day(s): {unmatched_votes}"
