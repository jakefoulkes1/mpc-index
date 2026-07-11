import datetime as dt
import json

import pytest

from pipeline.predict.lock import assert_curve_is_fresh, build_prediction, business_days_between, index_stats

SYNTHETIC_CURVE = {
    "as_of_date": "2026-06-30",
    "source_file": "fixture.xlsx",
    "sheet": "1. fwds, short end",
    "maturities_months": [1.0, 2.0],
    "forward_rates_pct": [3.75, 3.90],
}
SYNTHETIC_SONIA = {"as_of_date": "2026-07-08", "series_code": "IUDSOIA", "sonia_pct": 3.75}

REQUIRED_TOP_LEVEL_FIELDS = {
    "schema", "meeting_announcement", "lock_timestamp", "code_version",
    "input_hashes", "m0_market_only", "index_current", "index_current_doc_id",
    "index_trailing_mean", "index_trailing_n", "point_call", "rationale",
    "outcome", "scores",
}


def _write_fixture_index(path):
    docs = [
        {"doc_id": f"minutes-2026-0{i}", "published": f"2026-0{i}-15", "abg_net_index": v}
        for i, v in enumerate([1.0, 1.2, 0.8, 1.5, 1.1], start=1)
    ]
    path.write_text(json.dumps({"documents": docs}))


def test_index_stats_trailing_mean(tmp_path, monkeypatch):
    index_path = tmp_path / "index.json"
    _write_fixture_index(index_path)
    monkeypatch.setattr("pipeline.predict.lock.INDEX_PATH", index_path)

    stats = index_stats(n_trailing=4)
    assert stats["index_current"] == 1.1
    assert stats["index_current_doc_id"] == "minutes-2026-05"
    # last 4 of [1.0, 1.2, 0.8, 1.5, 1.1] = [1.2, 0.8, 1.5, 1.1]
    assert stats["index_trailing_mean"] == round((1.2 + 0.8 + 1.5 + 1.1) / 4, 4)
    assert stats["index_trailing_n"] == 4


def test_build_prediction_schema_no_live_calls(tmp_path, monkeypatch):
    index_path = tmp_path / "index.json"
    _write_fixture_index(index_path)
    monkeypatch.setattr("pipeline.predict.lock.INDEX_PATH", index_path)

    payload = build_prediction(dt.date(2026, 8, 15), curve=SYNTHETIC_CURVE, sonia=SYNTHETIC_SONIA)

    assert REQUIRED_TOP_LEVEL_FIELDS <= payload.keys()
    assert payload["meeting_announcement"] == "2026-08-15"
    assert payload["point_call"] is None
    assert payload["outcome"] is None
    assert payload["scores"] is None
    assert payload["rationale"].startswith("TODO(Jake)")
    assert set(payload["input_hashes"].keys()) == {"corpus_index_json_sha256", "ois_snapshot_sha256"}
    assert payload["m0_market_only"]["meeting_date"] == "2026-08-15"


def test_business_days_between_skips_weekends():
    # Fri 3 Jul -> Mon 6 Jul 2026 is 1 business day, despite spanning a weekend.
    assert business_days_between(dt.date(2026, 7, 3), dt.date(2026, 7, 6)) == 1
    assert business_days_between(dt.date(2026, 7, 6), dt.date(2026, 7, 3)) == -1
    assert business_days_between(dt.date(2026, 7, 6), dt.date(2026, 7, 6)) == 0


def test_assert_curve_is_fresh_passes_within_limit():
    # Curve from Tuesday, checked as of Thursday of the same week -> 2 business days.
    assert_curve_is_fresh("2026-07-07", today=dt.date(2026, 7, 9))


def test_assert_curve_is_fresh_hard_stops_when_stale():
    # Same stale case that motivated this fix: curve from end of June,
    # checked well into July.
    with pytest.raises(ValueError, match="HARD STOP"):
        assert_curve_is_fresh("2026-06-30", today=dt.date(2026, 7, 11))
