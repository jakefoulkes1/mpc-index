import random

from pipeline.build_ladder import run_evaluation, score_models


def _fixture_records(n: int, seed: int = 3) -> list[dict]:
    rng = random.Random(seed)
    records = []
    for i in range(n):
        bp = rng.uniform(-30, 30)
        outcome = "hike" if bp > 10 else ("cut" if bp < -10 else "hold")
        if rng.random() < 0.15:
            outcome = rng.choice(["hike", "hold", "cut"])
        year = 2016 + i // 12
        month = 1 + i % 12
        records.append({
            "doc_id": f"minutes-fixture-{i:03d}",
            "date": f"{year}-{month:02d}-15",
            "scheduled": rng.random() > 0.1,  # a few unscheduled/special fixtures too
            "outcome": outcome,
            "implied_change_bp": bp,
            "m0_probs": {"p_cut": max(0.0, -bp / 25), "p_hold": 1 - min(1.0, abs(bp) / 25), "p_hike": max(0.0, bp / 25)},
            "index_level": rng.uniform(0.5, 1.5),
            "skew": rng.uniform(-0.001, 0.001),
            "votes_date": f"{year}-{month:02d}-15",
            "member_roster": ["A", "B", "C"],
        })
    return records


def _fixture_votes(records: list[dict], seed: int = 5) -> dict:
    rng = random.Random(seed)
    votes_by_date = {}
    for r in records:
        decided = 3.75
        rows = []
        for member in ("A", "B", "C"):
            drift = rng.choice([-0.25, 0.0, 0.0, 0.25])
            rows.append({"member": member, "preferred_rate": str(decided + drift),
                         "decided_rate": str(decided), "skew": str(r["skew"])})
        votes_by_date[r["votes_date"]] = rows
    return votes_by_date


def test_ladder_run_is_reproducible_on_a_fixture():
    records = _fixture_records(48)
    votes_by_date = _fixture_votes(records)

    result1 = run_evaluation(records, votes_by_date, eval_start="2018-01-01")
    result2 = run_evaluation(records, votes_by_date, eval_start="2018-01-01")

    assert result1 == result2
    assert len(result1["per_meeting"]) > 0

    scores1 = score_models(result1["per_meeting"])
    scores2 = score_models(result2["per_meeting"])
    assert scores1 == scores2
    for model in ("L0", "L1", "L2", "L3", "L4"):
        assert scores1[model]["n"] == len(result1["per_meeting"])
