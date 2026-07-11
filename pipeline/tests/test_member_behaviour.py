from pipeline.member_behaviour import (
    classify,
    dissent_stickiness,
    transition_counts,
    transition_matrix,
)


def test_classify():
    assert classify(0.04, 0.0375) == "hawkish_dissent"
    assert classify(0.035, 0.0375) == "dovish_dissent"
    assert classify(0.0375, 0.0375) == "with_majority"


def test_transition_matrix_and_stickiness_on_synthetic_sequence():
    # One member dissenting hawkishly twice in a row, then back to majority.
    member_votes = {
        "A": [("2020-01-01", "with_majority"),
              ("2020-02-01", "hawkish_dissent"),
              ("2020-03-01", "hawkish_dissent"),
              ("2020-04-01", "with_majority")],
    }
    counts = transition_counts(member_votes)
    matrix = transition_matrix(counts)

    assert matrix["with_majority"]["counts"]["hawkish_dissent"] == 1
    assert matrix["hawkish_dissent"]["counts"]["hawkish_dissent"] == 1
    assert matrix["hawkish_dissent"]["counts"]["with_majority"] == 1
    assert matrix["hawkish_dissent"]["n"] == 2

    stick = dissent_stickiness(counts)
    assert stick["p_dissent_again_given_dissented"] == 0.5  # 1 of 2 dissent->dissent transitions
    assert stick["n_given_dissented"] == 2
