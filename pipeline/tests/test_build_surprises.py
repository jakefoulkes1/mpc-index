from pipeline.build_surprises import build_rows


def _record(doc_id, date, scheduled, implied_bp, votes_date):
    return {"doc_id": doc_id, "date": date, "scheduled": scheduled,
            "implied_change_bp": implied_bp, "votes_date": votes_date}


def test_build_rows_computes_surprise_and_skips_specials():
    records = [
        _record("m1", "2020-01-01", True, 5.0, "2020-01-01"),
        _record("m2-special", "2020-02-01", False, -10.0, "2020-02-01"),
        _record("m3", "2020-03-01", True, -5.0, "2020-03-01"),
    ]
    decided_rates = {"2020-01-01": 0.0100, "2020-02-01": 0.0050, "2020-03-01": 0.0050}

    rows = build_rows(records, decided_rates)

    # m1 is the first meeting overall -> no previous rate -> excluded.
    # m2-special is unscheduled -> excluded from output rows.
    # m3: prev rate is m2-special's 0.0050 (rate history doesn't skip
    # specials, only the OUTPUT does), decided rate 0.0050 -> no change.
    assert len(rows) == 1
    assert rows[0]["meeting"] == "m3"
    assert rows[0]["actual_change_bp"] == 0.0
    assert rows[0]["implied_change_bp"] == -5.0
    assert rows[0]["surprise_bp"] == 5.0


def test_build_rows_uses_special_meeting_as_prev_rate_reference():
    records = [
        _record("m1", "2020-01-01", True, 0.0, "2020-01-01"),
        _record("m2-special", "2020-02-01", False, 0.0, "2020-02-01"),
        _record("m3", "2020-03-01", True, 0.0, "2020-03-01"),
    ]
    decided_rates = {"2020-01-01": 0.0100, "2020-02-01": 0.0050, "2020-03-01": 0.0075}
    rows = build_rows(records, decided_rates)
    # m3's actual change is vs the special meeting's rate (0.0050), not m1's.
    assert rows[0]["actual_change_bp"] == 25.0
