import json
from pathlib import Path

import pytest

from pipeline.inspect import (
    find_matches,
    raw_text_path,
    term_report,
    vs_trailing_report,
)
from pipeline.score.abg import load_abg_lexicon, score_document

ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = ROOT / "data" / "index.json"


def test_find_matches_reconciles_with_score_document_on_synthetic_text():
    """Portable check (no dependency on local raw text files): the
    inspector's per-match walk must always agree with abg.score_document's
    aggregate counts, since both use the same tokeniser and lexicon."""
    text = "Higher inflation and stronger growth are expected, alongside weaker growth."
    lex = load_abg_lexicon()
    matches = find_matches(text, lex)
    scored = score_document(text, lex)

    hawk = sum(1 for m in matches if m["polarity"] == "hawkish")
    dove = sum(1 for m in matches if m["polarity"] == "dovish")
    assert hawk == scored["abg_hawk"]
    assert dove == scored["abg_dove"]


def _first_doc_with_local_raw_text():
    if not INDEX_PATH.exists():
        return None
    data = json.loads(INDEX_PATH.read_text())
    docs_sorted = sorted((d for d in data["documents"] if d["published"]), key=lambda d: d["published"])
    for doc in reversed(docs_sorted):
        if raw_text_path(doc).exists():
            return doc["doc_id"]
    return None


def test_term_report_reconciles_with_index_json_on_real_corpus():
    doc_id = _first_doc_with_local_raw_text()
    if doc_id is None:
        pytest.skip("no local raw text files available in this checkout (data/raw/ is gitignored)")

    data = json.loads(INDEX_PATH.read_text())
    doc = next(d for d in data["documents"] if d["doc_id"] == doc_id)

    report = term_report(doc_id)
    assert report["hawk_count"] == doc["abg_hawk"]
    assert report["dove_count"] == doc["abg_dove"]
    assert sum(report["by_phrase"].values()) == doc["abg_hawk"] + doc["abg_dove"]


def test_vs_trailing_report_shape_on_real_corpus():
    doc_id = _first_doc_with_local_raw_text()
    if doc_id is None:
        pytest.skip("no local raw text files available in this checkout (data/raw/ is gitignored)")

    data = json.loads(INDEX_PATH.read_text())
    docs_sorted = sorted((d for d in data["documents"] if d["published"]), key=lambda d: d["published"])
    dates = [d["published"] for d in docs_sorted]
    doc = next(d for d in data["documents"] if d["doc_id"] == doc_id)
    idx = dates.index(doc["published"])
    if idx < 4 or not all(raw_text_path(d).exists() for d in docs_sorted[idx - 4:idx]):
        pytest.skip("not enough local raw text files for a 4-document trailing comparison")

    report = vs_trailing_report(doc_id, 4)
    assert report["n_trailing"] == 4
    for row in report["rows"]:
        assert row["delta"] == pytest.approx(row["current"] - row["trailing_avg"], abs=0.01)
