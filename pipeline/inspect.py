"""Evidence inspector: for a given corpus document, shows exactly which
A&BG terms fired, where, and how the document's index compares to its
recent trailing average. Drafting material for Jake - never published to
the site, never read by index.html.

Read-only: imports the scorer's own tokenisation and lexicon loader from
pipeline/score/abg.py (never reimplemented here), and the sentence
splitter from pipeline/score/dictionary.py for display snippets only -
the scoring algorithm itself is untouched. See DECISIONS.md for the
"trailing N" convention used here (strictly the N documents BEFORE the
target, deliberately different from pipeline/predict/lock.py's own
"last N including current" convention, which is off-limits this session
and left unchanged).

Run:
    python -m pipeline.inspect <doc_id>
    python -m pipeline.inspect <doc_id> --vs-trailing 4
"""
import argparse
import json
from collections import Counter
from pathlib import Path

from pipeline.score.abg import _TOKEN, _noun_matches_at, load_abg_lexicon
from pipeline.score.dictionary import split_sentences

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "data" / "index.json"
RAW_DIR = ROOT / "data" / "raw"

TOP_N_SNIPPETS = 10


def load_index() -> dict:
    return json.loads(INDEX_PATH.read_text())


def find_doc(data: dict, doc_id: str) -> dict:
    for d in data["documents"]:
        if d["doc_id"] == doc_id:
            return d
    raise ValueError(f"HARD STOP: no document with doc_id {doc_id!r} in data/index.json")


def raw_text_path(doc: dict) -> Path:
    """Reconstructs the raw filename from doc_id - index.json doesn't store
    the raw filename directly, so this mirrors the naming build_index.py
    already uses (checked against data/raw/ in this checkout)."""
    parts = doc["doc_id"].split("-")
    if doc["type"] == "special_minutes":
        # doc_id: minutes-YYYY-MM-DD-special -> raw: YYYY-MM-DD-special-minutes.txt
        return RAW_DIR / f"{parts[1]}-{parts[2]}-{parts[3]}-special-minutes.txt"
    # doc_id: minutes-YYYY-MM -> raw: YYYY-MM-minutes.txt
    return RAW_DIR / f"{parts[1]}-{parts[2]}-minutes.txt"


def find_matches(text: str, lex: dict) -> list[dict]:
    """Same algorithm and same token order as pipeline.score.abg.score_document
    (tokenise whole doc, walk adjacent adjective+noun pairs) - but returns every
    individual match (phrase, polarity, token position) instead of just the
    aggregate hawk/dove tally, so results reconcile exactly with index.json."""
    tokens = _TOKEN.findall(text.lower())
    matches = []
    for i in range(len(tokens) - 1):
        token = tokens[i]
        is_hawk_adj = any(token.startswith(stem) for stem in lex["hawkish_adjectives"])
        is_dove_adj = any(token.startswith(stem) for stem in lex["dovish_adjectives"])
        if not is_hawk_adj and not is_dove_adj:
            continue
        for noun in lex["nouns"]:
            if _noun_matches_at(tokens, i + 1, noun):
                phrase = " ".join([token] + list(tokens[i + 1:i + 1 + len(noun)]))
                matches.append({
                    "phrase": phrase,
                    "polarity": "hawkish" if is_hawk_adj else "dovish",
                    "token_index": i,
                })
                break
    return matches


def sentence_lookup(sentences: list[str]) -> list[int]:
    """document-level token index -> sentence index, for snippet lookup.
    _TOKEN.findall is insensitive to whitespace (it only extracts word
    characters), and split_sentences' own whitespace normalisation doesn't
    change token content or order - so concatenating each sentence's token
    count reconstructs the same token order as tokenising the whole text."""
    lookup = []
    for sent_idx, sentence in enumerate(sentences):
        lookup.extend([sent_idx] * len(_TOKEN.findall(sentence.lower())))
    return lookup


def _trailing_docs(docs_sorted: list[dict], doc: dict, n_trailing: int) -> list[dict]:
    """The n_trailing documents strictly BEFORE doc, by published date."""
    dates = [d["published"] for d in docs_sorted]
    idx = dates.index(doc["published"])
    return docs_sorted[max(0, idx - n_trailing):idx]


def term_report(doc_id: str) -> dict:
    data = load_index()
    doc = find_doc(data, doc_id)
    path = raw_text_path(doc)
    if not path.exists():
        raise ValueError(
            f"HARD STOP: raw text for {doc_id} not found at {path} - "
            f"raw texts are gitignored/local-only, re-run the backfill first."
        )
    text = path.read_text()
    lex = load_abg_lexicon()
    matches = find_matches(text, lex)

    hawk_count = sum(1 for m in matches if m["polarity"] == "hawkish")
    dove_count = sum(1 for m in matches if m["polarity"] == "dovish")
    if hawk_count != doc["abg_hawk"] or dove_count != doc["abg_dove"]:
        raise ValueError(
            f"HARD STOP: inspector counts ({hawk_count} hawkish, {dove_count} dovish) "
            f"don't reconcile with index.json's abg_hawk/abg_dove "
            f"({doc['abg_hawk']}, {doc['abg_dove']}) for {doc_id} - "
            f"the inspector has drifted from the scorer, investigate before trusting this output."
        )

    sentences = split_sentences(text)
    lookup = sentence_lookup(sentences)

    by_phrase = Counter()
    polarity_of = {}
    snippet_of = {}
    for m in matches:
        by_phrase[m["phrase"]] += 1
        polarity_of[m["phrase"]] = m["polarity"]
        if m["phrase"] not in snippet_of and m["token_index"] < len(lookup):
            snippet_of[m["phrase"]] = sentences[lookup[m["token_index"]]]

    docs_sorted = sorted((d for d in data["documents"] if d["published"]), key=lambda d: d["published"])
    trailing = _trailing_docs(docs_sorted, doc, 4)
    trailing_mean = sum(d["abg_net_index"] for d in trailing) / len(trailing) if trailing else None

    return {
        "doc_id": doc_id,
        "index_value": doc["abg_net_index"],
        "trailing_mean": round(trailing_mean, 4) if trailing_mean is not None else None,
        "trailing_n": len(trailing),
        "trailing_doc_ids": [d["doc_id"] for d in trailing],
        "hawk_count": hawk_count,
        "dove_count": dove_count,
        "by_phrase": by_phrase,
        "polarity_of": polarity_of,
        "snippet_of": snippet_of,
    }


