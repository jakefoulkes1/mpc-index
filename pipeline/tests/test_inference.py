import random

import pytest

from pipeline.inference import lagged_features_by_doc_id, ols_newey_west, spec2_ordered_logit_lr_test


def test_lagged_features_by_doc_id_uses_previous_record():
    records = [
        {"doc_id": "m1", "index_level": 1.0, "skew": 0.001},
        {"doc_id": "m2", "index_level": 1.5, "skew": -0.002},
        {"doc_id": "m3", "index_level": 0.5, "skew": 0.003},
    ]
    lagged = lagged_features_by_doc_id(records)
    assert lagged["m1"] == {"lagged_index": None, "lagged_skew": None}
    assert lagged["m2"] == {"lagged_index": 1.0, "lagged_skew": 0.001}
    assert lagged["m3"] == {"lagged_index": 1.5, "lagged_skew": -0.002}


def test_ols_newey_west_recovers_known_linear_relationship():
    random.seed(11)
    X, y = [], []
    for i in range(50):
        x = random.uniform(-10, 10)
        noise = random.uniform(-0.5, 0.5)
        X.append([x])
        y.append(2.0 * x + 3.0 + noise)  # y = 3 + 2x

    result = ols_newey_west(y, X, ["x"], maxlags=2)
    assert result["n"] == 50
    assert result["coefficients"]["const"]["coef"] == pytest.approx(3.0, abs=0.3)
    assert result["coefficients"]["x"]["coef"] == pytest.approx(2.0, abs=0.1)
    assert result["coefficients"]["x"]["p"] < 0.01  # should be a highly significant slope


def test_spec2_lr_test_detects_informative_added_feature():
    random.seed(21)
    rows, records = [], []
    for i in range(60):
        implied = random.uniform(-20, 20)
        index_val = random.uniform(0, 2)
        # outcome driven by BOTH implied and a strong index effect
        score = implied + 30 * (index_val - 1)
        outcome = "hike" if score > 10 else ("cut" if score < -10 else "hold")
        if random.random() < 0.1:  # a little label noise, avoids quasi-complete separation
            outcome = random.choice(["hike", "hold", "cut"])
        rows.append({"meeting": f"m{i}", "implied_change_bp": implied, "lagged_index": index_val})
        records.append({"doc_id": f"m{i}", "outcome": outcome})

    result = spec2_ordered_logit_lr_test(rows, records)
    assert result["converged"]
    assert result["lr_statistic"] > 0
    assert result["p_value"] < 0.05  # index should show up as a genuinely informative addition


def test_spec2_lr_test_reports_non_convergence_without_crashing():
    # Too few observations / degenerate data -> should report converged=False, not raise.
    rows = [{"meeting": "m1", "implied_change_bp": 1.0, "lagged_index": 1.0}]
    records = [{"doc_id": "m1", "outcome": "hold"}]
    result = spec2_ordered_logit_lr_test(rows, records)
    assert result["converged"] is False
