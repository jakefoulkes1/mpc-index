"""Market-implied probabilities of {cut, hold, hike} for a given MPC meeting
date, from the OIS forward curve and current SONIA (pipeline/market/ois.py).

Method - a documented modelling ASSUMPTION, not derived from the A&BG paper
or any external model, and not the only reasonable choice:

1. implied_change_bp = (forward rate LOCK_OFFSET_DAYS after the meeting
   date, linearly interpolated between the curve's adjacent whole-month
   maturity buckets) - (current SONIA), in basis points.

   KNOWN LIMITATION (quantified and the offset chosen specifically to
   reduce it - see DECISIONS.md, 2026-08-01): the Bank's published forward
   curve is a smoothed spline fitted across maturities, which blurs the
   discrete jump in Bank Rate that actually happens on a meeting date. The
   curve's value AT the meeting date itself understates the priced move
   and biases probabilities toward hold. Evaluating a few days after
   (rather than exactly at) the meeting recovers most of this - quantified
   on live data as a ~0.3-1bp difference under the current fairly flat
   curve, growing under more sloped curves. A 2-week-average alternative
   was also quantified and rejected: it recovers slightly more of the
   bias, but during the Aug 2015-2016 monthly-meeting era a 2-week window
   is roughly half the inter-meeting gap, risking contamination from the
   NEXT meeting's expectations - a bigger problem for a benchmark that
   must run across that era than the small extra bias correction is worth.
   +3 days is safely inside even the shortest historical gap.

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
# See the module docstring and DECISIONS.md (2026-08-01) for why 3 days,
# not 0 (at the meeting) or a 2-week average.
LOCK_OFFSET_DAYS = 3


def months_between(today: dt.date, target_date: dt.date) -> float:
    return (target_date - today).days / AVG_DAYS_PER_MONTH


def interpolated_forward_rate(maturities_months: list[float], forward_rates_pct: list[float],
                               target_months: float) -> float:
    """Forward rate at an arbitrary (real-valued) maturity, linearly
    interpolated between the curve's adjacent whole-month buckets. Clipped
    to the first/last available bucket if target_months is outside the
    curve's range."""
    if target_months <= maturities_months[0]:
        return forward_rates_pct[0]
    if target_months >= maturities_months[-1]:
        return forward_rates_pct[-1]
    idx = bisect.bisect_left(maturities_months, target_months)
    m0, m1 = maturities_months[idx - 1], maturities_months[idx]
    r0, r1 = forward_rates_pct[idx - 1], forward_rates_pct[idx]
    frac = (target_months - m0) / (m1 - m0)
    return r0 + frac * (r1 - r0)


def forward_rate_for_date(maturities_months: list[float], forward_rates_pct: list[float],
                           today: dt.date, meeting_date: dt.date) -> float:
    """Forward rate LOCK_OFFSET_DAYS after the meeting date (interpolated -
    see module docstring for why not exactly at the meeting)."""
    target_date = meeting_date + dt.timedelta(days=LOCK_OFFSET_DAYS)
    target_months = months_between(today, target_date)
    if target_months <= 0:
        raise ValueError(f"meeting_date {meeting_date} (+{LOCK_OFFSET_DAYS}d) is not after curve as_of date {today}")
    return interpolated_forward_rate(maturities_months, forward_rates_pct, target_months)


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
        "lock_offset_days": LOCK_OFFSET_DAYS,
        **probs,
    }
