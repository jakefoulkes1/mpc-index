"""Unit + contract tests for the site-only track-record build step
(pipeline/build_track_record.py -> data/track_record.json).

Same spirit as test_build_annotations.py: pure-parser unit tests on
synthetic prediction files, plus a contract test that the REAL committed
data/track_record.json has every field the Track record section reads.
"""
import json
from pathlib import Path

import pytest

from pipeline.build_track_record import _kind_of, build, load_prediction_summary

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_TOP = {"schema", "first_pre_registered_call", "records"}
REQUIRED_RECORD = {
    "filename", "kind", "meeting_announcement", "lock_timestamp",
    "point_call", "m0_market_only", "outcome", "brier_m0",
}
REQUIRED_M0 = {"p_cut", "p_hold", "p_hike"}


def _make_prediction(**overrides) -> dict:
    payload = {
        "schema": "prediction-v1",
        "meeting_announcement": "2026-07-30",
        "lock_timestamp": "2026-07-11T17:40:05+00:00",
        "point_call": None,
        "m0_market_only": {"p_cut": 0.0, "p_hold": 0.97, "p_hike": 0.03},
        "outcome": None,
        "scores": None,
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize("filename,expected", [
    ("lock-2026-07.json", "locked"),
    ("dryrun-2026-07.json", "dryrun"),
    ("rehearsal-2026-07.json", "rehearsal"),
    ("mystery-2026-07.json", "other"),
])
def test_kind_of_filename_prefix(filename, expected):
    assert _kind_of(filename) == expected


def test_load_prediction_summary_unscored(tmp_path):
    path = tmp_path / "dryrun-2026-07.json"
    path.write_text(json.dumps(_make_prediction()))
    summary = load_prediction_summary(path)
    assert summary["kind"] == "dryrun"
    assert summary["brier_m0"] is None
    assert not (REQUIRED_M0 - summary["m0_market_only"].keys())


def test_load_prediction_summary_scored(tmp_path):
    path = tmp_path / "lock-2026-07.json"
    path.write_text(json.dumps(_make_prediction(
        point_call="hold", outcome="hold",
        scores={"m0_market_only": {"brier_score": 0.0018, "log_score": 0.0305},
                "always_hold_reference": {"brier_score": 0.0, "log_score": 0.0}},
    )))
    summary = load_prediction_summary(path)
    assert summary["kind"] == "locked"
    assert summary["brier_m0"] == 0.0018


def test_load_prediction_summary_missing_field_hard_stops(tmp_path):
    path = tmp_path / "broken.json"
    payload = _make_prediction()
    del payload["outcome"]
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="HARD STOP"):
        load_prediction_summary(path)


def test_build_shape_and_sort_with_synthetic_dir(tmp_path):
    (tmp_path / "dryrun-2026-07.json").write_text(json.dumps(_make_prediction()))
    (tmp_path / "lock-2026-05.json").write_text(json.dumps(
        _make_prediction(meeting_announcement="2026-05-14")
    ))
    data = build(predictions_dir=tmp_path)
    assert not (REQUIRED_TOP - data.keys())
    assert [r["filename"] for r in data["records"]] == ["lock-2026-05.json", "dryrun-2026-07.json"]
    assert not (REQUIRED_RECORD - data["records"][0].keys())


def test_real_track_record_json_has_every_field_the_section_reads():
    path = ROOT / "data" / "track_record.json"
    if not path.exists():
        return  # not generated in this checkout yet
    data = json.loads(path.read_text())
    assert not (REQUIRED_TOP - data.keys()), f"track_record.json missing: {REQUIRED_TOP - data.keys()}"
    for r in data["records"]:
        assert not (REQUIRED_RECORD - r.keys()), f"record missing: {REQUIRED_RECORD - r.keys()}"
        assert not (REQUIRED_M0 - r["m0_market_only"].keys())