def vs_trailing_report(doc_id: str, n_trailing: int = 4) -> dict:
    data = load_index()
    doc = find_doc(data, doc_id)
    docs_sorted = sorted((d for d in data["documents"] if d["published"]), key=lambda d: d["published"])
    trailing_docs = _trailing_docs(docs_sorted, doc, n_trailing)
    if not trailing_docs:
        raise ValueError(f"HARD STOP: {doc_id} has no prior documents to compare against")

    lex = load_abg_lexicon()
    current_path = raw_text_path(doc)
    if not current_path.exists():
        raise ValueError(f"HARD STOP: raw text for {doc_id} not found at {current_path}")
    current_counts = Counter(m["phrase"] for m in find_matches(current_path.read_text(), lex))

    trailing_counts_per_doc = []
    for td in trailing_docs:
        p = raw_text_path(td)
        if not p.exists():
            raise ValueError(f"HARD STOP: raw text for {td['doc_id']} not found at {p}")
        trailing_counts_per_doc.append(Counter(m["phrase"] for m in find_matches(p.read_text(), lex)))

    all_phrases = set(current_counts)
    for c in trailing_counts_per_doc:
        all_phrases |= set(c)

    rows = []
    for phrase in all_phrases:
        current_n = current_counts.get(phrase, 0)
        avg_prior = sum(c.get(phrase, 0) for c in trailing_counts_per_doc) / len(trailing_counts_per_doc)
        rows.append({
            "phrase": phrase,
            "current": current_n,
            "trailing_avg": round(avg_prior, 2),
            "delta": round(current_n - avg_prior, 2),
        })
    rows.sort(key=lambda r: (-abs(r["delta"]), r["phrase"]))

    return {
        "doc_id": doc_id,
        "n_trailing": len(trailing_docs),
        "trailing_doc_ids": [d["doc_id"] for d in trailing_docs],
        "rows": rows,
    }


def format_term_report(report: dict) -> str:
    lines = []
    lines.append(f"=== Evidence inspector: {report['doc_id']} ===")
    lines.append("")
    lines.append(f"A&BG index: {report['index_value']}")
    if report["trailing_mean"] is not None:
        lines.append(
            f"Trailing {report['trailing_n']}-document mean: {report['trailing_mean']} "
            f"(docs: {', '.join(report['trailing_doc_ids'])})"
        )
    else:
        lines.append("Trailing mean: n/a (no prior documents)")
    lines.append(f"Total hits: {report['hawk_count']} hawkish, {report['dove_count']} dovish")
    lines.append("")

    lines.append("-- All terms fired --")
    for phrase, count in report["by_phrase"].most_common():
        polarity = report["polarity_of"][phrase]
        lines.append(f"  [{polarity:>8}] {phrase!r}: {count}")
    lines.append("")

    lines.append(f"-- Top {TOP_N_SNIPPETS} terms, in-context snippet --")
    for phrase, count in report["by_phrase"].most_common(TOP_N_SNIPPETS):
        polarity = report["polarity_of"][phrase]
        snippet = report["snippet_of"].get(phrase, "(snippet not found)")
        lines.append(f"  [{polarity:>8}] {phrase!r} (x{count}):")
        lines.append(f"      \"{snippet.strip()}\"")
    return "\n".join(lines)


def format_vs_trailing_report(report: dict) -> str:
    lines = []
    lines.append(f"=== Comparison vs trailing {report['n_trailing']} documents: {report['doc_id']} ===")
    lines.append(f"Trailing docs: {', '.join(report['trailing_doc_ids'])}")
    lines.append("")
    lines.append(f"{'term':<30} {'current':>8} {'trailing avg':>13} {'delta':>8}")
    for row in report["rows"]:
        lines.append(f"{row['phrase']:<30} {row['current']:>8} {row['trailing_avg']:>13} {row['delta']:>8}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Evidence inspector for an A&BG-scored document.")
    parser.add_argument("doc_id")
    parser.add_argument("--vs-trailing", type=int, default=None, metavar="N",
                         help="show a comparison table of term frequency vs the prior N documents' average")
    args = parser.parse_args()

    if args.vs_trailing is not None:
        print(format_vs_trailing_report(vs_trailing_report(args.doc_id, args.vs_trailing)))
    else:
        print(format_term_report(term_report(args.doc_id)))


if __name__ == "__main__":
    main()
