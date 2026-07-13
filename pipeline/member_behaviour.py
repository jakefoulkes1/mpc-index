"""Descriptive member-behaviour table: how does each MPC member vote relative
to the decided rate, and how sticky is dissent from one meeting to the next?

Descriptive counts only - no modelling, no prediction. Seeds Stage 4's
member-level predictor (not built here).

States, per member-meeting (from data/votes.csv):
- hawkish_dissent: preferred_rate > decided_rate
- dovish_dissent:  preferred_rate < decided_rate
- with_majority:   preferred_rate == decided_rate

The transition matrix is P(state at a member's NEXT voted meeting | state
now), pooled across all members (not per-member - most members have too few
meetings to split further without n per cell becoming meaningless).

Governed by DECISIONS.md: 2026-07-11 (member-behaviour table, seeds
Stage 4).

Run:  python -m pipeline.member_behaviour
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOTES_PATH = ROOT / "data" / "votes.csv"
OUT = ROOT / "data" / "member_behaviour_v1.json"

STATES = ("hawkish_dissent", "with_majority", "dovish_dissent")
DISSENT_STATES = ("hawkish_dissent", "dovish_dissent")


def classify(preferred: float, decided: float) -> str:
    if preferred > decided:
        return "hawkish_dissent"
    if preferred < decided:
        return "dovish_dissent"
    return "with_majority"


def load_member_votes() -> dict[str, list[tuple[str, str]]]:
    """member -> [(meeting_date, state), ...] in chronological order."""
    rows = defaultdict(list)
    with open(VOTES_PATH) as fh:
        for row in csv.DictReader(fh):
            state = classify(float(row["preferred_rate"]), float(row["decided_rate"]))
            rows[row["member"]].append((row["meeting_date"], state))
    for member in rows:
        rows[member].sort(key=lambda r: r[0])
    return rows


def dissent_frequency(member_votes: dict[str, list[tuple[str, str]]]) -> dict[str, dict]:
    out = {}
    for member, votes in member_votes.items():
        n = len(votes)
        hawkish = sum(1 for _, s in votes if s == "hawkish_dissent")
        dovish = sum(1 for _, s in votes if s == "dovish_dissent")
        out[member] = {
            "n_meetings": n,
            "dissent_frequency": round((hawkish + dovish) / n, 4) if n else None,
            "hawkish_dissent_frequency": round(hawkish / n, 4) if n else None,
            "dovish_dissent_frequency": round(dovish / n, 4) if n else None,
        }
    return out


def transition_counts(member_votes: dict[str, list[tuple[str, str]]]) -> dict[str, dict[str, int]]:
    counts = {s: {t: 0 for t in STATES} for s in STATES}
    for votes in member_votes.values():
        for (_, s_now), (_, s_next) in zip(votes, votes[1:]):
            counts[s_now][s_next] += 1
    return counts


def transition_matrix(counts: dict[str, dict[str, int]]) -> dict:
    matrix = {}
    for s_now in STATES:
        total = sum(counts[s_now].values())
        matrix[s_now] = {
            "n": total,
            "probabilities": {t: round(counts[s_now][t] / total, 4) if total else None for t in STATES},
            "counts": counts[s_now],
        }
    return matrix


def dissent_stickiness(counts: dict[str, dict[str, int]]) -> dict:
    """P(dissenting again next time | dissenting now), collapsing hawkish
    and dovish dissent into one "dissent" state for a single headline
    number - the finer 3-state matrix above keeps the direction split."""
    dissent_to_dissent = sum(counts[s_now][t] for s_now in DISSENT_STATES for t in DISSENT_STATES)
    dissent_total = sum(sum(counts[s_now].values()) for s_now in DISSENT_STATES)
    majority_to_dissent = sum(counts["with_majority"][t] for t in DISSENT_STATES)
    majority_total = sum(counts["with_majority"].values())
    return {
        "p_dissent_again_given_dissented": round(dissent_to_dissent / dissent_total, 4) if dissent_total else None,
        "n_given_dissented": dissent_total,
        "p_dissent_given_with_majority": round(majority_to_dissent / majority_total, 4) if majority_total else None,
        "n_given_with_majority": majority_total,
    }


def main() -> None:
    member_votes = load_member_votes()
    freq = dissent_frequency(member_votes)
    counts = transition_counts(member_votes)
    matrix = transition_matrix(counts)
    stickiness = dissent_stickiness(counts)

    payload = {
        "schema": "member-behaviour-v1",
        "notes": ("Descriptive counts only, no modelling. States: hawkish_dissent "
                  "(preferred > decided), with_majority (preferred == decided), "
                  "dovish_dissent (preferred < decided). Transition matrix is P(state "
                  "at a member's NEXT voted meeting | state now), pooled across all "
                  "members. Seeds Stage 4's member-level predictor; not a predictor "
                  "itself."),
        "member_dissent_frequency": dict(
            sorted(freq.items(), key=lambda kv: -(kv[1]["dissent_frequency"] or 0))
        ),
        "transition_matrix": matrix,
        "dissent_stickiness": stickiness,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {OUT}")
    print(json.dumps({"transition_matrix": matrix, "dissent_stickiness": stickiness}, indent=2))


if __name__ == "__main__":
    main()
