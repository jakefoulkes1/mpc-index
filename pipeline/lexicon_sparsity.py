"""Read-only lexicon-sparsity statistic for the methodology page.

Computes, per corpus document, total_hits = abg_hawk + abg_dove (the number
of A&BG lexicon bigram matches the scorer found in that document), and
reports the median and interquartile range across the whole corpus. This
quantifies the documented "sparse lexicon hits" limitation: the Net Index
for a document rests on however many matches these are.

Reads data/index.json only. Writes nothing, modifies nothing - the numbers
are quoted (with this script cited) on methodology.html#limitations.

Quartile convention: statistics.quantiles(n=4, method="inclusive") (the
median-inclusive/Tukey convention); IQR = Q3 - Q1.

Governed by DECISIONS.md: 2026-07-12 (final polish - lexicon sparsity
published).

Run:  python -m pipeline.lexicon_sparsity
"""
import json
import statistics
from pathlib import Path

INDEX_PATH = Path(__file__).resolve().parent.parent / "data" / "index.json"


def sparsity_summary(documents: list[dict]) -> dict:
    """median/Q1/Q3/IQR of (abg_hawk + abg_dove) across the given documents."""
    hits = sorted(d["abg_hawk"] + d["abg_dove"] for d in documents)
    q1, med, q3 = statistics.quantiles(hits, n=4, method="inclusive")
    return {
        "n_documents": len(hits),
        "median_total_hits": med,
        "q1": q1,
        "q3": q3,
        "iqr": q3 - q1,
        "min": hits[0],
        "max": hits[-1],
    }


def main() -> None:
    corpus = json.loads(INDEX_PATH.read_text())
    s = sparsity_summary(corpus["documents"])
    print(f"n documents:        {s['n_documents']}")
    print(f"median total hits:  {s['median_total_hits']:g}")
    print(f"Q1 / Q3:            {s['q1']:g} / {s['q3']:g}")
    print(f"IQR:                {s['iqr']:g}")
    print(f"min / max:          {s['min']} / {s['max']}")


if __name__ == "__main__":
    main()
