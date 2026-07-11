"""First validation pass: does the A&BG index line up with the Bank's own
voting record?

Contemporaneous only - the index for a meeting's own minutes against that
same meeting's own skew/dissents/decision. Not a predictive (index_t vs
decision_t+1) test; that, and any OIS/market benchmark, is out of scope for
this pass (see DECISIONS.md / task scope: Stage 3).

Computes, with no scipy dependency (pure Python, matching the rest of the
pipeline):
- Pearson and Spearman correlation of abg_net_index with skew (r, n)
- Pearson and Spearman correlation of abg_net_index with net dissents
  (hawkish_dissents - dovish_dissents) (r, n)
- Mean abg_net_index grouped by decision (hike/hold/cut)

Run:  python -m pipeline.validate
"""
import csv
import json
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "data" / "index.json"
VOTES_PATH = ROOT / "data" / "votes.csv"
OUT = ROOT / "data" / "validation_v1.json"

DECISION_LABELS = {"increase": "hike", "maintain": "hold", "reduce": "cut"}


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


def load_corpus_by_published() -> dict[str, dict]:
    data = json.loads(INDEX_PATH.read_text())
    by_date = {}
    for d in data["documents"]:
        if d["published"] and d["decision"]:
            verb = d["decision"].split()[0].lower()
            by_date[d["published"]] = {
                "doc_id": d["doc_id"],
                "abg_net_index": d["abg_net_index"],
                "decision_label": DECISION_LABELS.get(verb),
            }
    return by_date


def load_votes_by_date() -> dict[str, dict]:
    by_date = {}
    with open(VOTES_PATH) as fh:
        for row in csv.DictReader(fh):
            by_date[row["meeting_date"]] = {
                "skew": float(row["skew"]),
                "net_dissents": int(row["hawkish_dissents"]) - int(row["dovish_dissents"]),
            }
    return by_date


def main() -> None:
    corpus = load_corpus_by_published()
    votes = load_votes_by_date()
    joined = [{**corpus[date], **votes[date], "date": date}
              for date in sorted(corpus) if date in votes]
    unmatched = sorted(set(corpus) - set(votes))
    print(f"joined {len(joined)} meetings; {len(unmatched)} corpus dates with no voting-sheet match: {unmatched}")

    index_vals = [r["abg_net_index"] for r in joined]
    skew_vals = [r["skew"] for r in joined]
    dissent_vals = [r["net_dissents"] for r in joined]

    corr_skew = {
        "pearson_r": pearson(index_vals, skew_vals),
        "spearman_r": spearman(index_vals, skew_vals),
        "n": len(joined),
    }
    corr_dissents = {
        "pearson_r": pearson(index_vals, dissent_vals),
        "spearman_r": spearman(index_vals, dissent_vals),
        "n": len(joined),
    }

    by_decision = {}
    for label in ("hike", "hold", "cut"):
        vals = [r["abg_net_index"] for r in joined if r["decision_label"] == label]
        by_decision[label] = {
            "mean_abg_net_index": round(st.mean(vals), 4) if vals else None,
            "n": len(vals),
        }

    payload = {
        "schema": "validation-v1",
        "n_joined_meetings": len(joined),
        "unmatched_corpus_dates": unmatched,
        "corr_abg_index_vs_skew": corr_skew,
        "corr_abg_index_vs_net_dissents": corr_dissents,
        "mean_abg_index_by_decision": by_decision,
        "notes": "Contemporaneous only (meeting's own minutes vs that meeting's own vote/decision), not predictive of the next meeting. See DECISIONS.md.",
    }
    for key in ("corr_abg_index_vs_skew", "corr_abg_index_vs_net_dissents"):
        for stat in ("pearson_r", "spearman_r"):
            if payload[key][stat] is not None:
                payload[key][stat] = round(payload[key][stat], 4)

    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {OUT}")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
