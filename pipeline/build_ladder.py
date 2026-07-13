"""Runs the expanding-window benchmark ladder (L0-L4) and writes
data/ladder_v1.json. See pipeline/ladder.py for every model's definition
and DECISIONS.md (2026-07-11) for the modelling choices.

NOT published to the site - results get reviewed before display, per
instruction.

Run:  python -m pipeline.build_ladder
"""
import json
import statistics as st
from pathlib import Path

from pipeline.ladder import (
    EVAL_START,
    l0_always_hold,
    l1_market_only,
    l2_market_logit,
    l3_market_index_skew_logit,
    l4_member_simulation,
    load_raw_votes,
    load_records,
)
from pipeline.predict.score_outcomes import LOG_SCORE_EPSILON, brier_score, log_score

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "ladder_v1.json"
MODELS = ("L0", "L1", "L2", "L3", "L4")


def run_evaluation(records: list[dict] | None = None, votes_by_date: dict | None = None,
                    eval_start: str = EVAL_START) -> dict:
    """records/votes_by_date default to the real data; pass fixtures (as
    in pipeline/tests/test_build_ladder.py) to run reproducibly without
    the full live corpus."""
    if records is None:
        records = load_records()
    if votes_by_date is None:
        votes_by_date = load_raw_votes()
    eval_indices = [i for i, r in enumerate(records) if r["date"] >= eval_start]

    per_meeting = []
    fallback_log = []
    for i in eval_indices:
        target = records[i]
        train = records[:i]
        actual = target["outcome"]

        preds = {"L0": l0_always_hold(train, target), "L1": l1_market_only(train, target)}

        l2_probs, l2_status = l2_market_logit(train, target)
        if l2_probs is None:
            fallback_log.append(f"{target['doc_id']}: L2 fell back to L1 ({l2_status})")
            l2_probs = preds["L1"]
        preds["L2"] = l2_probs

        l3_probs, l3_status = l3_market_index_skew_logit(records, i, i)
        if l3_probs is None:
            fallback_log.append(f"{target['doc_id']}: L3 fell back to L1 ({l3_status})")
            l3_probs = preds["L1"]
        preds["L3"] = l3_probs

        l4_probs = l4_member_simulation(votes_by_date, target)
        if l4_probs is None:
            fallback_log.append(f"{target['doc_id']}: L4 fell back to L1 (no voting-record match for this meeting)")
            l4_probs = preds["L1"]
        preds["L4"] = l4_probs

        per_meeting.append({
            "doc_id": target["doc_id"], "date": target["date"], "scheduled": target["scheduled"],
            "actual": actual, "predictions": preds,
        })

    for line in fallback_log:
        print("log:", line)

    return {"per_meeting": per_meeting, "fallback_log": fallback_log}


def score_models(per_meeting: list[dict]) -> dict:
    if not per_meeting:
        return {model: {"mean_brier": None, "mean_log_score": None, "n": 0} for model in MODELS}
    scores = {}
    for model in MODELS:
        briers = [brier_score(m["predictions"][model], m["actual"]) for m in per_meeting]
        logs = [log_score(m["predictions"][model], m["actual"]) for m in per_meeting]
        scores[model] = {
            "mean_brier": round(st.mean(briers), 4),
            "mean_log_score": round(st.mean(logs), 4),
            "n": len(briers),
        }
    l1_brier = scores["L1"]["mean_brier"]
    for model in ("L2", "L3", "L4"):
        scores[model]["skill_vs_l1"] = round(1 - scores[model]["mean_brier"] / l1_brier, 4) if l1_brier else None
    return scores


def print_table(title: str, scores: dict) -> None:
    print(f"\n{title}")
    print(f"{'model':6}{'mean_brier':13}{'mean_log':11}{'skill_vs_L1':13}{'n':5}")
    for model in MODELS:
        s = scores[model]
        if s["n"] == 0:
            print(f"{model:6}{'-':<13}{'-':<11}{'-':<13}{0:<5}")
            continue
        skill = f"{s['skill_vs_l1']:.4f}" if s.get("skill_vs_l1") is not None else "-"
        print(f"{model:6}{s['mean_brier']:<13}{s['mean_log_score']:<11}{skill:<13}{s['n']:<5}")


def main() -> None:
    result = run_evaluation()
    per_meeting = result["per_meeting"]
    scheduled_only = [m for m in per_meeting if m["scheduled"]]
    specials_only = [m for m in per_meeting if not m["scheduled"]]

    headline_scores = score_models(scheduled_only)
    specials_scores = score_models(specials_only)

    payload = {
        "schema": "ladder-v1",
        "eval_start": EVAL_START,
        "n_meetings": len(per_meeting),
        "n_scheduled": len(scheduled_only),
        "n_specials": len(specials_only),
        "log_score_probability_clip": LOG_SCORE_EPSILON,
        "headline_scores_scheduled_only": headline_scores,
        "specials_robustness_scores": specials_scores,
        "fallback_log": result["fallback_log"],
        "per_meeting": per_meeting,
        "notes": ("3-class outcomes coded by sign only (a 50bp+ move counts the same as a "
                  "smaller move in the same direction). L3's index_level and skew are both "
                  "the PREVIOUS meeting's values, not the target's own - see DECISIONS.md, "
                  "2026-07-11, for why. HEADLINE evaluation is scheduled meetings only - "
                  "special/emergency meetings (e.g. the March 2020 Covid cuts) could not have "
                  "been pre-registered forecasts, since at lock time nobody knew they'd occur; "
                  "they're reported separately as a robustness check, not blended into the "
                  "headline. log_score_probability_clip is the floor applied to p(actual "
                  "outcome) before taking -log(p), to avoid -log(0) for a confidently-wrong "
                  "call - see pipeline/predict/score_outcomes.py. NOT published to the site - "
                  "for review first."),
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")

    print(f"\nwrote {OUT} ({len(per_meeting)} evaluation meetings: "
          f"{len(scheduled_only)} scheduled, {len(specials_only)} special; "
          f"{len(result['fallback_log'])} fallbacks; log_score_probability_clip={LOG_SCORE_EPSILON})")
    print_table("HEADLINE (scheduled meetings only):", headline_scores)
    print_table("Specials robustness line (NOT blended into headline):", specials_scores)


if __name__ == "__main__":
    main()
