"""Contract + unit tests for the site-only context exporter
(pipeline/site_context.py -> data/site_context.json).

Same spirit as test_site_contract.py: the contract test asserts the REAL
committed data/site_context.json contains every field the front-end's
"Market & macro context" panel and the chart's Bank Rate overlay read, so
the panel can't silently break from schema drift. The unit tests exercise
the pure helpers against synthetic data - no live downloads in tests.
"""
import datetime as dt
import json
from pathlib import Path

from pipeline.site_context import (
    bank_rate_history,
    gilt_2y_context,
    ois_path_context,
    _era_end_year,
)

ROOT = Path(__file__).resolve().parents[2]

# Fields index.html's context panel / chart overlay actually read - keep in
# sync with index.html by hand (same convention as test_site_contract.py).
REQUIRED_TOP = {"schema", "disclaimer", "context_not_model_inputs",
                "ois_path", "bank_rate_history", "gilt_2y"}
REQUIRED_OIS_PATH = {"curve_as_of", "sonia_as_of", "sonia_pct", "assumed_move_bp", "meetings"}
REQUIRED_OIS_MEETING = {"meeting_date", "implied_change_bp", "p_cut", "p_hold", "p_hike"}
REQUIRED_GILT = {"label", "as_of", "latest_pct", "window_months", "sparkline"}
REQUIRED_GILT_POINT = {"date", "yield_pct"}
REQUIRED_RATE_POINT = {"date", "rate_pct"}


def test_site_context_json_has_every_field_the_panel_reads():
    path = ROOT / "data" / "site_context.json"
    if not path.exists():
        return  # not generated in this checkout yet
    d = json.loads(path.read_text())
    assert not (REQUIRED_TOP - d.keys()), f"site_context.json missing top-level: {REQUIRED_TOP - d.keys()}"

    assert not (REQUIRED_OIS_PATH - d["ois_path"].keys())
    assert d["ois_path"]["meetings"], "ois_path has no meetings"
    for m in d["ois_path"]["meetings"]:
        assert not (REQUIRED_OIS_MEETING - m.keys()), f"ois meeting missing: {REQUIRED_OIS_MEETING - m.keys()}"

    assert d["bank_rate_history"]["points"], "bank_rate_history has no points"
    for p in d["bank_rate_history"]["points"]:
        assert not (REQUIRED_RATE_POINT - p.keys())

    assert not (REQUIRED_GILT - d["gilt_2y"].keys()), f"gilt_2y missing: {REQUIRED_GILT - d['gilt_2y'].keys()}"
    assert d["gilt_2y"]["sparkline"], "gilt sparkline empty"
    for p in d["gilt_2y"]["sparkline"]:
        assert not (REQUIRED_GILT_POINT - p.keys())


def test_bank_rate_history_dedups_members_and_converts_to_percent():
    rows = [
        {"meeting_date": "2020-03-11", "decided_rate": "0.0025"},
        {"meeting_date": "2020-03-11", "decided_rate": "0.0025"},  # another member, same meeting
        {"meeting_date": "2015-08-06", "decided_rate": "0.005"},
    ]
    out = bank_rate_history(rows)
    assert out == [
        {"date": "2015-08-06", "rate_pct": 0.5},  # sorted by date
        {"date": "2020-03-11", "rate_pct": 0.25},
    ]


def test_era_end_year_parses_present_and_ranges():
    assert _era_end_year("GLC Nominal daily data_2025 to present.xlsx") == 9999
    assert _era_end_year("GLC Nominal daily data_2016 to 2024.xlsx") == 2024
    assert _era_end_year("GLC Nominal daily data_1979 to 1984.xlsx") == 1984


def test_gilt_2y_context_windows_to_last_12_months():
    # Two years of monthly points; only the last ~12 months should survive.
    series = []
    d = dt.date(2024, 7, 1)
    val = 3.0
    while d <= dt.date(2026, 7, 1):
        series.append((d, round(val, 4)))
        # advance ~1 month
        year, month = (d.year + (d.month // 12)), (d.month % 12 + 1)
        d = dt.date(year, month, 1)
        val += 0.05
    ctx = gilt_2y_context(series=series)
    assert ctx["latest_pct"] == series[-1][1]
    assert ctx["as_of"] == series[-1][0].isoformat()
    # every kept point is within 365 days of the latest
    latest = dt.date.fromisoformat(ctx["as_of"])
    for p in ctx["sparkline"]:
        assert (latest - dt.date.fromisoformat(p["date"])).days <= 365
    # and it dropped the oldest (2024-07) point
    assert ctx["sparkline"][0]["date"] > "2025-06-01"


def test_ois_path_context_shape_with_synthetic_curve():
    # flat curve slightly above SONIA -> small hike lean, well-formed output
    curve = {
        "as_of_date": "2026-07-09",
        "maturities_months": [float(m) for m in range(1, 25)],
        "forward_rates_pct": [3.80] * 24,
    }
    sonia = {"as_of_date": "2026-07-08", "sonia_pct": 3.75}
    out = ois_path_context(curve, sonia, meeting_dates=["2026-07-30", "2026-09-17"])
    assert not (REQUIRED_OIS_PATH - out.keys())
    assert len(out["meetings"]) == 2
    for m in out["meetings"]:
        assert not (REQUIRED_OIS_MEETING - m.keys())
        # probabilities form a valid distribution
        assert abs(m["p_cut"] + m["p_hold"] + m["p_hike"] - 1.0) < 1e-9
