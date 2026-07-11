from pathlib import Path

from pipeline.score.abg import load_abg_lexicon, score_document

FIX = Path(__file__).parent / "fixtures"


def test_lexicon_term_counts_match_the_paper():
    lex = load_abg_lexicon()
    assert len(lex["nouns"]) == 7
    assert len(lex["hawkish_adjectives"]) == 5
    assert len(lex["dovish_adjectives"]) == 5


def test_hawkish_dovish_bigram_classification():
    lex = load_abg_lexicon()
    hawk = score_document("Higher inflation and stronger growth are expected.", lex)
    assert hawk["abg_hawk"] == 2
    assert hawk["abg_dove"] == 0
    assert hawk["abg_net_index"] == 2.0

    dove = score_document("Weaker growth and lower prices are expected.", lex)
    assert dove["abg_hawk"] == 0
    assert dove["abg_dove"] == 2
    assert dove["abg_net_index"] == 0.0

    neutral = score_document("No relevant terms here at all.")
    assert neutral["abg_net_index"] == 1.0


def test_june_2026_fixture_score_is_stable():
    text = (FIX / "june_2026_summary_excerpt.txt").read_text()
    result = score_document(text)
    assert result == {"abg_hawk": 0, "abg_dove": 0, "abg_net_index": 1.0}
