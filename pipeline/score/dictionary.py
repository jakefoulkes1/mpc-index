"""Dictionary-based hawk-dove scoring, sentence level. v0.

Method
------
1. Split a document into sentences.
2. Lowercase and tokenise each sentence (hyphens break tokens, so
   "second-round" -> "second", "round" and multi-word terms match).
3. Match hawkish/dovish terms (1-3 word phrases) against the token sequence.
4. A negator token within the 3 tokens before a match flips its sign
   ("did not tighten" reads dovish).
5. Document score: net_hawkishness = (H - D) / (H + D), zero if no hits.

The bundled lexicon (lexicon/starter_v0.json) is a PLUMBING lexicon: it exists
to test the pipeline end to end and its output is never used in analysis.
The research baseline is Apel & Blix Grimaldi (2012) implemented verbatim.
See DECISIONS.md, entry 2026-07-05.
"""
import json
import re
from pathlib import Path

LEXICON_PATH = Path(__file__).parent / "lexicon" / "starter_v0.json"

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\u201c(])")
_TOKEN = re.compile(r"[a-z']+")
_NEGATION_WINDOW = 3


def load_lexicon(path: Path = LEXICON_PATH) -> dict:
    with open(path) as fh:
        raw = json.load(fh)
    return {
        "hawkish": [term.lower().split() for term in raw["hawkish"]],
        "dovish": [term.lower().split() for term in raw["dovish"]],
        "negators": set(raw["negators"]),
    }


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    return [s for s in _SENT_SPLIT.split(text) if len(s) > 1]


def _matches(tokens: list[str], term: list[str], negators: set[str]):
    """Yield +1 for each clean match of `term`, -1 if negated."""
    width = len(term)
    for i in range(len(tokens) - width + 1):
        if tokens[i:i + width] == term:
            window = tokens[max(0, i - _NEGATION_WINDOW):i]
            yield -1 if any(tok in negators for tok in window) else 1


def score_sentence(sentence: str, lex: dict) -> dict:
    tokens = _TOKEN.findall(sentence.lower())
    hawk = dove = 0
    for term in lex["hawkish"]:
        for hit in _matches(tokens, term, lex["negators"]):
            if hit == 1:
                hawk += 1
            else:
                dove += 1  # negated hawkish reads dovish
    for term in lex["dovish"]:
        for hit in _matches(tokens, term, lex["negators"]):
            if hit == 1:
                dove += 1
            else:
                hawk += 1  # negated dovish reads hawkish
    if hawk > dove:
        label = "hawkish"
    elif dove > hawk:
        label = "dovish"
    else:
        label = "neutral"
    return {"hawkish": hawk, "dovish": dove, "label": label}


def score_document(text: str, lex: dict | None = None) -> dict:
    lex = lex or load_lexicon()
    sentences = split_sentences(text)
    hawk = dove = scored = 0
    for sentence in sentences:
        result = score_sentence(sentence, lex)
        hawk += result["hawkish"]
        dove += result["dovish"]
        if result["label"] != "neutral":
            scored += 1
    total = hawk + dove
    net = (hawk - dove) / total if total else 0.0
    return {
        "n_sentences": len(sentences),
        "n_scored_sentences": scored,
        "hawkish_hits": hawk,
        "dovish_hits": dove,
        "net_hawkishness": round(net, 4),
    }
