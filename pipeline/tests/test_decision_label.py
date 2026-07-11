from pipeline.decision_label import classify_decision


def test_classify_simple_decisions():
    assert classify_decision("maintain Bank Rate at 3.75%") == "hold"
    assert classify_decision("increase Bank Rate by 0.25 percentage points, to 0.5%") == "hike"
    assert classify_decision("reduce Bank Rate by 0.25 percentage points, to 4.5%") == "cut"


def test_classify_compound_decision_uses_bank_rate_verb_not_first_word():
    # minutes-2020-03-19-special: asset purchases mentioned first (increase),
    # Bank Rate actually cut - first-word classification gets this wrong.
    text = (
        "increase the Bank of England's holdings of UK government bonds and "
        "sterling non-financial investment-grade corporate bonds by £200 billion "
        "to a total of £645 billion, financed by the issuance of central bank "
        "reserves, and to reduce Bank Rate by 15 basis points to 0.1%"
    )
    assert classify_decision(text) == "cut"


def test_classify_none_and_unparseable():
    assert classify_decision(None) is None
    assert classify_decision("") is None
    assert classify_decision("some unrelated sentence with no rate verb") is None
