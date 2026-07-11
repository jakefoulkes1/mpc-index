"""First validation pass: does the A&BG index line up with the Bank's own
voting record?

Contemporaneous only - the index for a meeting's own minutes against that
same meeting's own skew/dissents/decision. Not a predictive (index_t vs
decision_t+1) test; that, and any OIS/market benchmark, is out of scope for
this pass (see DECISIONS.md / task scope: Stage 3).

Join key: the voting sheet's own announcement date is canonical (it is a
single, consistent convention), not our own `published` field (meeting_end
+ 1 day, a uniform rule that is off by 1 day for a handful of real
documents - 3 weekend/holiday slippages plus the 19 March 2020 special,
which was announced same-day rather than the next day - see
DECISIONS.md). Each corpus document is matched to its NEAREST voting-sheet
date within a small tolerance; every document that can't be matched within
tolerance is excluded and individually logged, not silently dropped.

Computes, with no scipy dependency (pure Python, matching the rest of the
pipeline):
- Pearson and Spearman correlation of abg_net_index with skew (r, n)
- Pearson and Spearman correlation of abg_net_index with net dissents
  (hawkish_dissents - dovish_dissents) (r, n)
- The same two correlations for delta_index (change in abg_net_index since
  the previous document in the corpus), not just the level.
- Mean abg_net_index grouped by decision (hike/hold/cut)

Run:  python -m pipeline.validate
"""
import csv
import datetime as dt
import json
import statistics as st
from pathlib import Path

from pipeline.decision_label import classify_decision

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "data" / "index.json"
VOTES_PATH = ROOT / "data" / "votes.csv"
OUT = ROOT / "data" / "validation_v1.json"

# Largest known real gap is 1 day (see DECISIONS.md); allow a little more
# headroom before treating a document as unmatched.
MAX_DAY_TOLERANCE = 3


def pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 2 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return None
    mx, my = st.mean(xs), st.mean(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sx = (sum((x - mx) ** 2 for x in xs)) ** 0.5
    sy = (sum((y - my) ** 2 for y in ys)) ** 0.5
    return cov / (sx * sy)


def rank(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1
    return ranks


def spearman(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 2:
        return None
    return pearson(rank(xs), rank(ys))


def corr_pair(xs: list[float], ys: list[float]) -> dict:
    return {
        "pearson_r": round(r, 4) if (r := pearson(xs, ys)) is not None else None,
        "spearman_r": round(r, 4) if (r := spearman(xs, ys)) is not None else None,
        "n": len(xs),
    }


def load_corpus_documents() -> list[dict]:
    """All documents with both a published date and a parsed decision,
    in published order, with delta_index vs the previous document in that
    order (not the previous *matched* one - the corpus's own sequence)."""
    data = json.loads(INDEX_PATH.read_text())
    docs = sorted(
        (d for d in data["documents"] if d["published"] and d["decision"]),
        key=lambda d: d["published"],
    )
    prev_index = None
    out = []
    for d in docs:
        delta = d["abg_net_index"] - prev_index if prev_index is not None else None
        out.append({
            "doc_id": d["doc_id"],
            "published": d["published"],
            "abg_net_index": d["abg_net_index"],
            "delta_index": delta,
            "decision_label": classify_decision(d["decision"]),
        })
        prev_index = d["abg_net_index"]
    return out


def load_votes_by_date() -> dict[str, dict]:
    by_date = {}
    with open(VOTES_PATH) as fh:
        for row in csv.DictReader(fh):
            by_date[row["meeting_date"]] = {
                "skew": float(row["skew"]),
                "net_dissents": int(row["hawkish_dissents"]) - int(row["dovish_dissents"]),
            }
    return by_date


def join_to_votes(docs: list[dict], votes: dict[str, dict]) -> tuple[list[dict], list[dict]]:
    vote_dates = sorted(dt.date.fromisoformat(d) for d in votes)
    joined, unmatched = [], []
    for doc in docs:
        pub = dt.date.fromisoformat(doc["published"])
        nearest = min(vote_dates, key=lambda v: abs((v - pub).days))
        gap = abs((nearest - pub).days)
        if gap > MAX_DAY_TOLERANCE:
            unmatched.append({"doc_id": doc["doc_id"], "published": doc["published"],
                               "nearest_votes_date": nearest.isoformat(), "gap_days": gap})
            continue
        joined.append({**doc, **votes[nearest.isoformat()], "votes_date": nearest.isoformat(), "gap_days": gap})
    return joined, unmatched


def main() -> None:
    docs = load_corpus_documents()
    votes = load_votes_by_date()
    joined, unmatched = join_to_votes(docs, votes)

    print(f"joined {len(joined)} of {len(docs)} candidate documents (published + decision) "
          f"to a voting-sheet row within {MAX_DAY_TOLERANCE} day(s)")
    for u in unmatched:
        print(f"log: {u['doc_id']}: no voting-sheet row within {MAX_DAY_TOLERANCE} day(s) "
              f"(published {u['published']}, nearest sheet date {u['nearest_votes_date']}, "
              f"{u['gap_days']} day(s) away) - excluded from validation")

    level_rows = joined
    delta_rows = [r for r in joined if r["delta_index"] is not None]

    corr = {
        "level_vs_skew": corr_pair([r["abg_net_index"] for r in level_rows], [r["skew"] for r in level_rows]),
        "level_vs_net_dissents": corr_pair([r["abg_net_index"] for r in level_rows], [r["net_dissents"] for r in level_rows]),
        "delta_vs_skew": corr_pair([r["delta_index"] for r in delta_rows], [r["skew"] for r in delta_rows]),
        "delta_vs_net_dissents": corr_pair([r["delta_index"] for r in delta_rows], [r["net_dissents"] for r in delta_rows]),
    }

    by_decision = {}
    for label in ("hike", "hold", "cut"):
        vals = [r["abg_net_index"] for r in joined if r["decision_label"] == label]
        by_decision[label] = {
            "mean_abg_net_index": round(st.mean(vals), 4) if vals else None,
            "n": len(vals),
        }

    payload = {
        "schema": "validation-v2",
        "join_key": "voting-sheet announcement date, nearest match within tolerance",
        "max_day_tolerance": MAX_DAY_TOLERANCE,
        "n_candidate_documents": len(docs),
        "n_joined_meetings": len(joined),
        "unmatched_documents": unmatched,
        "correlations": corr,
        "mean_abg_index_by_decision": by_decision,
        "notes": "Contemporaneous only (meeting's own minutes vs that meeting's own vote/decision), not predictive of the next meeting. delta_index is abg_net_index minus the previous document's, in corpus order. See DECISIONS.md.",
    }

    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {OUT}")
    print(json.dumps({"correlations": corr, "mean_abg_index_by_decision": by_decision}, indent=2))


if __name__ == "__main__":
    main()
