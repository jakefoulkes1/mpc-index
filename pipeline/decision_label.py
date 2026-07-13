"""Classifies a corpus document's `decision` text into {hike, hold, cut}.

Finds the verb immediately adjacent to "Bank Rate", not just the first
word of the decision string. A handful of decisions are compound
sentences where something else (e.g. asset purchases) is mentioned first
and the Bank Rate action second - "increase the Bank of England's
holdings of ... and to reduce Bank Rate by 15 basis points to 0.1%"
(minutes-2020-03-19-special) is genuinely a CUT, but its first word is
"increase". First-word classification silently mislabels any such
document; this is the one classifier used everywhere a document needs a
hike/hold/cut label (pipeline/validate.py, pipeline/build_market_history.py
sanity checks, the ladder in pipeline/ladder.py, index.html's chart
markers) so there is exactly one place this can go wrong, not several
copies that can drift. See DECISIONS.md, 2026-07-11.
"""
import re

DECISION_LABELS = {"increase": "hike", "maintain": "hold", "reduce": "cut"}
BANK_RATE_VERB_RE = re.compile(r"(increase|reduce|maintain)\w*\s+Bank Rate", re.IGNORECASE)


def classify_decision(decision_text: str | None) -> str | None:
    if not decision_text:
        return None
    m = BANK_RATE_VERB_RE.search(decision_text)
    if not m:
        return None
    return DECISION_LABELS.get(m.group(1).lower())
