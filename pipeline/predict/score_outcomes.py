"""After an MPC announcement, fills a prediction file's `outcome` and
`scores` fields with Brier and log scores for m0_market_only and an
always-hold reference forecast (a fixed p_hold=1 forecast - the baseline
any real forecast needs to beat, since holds are the most common outcome).

Brier score (3-class): sum over {hike, hold, cut} of (p_i - o_i)^2, where
o_i is 1 for the actual outcome and 0 otherwise. Range [0, 2]; 0 is
perfect. Log score: -log(p_actual_outcome); lower is better, unbounded
above (floored at a small epsilon to avoid -log(0)).

Run:  python -m pipeline.predict.score_outcomes <prediction-file.json> <outcome: hike|hold|cut>
"""
import json
import math
import sys
from pathlib import Path

OUTCOMES = ("hike", "hold", "cut")
ALWAYS_HOLD = {"p_hike": 0.0, "p_hold": 1.0, "p_cut": 0.0}
LOG_SCORE_EPSILON = 1e-9


def brier_score(probs: dict, outcome: str) -> float:
    return sum((probs[f"p_{o}"] - (1.0 if o == outcome else 0.0)) ** 2 for o in OUTCOMES)


def log_score(probs: dict, outcome: str) -> float:
    p = max(probs[f"p_{outcome}"], LOG_SCORE_EPSILON)
    return -math.log(p)


def score_forecast(probs: dict, outcome: str) -> dict:
    return {
        "brier_score": round(brier_score(probs, outcome), 4),
        "log_score": round(log_score(probs, outcome), 4),
    }


def fill_outcome(payload: dict, outcome: str) -> dict:
    if outcome not in OUTCOMES:
        raise ValueError(f"outcome must be one of {OUTCOMES}, got {outcome!r}")
    m0_probs = {k: payload["m0_market_only"][k] for k in ("p_hike", "p_hold", "p_cut")}
    payload["outcome"] = outcome
    payload["scores"] = {
        "m0_market_only": score_forecast(m0_probs, outcome),
        "always_hold_reference": score_forecast(ALWAYS_HOLD, outcome),
    }
    return payload


def main() -> None:
    if len(sys.argv) != 3:
        print("usage: python -m pipeline.predict.score_outcomes <prediction-file.json> <outcome: hike|hold|cut>")
        sys.exit(1)
    path = Path(sys.argv[1])
    payload = fill_outcome(json.loads(path.read_text()), sys.argv[2])
    path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"updated {path}")
    print(json.dumps(payload["scores"], indent=2))


if __name__ == "__main__":
    main()
