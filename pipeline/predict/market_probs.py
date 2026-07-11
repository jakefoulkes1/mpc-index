"""Market-implied probabilities of {cut, hold, hike} for a given MPC meeting
date, from the OIS forward curve and current SONIA (pipeline/market/ois.py).

Method - a documented modelling ASSUMPTION, not derived from the A&BG paper
or any external model, and not the only reasonable choice:

1. implied_change_bp = (forward rate at the maturity bucket just AFTER the
   meeting date) - (current SONIA), in basis points.
2. Two-state mapping: the implied change is assumed to price a SINGLE
   possible move, in ONE direction only (never a simultaneous hike
   probability and cut probability), of a fixed size (ASSUMED_MOVE_BP,
   25bp - the Bank's usual step size):
   - implied_change_bp > 0: p_hike = clip(implied_change_bp / 25, 0, 1),
     p_hold = 1 - p_hike, p_cut = 0
   - implied_change_bp < 0: p_cut  = clip(-implied_change_bp / 25, 0, 1),
     p_hold = 1 - p_cut, p_hike = 0
   - implied_change_bp == 0: p_hold = 1, others 0

This is a simplification: real market-implied distributions can price
partial moves in both directions at once, or moves of other sizes (50bp,
15bp). Documented here rather than hidden. See DECISIONS.md.
"""
import bisect
import datetime as dt

ASSUMED_MOVE_BP = 25.0
AVG_DAYS_PER_MONTH = 365.2425 / 12


def months_between(today: dt.date, meeting_date: dt.date) -> float:
    return (meeting_date - today).days / AVG_DAYS_PER_MONTH


def forward_rate_for_date(maturities_months: list[float], forward_rates_pct: list[float],
                           today: dt.date, meeting_date: dt.date) -> float:
    """Forward rate at the maturity bucket just AFTER the meeting date
    (the first available maturity >= the meeting's distance from today)."""
    target_months = months_between(today, meeting_date)
    if target_months <= 0:
        raise ValueError(f"meeting_date {meeting_date} is not after curve as_of date {today}")
    idx = bisect.bisect_left(maturities_months, target_months)
    if idx >= len(maturities_months):
        idx = len(maturities_months) - 1  # clip to the longest available maturity
    return forward_rates_pct[idx]


def implied_probs(forward_rate_pct: float, sonia_pct: float) -> dict:
    implied_change_bp = (forward_rate_pct - sonia_pct) * 100
    if implied_change_bp > 0:
        p_hike = max(0.0, min(1.0, implied_change_bp / ASSUMED_MOVE_BP))
        p_hold, p_cut = 1 - p_hike, 0.0
    elif implied_change_bp < 0:
        p_cut = max(0.0, min(1.0, -implied_change_bp / ASSUMED_MOVE_BP))
        p_hold, p_hike = 1 - p_cut, 0.0
    else:
        p_hold, p_hike, p_cut = 1.0, 0.0, 0.0
    return {
        "implied_change_bp": round(implied_change_bp, 2),
        "p_hike": round(p_hike, 4),
        "p_hold": round(p_hold, 4),
        "p_cut": round(p_cut, 4),
    }


def market_probs_for_meeting(curve: dict, sonia: dict, meeting_date: dt.date) -> dict:
    """curve is pipeline.market.ois.latest_forward_curve()'s return value;
    sonia is pipeline.market.ois.latest_sonia()'s."""
    curve_as_of = dt.date.fromisoformat(curve["as_of_date"])
    rate = forward_rate_for_date(curve["maturities_months"], curve["forward_rates_pct"], curve_as_of, meeting_date)
    probs = implied_probs(rate, sonia["sonia_pct"])
    return {
        "meeting_date": meeting_date.isoformat(),
        "curve_as_of": curve["as_of_date"],
        "sonia_as_of": sonia["as_of_date"],
        "forward_rate_pct": round(rate, 4),
        "sonia_pct": sonia["sonia_pct"],
        "assumed_move_bp": ASSUMED_MOVE_BP,
        **probs,
    }
