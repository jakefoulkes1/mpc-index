import pytest

from pipeline.validate import join_to_votes, pearson, spearman


def test_join_uses_nearest_date_within_tolerance():
    docs = [
        {"doc_id": "a", "published": "2020-03-20", "abg_net_index": 1.5, "delta_index": None, "decision_label": "cut"},
        {"doc_id": "b", "published": "2026-01-01", "abg_net_index": 1.0, "delta_index": -0.5, "decision_label": "hold"},
    ]
    votes = {
        "2020-03-19": {"skew": 0.01, "net_dissents": 0},
        "2019-01-01": {"skew": 0.0, "net_dissents": 0},
    }
    joined, unmatched = join_to_votes(docs, votes)
    assert len(joined) == 1
    assert joined[0]["doc_id"] == "a"
    assert joined[0]["gap_days"] == 1
    assert len(unmatched) == 1
    assert unmatched[0]["doc_id"] == "b"


def test_pearson_perfect_correlation():
    assert pearson([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)
    assert pearson([1, 2, 3], [6, 4, 2]) == pytest.approx(-1.0)


def test_spearman_handles_ties():
    assert spearman([1, 1, 2], [1, 1, 2]) == pytest.approx(1.0)
