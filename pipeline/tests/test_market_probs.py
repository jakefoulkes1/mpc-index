import datetime as dt

import pytest

from pipeline.predict.market_probs import (
    LOCK_OFFSET_DAYS,
    forward_rate_for_date,
    implied_probs,
    interpolated_forward_rate,
    market_probs_for_meeting,
    months_between,
)


def test_months_between():
    assert months_between(dt.date(2026, 1, 1), dt.date(2026, 2, 1)) == pytest.approx(1.0186, abs=0.01)


def test_interpolated_forward_rate_linear_between_buckets():
    maturities = [1.0, 2.0, 3.0]
    rates = [3.70, 3.80, 3.90]
    assert interpolated_forward_rate(maturities, rates, 1.5) == pytest.approx(3.75)
    assert interpolated_forward_rate(maturities, rates, 1.0) == pytest.approx(3.70)


def test_interpolated_forward_rate_clips_outside_range():
    maturities = [1.0, 2.0]
    rates = [3.70, 3.75]
    assert interpolated_forward_rate(maturities, rates, 0.1) == 3.70
    assert interpolated_forward_rate(maturities, rates, 10.0) == 3.75


def test_forward_rate_for_date_uses_lock_offset_not_meeting_date():
    maturities = [1.0, 2.0, 3.0, 4.0]
    rates = [3.70, 3.75, 3.80, 3.85]
    today = dt.date(2026, 1, 1)
    # LOCK_OFFSET_DAYS=3 pushes the evaluation date past the meeting itself,
    # so the rate should differ from (and exceed, on this upward-sloping
    # curve) the rate evaluated exactly at the meeting date.
    meeting = dt.date(2026, 2, 25)  # ~1.81 months out
    at_meeting_months = months_between(today, meeting)
    rate_at_meeting = interpolated_forward_rate(maturities, rates, at_meeting_months)
    rate_with_offset = forward_rate_for_date(maturities, rates, today, meeting)
    assert rate_with_offset > rate_at_meeting


def test_forward_rate_for_date_clips_to_longest_maturity():
    maturities = [1.0, 2.0]
    rates = [3.70, 3.75]
    today = dt.date(2026, 1, 1)
    rate = forward_rate_for_date(maturities, rates, today, dt.date(2030, 1, 1))
    assert rate == 3.75


def test_forward_rate_for_date_rejects_past_meeting():
    with pytest.raises(ValueError):
        forward_rate_for_date([1.0], [3.7], dt.date(2026, 6, 1), dt.date(2026, 1, 1))


def test_implied_probs_zero_change_is_certain_hold():
    probs = implied_probs(forward_rate_pct=3.75, sonia_pct=3.75)
    assert probs == {"implied_change_bp": 0.0, "p_hike": 0.0, "p_hold": 1.0, "p_cut": 0.0}


def test_implied_probs_exactly_one_move_is_certain():
    hike = implied_probs(forward_rate_pct=4.00, sonia_pct=3.75)  # +25bp
    assert hike["p_hike"] == 1.0 and hike["p_hold"] == 0.0 and hike["p_cut"] == 0.0

    cut = implied_probs(forward_rate_pct=3.50, sonia_pct=3.75)  # -25bp
    assert cut["p_cut"] == 1.0 and cut["p_hold"] == 0.0 and cut["p_hike"] == 0.0


def test_implied_probs_partial_move_is_linear():
    probs = implied_probs(forward_rate_pct=3.875, sonia_pct=3.75)  # +12.5bp = half a move
    assert probs["p_hike"] == pytest.approx(0.5)
    assert probs["p_hold"] == pytest.approx(0.5)


def test_implied_probs_clips_beyond_one_move():
    probs = implied_probs(forward_rate_pct=4.25, sonia_pct=3.75)  # +50bp, double the assumed move
    assert probs["p_hike"] == 1.0
    assert probs["p_hold"] == 0.0


def test_market_probs_for_meeting_end_to_end_synthetic():
    curve = {
        "as_of_date": "2026-06-30",
        "maturities_months": [1.0, 2.0, 3.0],
        "forward_rates_pct": [3.75, 3.90, 4.00],
    }
    sonia = {"as_of_date": "2026-07-08", "sonia_pct": 3.75}
    result = market_probs_for_meeting(curve, sonia, dt.date(2026, 8, 15))
    assert result["meeting_date"] == "2026-08-15"
    assert result["lock_offset_days"] == LOCK_OFFSET_DAYS
    # meeting + 3 days is still within the 1-2 month window, interpolated
    # rate should sit strictly between the 1mo and 2mo bucket values.
    assert 3.75 < result["forward_rate_pct"] < 3.90
    assert 0.0 < result["p_hike"] < 1.0
