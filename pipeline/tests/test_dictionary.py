from pathlib import Path

from pipeline.score.dictionary import (
    load_lexicon,
    score_document,
    score_sentence,
    split_sentences,
)

FIX = Path(__file__).parent / "fixtures"
LEX = load_lexicon()


def test_sentence_split():
    sents = split_sentences("Rates rose. Inflation fell! Was it enough? Yes.")
    assert len(sents) == 4


def test_plain_hawkish():
    r = score_sentence("Upside risks to inflation warranted further tightening.", LEX)
    assert r["label"] == "hawkish"


def test_negation_flips_sign():
    r = score_sentence("The Committee did not tighten policy.", LEX)
    assert r["label"] == "dovish"


def test_empty_text():
    r = score_document("")
    assert r["n_sentences"] == 0
    assert r["net_hawkishness"] == 0.0


def test_real_excerpt_scores_in_range():
    text = (FIX / "june_2026_summary_excerpt.txt").read_text()
    r = score_document(text)
    assert r["n_sentences"] > 10
    assert r["hawkish_hits"] + r["dovish_hits"] > 0
    assert -1.0 <= r["net_hawkishness"] <= 1.0
