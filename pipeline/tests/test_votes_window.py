"""The voting-sheet era window is derived from the corpus, not declared.

Before 2026-08-10 it was two hardcoded dates. The 30 July 2026 meeting was
silently dropped from votes.csv because the upper bound still read
2026-07-01: the script printed "94 meetings" and exited 0. Nothing failed.

These tests hold the derived window to its purpose - the window is the
corpus, so a meeting in the corpus can never fall outside it - and add the
alarm for the opposite direction: a meeting sitting in the Bank's sheet that
the window excludes, which means there is an ingest waiting to be done.

See DECISIONS.md, 2026-08-10.
"""
import datetime as dt
import json

import pytest

from pipeline.build_votes import XLSX_PATH, corpus_window


def test_derived_window_covers_every_published_corpus_document():
    """The invariant the hardcoded constant broke."""
    start, end = corpus_window()
    from pipeline.build_votes import INDEX_PATH

    corpus = json.loads(INDEX_PATH.read_text())
    published = [d["published"] for d in corpus["documents"] if d["published"]]
    assert published, "corpus has no published documents"

    outside = [p for p in published if not (start <= dt.date.fromisoformat(p) < end)]
    assert not outside, (
        f"corpus documents fall outside the derived voting window "
        f"{start}..{end}: {sorted(outside)}"
    )


def test_derived_window_is_tight_to_the_corpus(monkeypatch, tmp_path):
    """Synthetic corpus, so this runs anywhere: the window is exactly the
    span of published dates, with an exclusive upper bound one day past the
    last one."""
    index = tmp_path / "index.json"
    index.write_text(json.dumps({"documents": [
        {"doc_id": "a", "published": "2020-01-30"},
        {"doc_id": "b", "published": "2021-06-23"},
        {"doc_id": "c", "published": None},
        {"doc_id": "d", "published": "2019-08-01"},
    ]}))
    monkeypatch.setattr("pipeline.build_votes.INDEX_PATH", index)

    start, end = corpus_window()
    assert start == dt.date(2019, 8, 1), "start is the earliest published date"
    assert end == dt.date(2021, 6, 24), "end is one day past the latest, exclusive"
    assert start <= dt.date(2021, 6, 23) < end


def test_missing_index_is_a_hard_stop_not_a_silent_default(monkeypatch, tmp_path):
    """A missing corpus must stop the build, not fall back to some window.

    Falling back is how the original bug shipped: a plausible-looking number
    of meetings and no error.
    """
    monkeypatch.setattr("pipeline.build_votes.INDEX_PATH", tmp_path / "nope.json")
    with pytest.raises(SystemExit, match="build the index first"):
        corpus_window()


def test_voting_sheet_has_no_meeting_the_window_excludes():
    """Alarm for an un-ingested meeting.

    If the Bank's sheet carries a meeting dated at or after the corpus's own
    end, the corpus is behind the source: the minutes for that meeting have
    not been scraped yet. That is not a bug in this code, it is a to-do -
    but it must be loud, because the silent version of exactly this cost a
    meeting last time.

    Skips when the spreadsheet is absent: data/raw/ is gitignored, so CI has
    no copy. Same convention as test_inspect.py.
    """
    if not XLSX_PATH.exists():
        pytest.skip(f"{XLSX_PATH.name} not in this checkout (data/raw/ is gitignored)")

    import openpyxl

    from pipeline.build_votes import HEADER_ROW

    start, end = corpus_window()
    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
    ws = wb["Bank Rate Decisions"]

    later = []
    for row in ws.iter_rows(min_row=HEADER_ROW + 1, values_only=True):
        date, decided = row[1], row[2]
        if not isinstance(date, dt.datetime) or not isinstance(decided, (int, float)):
            continue
        if date.date() >= end:
            later.append(date.date().isoformat())

    assert not later, (
        f"the Bank's voting sheet has {len(later)} meeting(s) at or after the corpus "
        f"end ({end}): {sorted(later)}. The corpus is behind the source - scrape "
        f"those minutes and rebuild: python -m pipeline.scrape.minutes <year> <month>, "
        f"then python -m pipeline.build_index && python -m pipeline.build_votes"
    )
