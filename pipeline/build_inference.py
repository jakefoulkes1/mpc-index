"""Runs the full headline inference (Spec 3 OLS + Spec 2 ordered-logit LR
test, full sample and a Sep 2023-present fragility check) and writes
data/inference_v1.json. See pipeline/inference.py and DECISIONS.md
(2026-07-11) for every modelling choice.

NOT published to the site - per instruction, for review first.

Run:  python -m pipeline.build_inference
"""
import json
from pathlib import Path

from pipeline.inference import (
    NEWEY_WEST_MAXLAGS,
    load_surprises_with_lags,
    spec2_ordered_logit_lr_test,
    spec3_surprise_on_lagged_index,
    spec3_surprise_on_lagged_index_and_skew,
)
from pipeline.ladder import load_records

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "inference_v1.json"
FRAGILITY_SUBSAMPLE_START = "2023-09-01"


def run_specs(rows: list[dict], records: list[dict]) -> dict:
    return {
        "n": len(rows),
        "spec3_surprise_on_lagged_index": spec3_surprise_on_lagged_index(rows),
        "spec3_surprise_on_lagged_index_and_skew": spec3_surprise_on_lagged_index_and_skew(rows),
        "spec2_ordered_logit_lr_test": spec2_ordered_logit_lr_test(rows, records),
    }


def main() -> None:
    rows = load_surprises_with_lags()
    records = load_records()

    full_sample = run_specs(rows, records)

    fragility_rows = [r for r in rows if r["date"] >= FRAGILITY_SUBSAMPLE_START]
    fragility = run_specs(fragility_rows, records)

    payload = {
        "schema": "inference-v1",
        "newey_west_maxlags": NEWEY_WEST_MAXLAGS,
        "full_sample": full_sample,
        "fragility_check_subsample": {
            "start_date": FRAGILITY_SUBSAMPLE_START,
            "results": fragility,
        },
        "notes": ("Small and careful, per instruction: this is a handful of specifications on "
                  "91 scheduled meetings (full sample) / 23 (post-hiking-cycle subsample), not a "
                  "search over many. Lagged features (index_level, skew) use the PREVIOUS meeting's "
                  "value, same convention as the benchmark ladder's L3 - see DECISIONS.md, 2026-07-11 "
                  "(ladder and headline-inference entries). The fragility-check subsample is small (n=23) and its ordered-logit "
                  "fit did not converge - reported anyway, clearly caveated, not hidden. "
                  "NOT published to the site - for review first."),
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")

    print(f"wrote {OUT}")
    fs3 = full_sample["spec3_surprise_on_lagged_index"]["coefficients"]["lagged_index"]
    print(f"\nFull sample (n={full_sample['n']}): Spec 3 lagged_index coef={fs3['coef']} t={fs3['t']} p={fs3['p']}")
    lr = full_sample["spec2_ordered_logit_lr_test"]
    print(f"Full sample: Spec 2 LR={lr.get('lr_statistic')} p={lr.get('p_value')} (converged={lr.get('converged')})")

    frag3 = fragility["spec3_surprise_on_lagged_index"]["coefficients"]["lagged_index"]
    print(f"\nFragility subsample (n={fragility['n']}, from {FRAGILITY_SUBSAMPLE_START}): "
          f"Spec 3 lagged_index coef={frag3['coef']} t={frag3['t']} p={frag3['p']}")
    frag_lr = fragility["spec2_ordered_logit_lr_test"]
    print(f"Fragility subsample: Spec 2 converged={frag_lr.get('converged')} "
          f"({frag_lr.get('note', 'ok')})")


if __name__ == "__main__":
    main()
