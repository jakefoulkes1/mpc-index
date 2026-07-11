import datetime as dt

from pipeline.build_market_history import FIELDNAMES, build_rows

CURVE = {"maturities_months": [1.0, 2.0, 3.0], "forward_rates_pct": [3.70, 3.80, 3.90], "source_file": "fixture.xlsx"}


def _curve_history(dates: list[dt.date]) -> dict:
    return {d: dict(CURVE) for d in dates}


def test_build_rows_covers_every_meeting_with_full_history():
    meetings = [
        {"doc_id": "minutes-2026-01", "published": "2026-01-15"},
        {"doc_id": "minutes-2026-02", "published": "2026-02-19"},
    ]
    # Every calendar day covered, so no walk-back needed for this test.
    all_days = [dt.date(2026, 1, 1) + dt.timedelta(days=i) for i in range(80)]
    curve_history = _curve_history(all_days)
    sonia_history = {d: 3.75 for d in all_days}

    rows = build_rows(meetings, curve_history, sonia_history)

    assert len(rows) == len(meetings)
    assert {r["meeting"] for r in rows} == {"minutes-2026-01", "minutes-2026-02"}
    assert set(rows[0].keys()) == set(FIELDNAMES)


def test_build_rows_walks_back_over_weekend_gap():
    # Announcement is a Thursday; announcement-2d lands on a Tuesday that's
    # missing from the curve, so it should walk back to the Monday before.
    meetings = [{"doc_id": "minutes-2026-03", "published": "2026-03-05"}]  # Thursday
    tuesday = dt.date(2026, 3, 3)
    monday = dt.date(2026, 3, 2)
    curve_history = _curve_history([monday, dt.date(2026, 3, 5), dt.date(2026, 3, 8)])
    sonia_history = {d: 3.75 for d in curve_history}

    rows = build_rows(meetings, curve_history, sonia_history)

    assert tuesday not in curve_history
    assert rows[0]["lock_date"] == monday.isoformat()
