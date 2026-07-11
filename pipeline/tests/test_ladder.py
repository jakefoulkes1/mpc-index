import random

import pytest

from pipeline.ladder import (
    l0_always_hold,
    l1_market_only,
    l2_market_logit,
    l3_market_index_skew_logit,
    l4_member_simulation,
    market_implied_state_distribution,
)


def _assert_valid_probs(probs: dict):
    assert set(probs.keys()) == {"p_cut", "p_hold", "p_hike"}
    assert all(v >= 0 for v in probs.values())
    assert probs["p_cut"] + probs["p_hold"] + probs["p_hike"] == pytest.approx(1.0)


def _synthetic_records(n: int, seed: int = 7) -> list[dict]:
    rng = random.Random(seed)
    records = []
    for i in range(n):
        bp = rng.uniform(-30, 30)
        outcome = "hike" if bp > 10 else ("cut" if bp < -10 else "hold")
        if rng.random() < 0.1:  # a little label noise so the threshold isn't perfectly clean
            outcome = rng.choice(["hike", "hold", "cut"])
        records.append({
            "doc_id": f"minutes-fixture-{i:03d}",
            "date": f"2018-{1 + i // 8:02d}-{1 + i % 28:02d}",
            "outcome": outcome,
            "implied_change_bp": bp,
            "m0_probs": {"p_cut": 0.1, "p_hold": 0.8, "p_hike": 0.1},
            "index_level": rng.uniform(0.5, 1.5),
            "skew": rng.uniform(-0.001, 0.001),
            "votes_date": None,
            "member_roster": [],
        })
    return records


def test_l0_always_hold():
    _assert_valid_probs(l0_always_hold(None, None))
    assert l0_always_hold(None, None)["p_hold"] == 1.0


def test_l1_passes_through_m0():
    target = {"m0_probs": {"p_cut": 0.2, "p_hold": 0.5, "p_hike": 0.3}}
    assert l1_market_only(None, target) == target["m0_probs"]


def test_l2_falls_back_with_too_little_data():
    train = [{"implied_change_bp": 1.0, "outcome": "hold"}]
    target = {"implied_change_bp": 5.0}
    probs, status = l2_market_logit(train, target)
    assert probs is None
    assert "too little" in status


def test_l2_fits_and_predicts_with_enough_data():
    records = _synthetic_records(40)
    probs, status = l2_market_logit(records, {"implied_change_bp": 25})
    assert status == "ok"
    _assert_valid_probs(probs)
    assert probs["p_hike"] > probs["p_cut"]


def test_l3_uses_lagged_features_and_is_reproducible():
    records = _synthetic_records(40)
    result1 = l3_market_index_skew_logit(records, 30, 30)
    result2 = l3_market_index_skew_logit(records, 30, 30)
    assert result1 == result2


def test_market_implied_state_distribution():
    hawk = market_implied_state_distribution(25)
    assert hawk == {"hike": 1.0, "hold": 0.0, "cut": 0.0}
    dove = market_implied_state_distribution(-12.5)
    assert dove["cut"] == pytest.approx(0.5)
    neutral = market_implied_state_distribution(0)
    assert neutral["hold"] == 1.0


def test_l4_no_votes_date_returns_none():
    target = {"votes_date": None, "member_roster": []}
    assert l4_member_simulation({}, target) is None


def test_l4_is_reproducible_given_fixed_seed():
    votes_by_date = {
        "2018-01-01": [
            {"member": "A", "preferred_rate": "0.50", "decided_rate": "0.50", "skew": "0"},
            {"member": "B", "preferred_rate": "0.75", "decided_rate": "0.50", "skew": "0"},
        ],
    }
    target = {"votes_date": "2018-02-01", "member_roster": ["A", "B", "C"], "implied_change_bp": 10}
    result1 = l4_member_simulation(votes_by_date, target)
    result2 = l4_member_simulation(votes_by_date, target)
    assert result1 == result2
    _assert_valid_probs(result1)


def test_l4_member_with_no_history_defaults_to_majority_only():
    # No prior votes at all -> every member defaults to 100% hold, so the
    # simulated committee outcome should be a near-certain hold.
    target = {"votes_date": "2018-02-01", "member_roster": ["X", "Y", "Z"], "implied_change_bp": 0}
    result = l4_member_simulation({}, target)
    assert result["p_hold"] == pytest.approx(1.0)
