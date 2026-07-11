"""Apel & Blix Grimaldi (2012) hawkish/dovish index, implemented as described
in the paper - see pipeline/score/lexicon/abg_2012.json for the verbatim term
lists, page references and formulas.

Method (paper's own, not this repo's dictionary.py machinery):
1. Tokenise the whole document (no sentence splitting - the paper counts
   two-word combinations across the full text, not per sentence).
2. For each adjacent (adjective, noun) token pair, e.g. "higher inflation",
   count it hawkish if the adjective is one of the paper's hawkish stems and
   dovish if one of the paper's dovish stems. Multi-word nouns ("oil price",
   "cyclical position") are matched as a following two-token sequence.
3. Net Index = [(#hawk / (#hawk + #dove)) - (#dove / (#hawk + #dove))] + 1
   (p.10). Range [0, 2]; 1 is neutral. 0 hawk+dove hits -> defined as 1
   (neutral), matching the paper's "excludes negative numbers" intent.

Deliberately NOT applied here (see DECISIONS.md for why): this repo's
negation window, sentence-level scoring, or any other extra from
pipeline/score/dictionary.py. The paper has no negation handling at all.
"""
import json
import re
from pathlib import Path

LEXICON_PATH = Path(__file__).parent / "lexicon" / "abg_2012.json"

# Net Index = [(#hawk/(#hawk+#dove)) - (#dove/(#hawk+#dove))] + 1 (paper p.10).
# Theoretical range [0, 2]; this is the ratio's fixed midpoint, not fitted.
NEUTRAL_VALUE = 1.0

_TOKEN = re.compile(r"[a-z']+")


def load_abg_lexicon(path: Path = LEXICON_PATH) -> dict:
    with open(path) as fh:
        raw = json.load(fh)
    return {
        "nouns": [tuple(term.split()) for term in raw["nouns_core"]["terms"]],
        "hawkish_adjectives": tuple(raw["hawkish_adjectives"]["terms"]),
        "dovish_adjectives": tuple(raw["dovish_adjectives"]["terms"]),
    }


def _noun_matches_at(tokens: list[str], i: int, noun: tuple[str, ...]) -> bool:
    if i + len(noun) > len(tokens):
        return False
    return all(tokens[i + k].startswith(noun[k]) for k in range(len(noun)))


def score_document(text: str, lex: dict | None = None) -> dict:
    lex = lex or load_abg_lexicon()
    tokens = _TOKEN.findall(text.lower())

    hawk = dove = 0
    for i in range(len(tokens) - 1):
        token = tokens[i]
        is_hawk_adj = any(token.startswith(stem) for stem in lex["hawkish_adjectives"])
        is_dove_adj = any(token.startswith(stem) for stem in lex["dovish_adjectives"])
        if not is_hawk_adj and not is_dove_adj:
            continue
        for noun in lex["nouns"]:
            if _noun_matches_at(tokens, i + 1, noun):
                if is_hawk_adj:
                    hawk += 1
                else:
                    dove += 1
                break

    total = hawk + dove
    net_index = ((hawk / total) - (dove / total)) + 1 if total else NEUTRAL_VALUE
    return {
        "abg_hawk": hawk,
        "abg_dove": dove,
        "abg_net_index": round(net_index, 4),
    }
