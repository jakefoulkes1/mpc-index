"""The headline inference: does the (lagged) A&BG index carry information
about market surprises or MPC decisions, beyond what the market already
priced? Small and careful, per instruction - a handful of specifications,
reported honestly including a small-n post-hiking-cycle fragility check.

Spec 3: OLS of surprise_bp (data/surprises.csv) on the lagged A&BG index
level, Newey-West HAC standard errors (statsmodels). A second version adds
lagged vote skew. "Lagged" = the PREVIOUS meeting's value, same convention
as the benchmark ladder's L3 (see DECISIONS.md, 2026-08-01, on why
index_level is lagged there - the identical reasoning applies here: a
meeting's own minutes publish simultaneously with its own decision, so
using them unlagged wouldn't be information available before that
decision was surprising or not).

Spec 2: in-sample ordered logit of the 3-class decision on
implied_change_bp, with and without the lagged index, likelihood-ratio
test for whether adding the index improves the fit.

Uses pipeline/predict/ordered_logit.py (already built for the benchmark
ladder) for Spec 2, and statsmodels (new dependency, for Newey-West HAC
specifically - see DECISIONS.md) for Spec 3.
"""
import csv
import json
from pathlib import Path

import statsmodels.api as sm

from pipeline.ladder import OUTCOME_CODES, load_records
from pipeline.predict.ordered_logit import fit_ordered_logit

ROOT = Path(__file__).resolve().parents[1]
SURPRISES_PATH = ROOT / "data" / "surprises.csv"

# Newey-West lag length: ~half a year of overlap at the current ~8
# meetings/year MPC cadence. A documented choice, not the only reasonable
# one - see DECISIONS.md.
NEWEY_WEST_MAXLAGS = 4
# Same threshold as pipeline/ladder.py's MIN_TRAINING_EXAMPLES, for the
# same reason: below this an ordered-logit fit isn't attempted at all,
# rather than risking scipy reporting a spurious "success" on a fit that's
# only trivially well-behaved because there's too little data to fail on.
MIN_OBSERVATIONS_FOR_LR_TEST = 10


def lagged_features_by_doc_id(records: list[dict]) -> dict[str, dict]:
    """doc_id -> {"lagged_index": prev meeting's abg_net_index or None,
    "lagged_skew": prev meeting's skew or None}, using records' own
    chronological order (records must already be sorted - load_records()
    returns them that way)."""
    out = {}
    prev = None
    for r in records:
        out[r["doc_id"]] = {
            "lagged_index": prev["index_level"] if prev else None,
            "lagged_skew": prev["skew"] if prev else None,
        }
        prev = r
    return out


def load_surprises_with_lags() -> list[dict]:
    records = load_records()
    lagged = lagged_features_by_doc_id(records)
    rows = []
    with open(SURPRISES_PATH) as fh:
        for row in csv.DictReader(fh):
            feats = lagged.get(row["meeting"])
            if feats is None or feats["lagged_index"] is None or feats["lagged_skew"] is None:
                continue
            rows.append({
                "meeting": row["meeting"],
                "date": row["date"],
                "surprise_bp": float(row["surprise_bp"]),
                "implied_change_bp": float(row["implied_change_bp"]),
                "lagged_index": feats["lagged_index"],
                "lagged_skew": feats["lagged_skew"],
            })
    return rows


def ols_newey_west(y: list[float], X: list[list[float]], feature_names: list[str],
                    maxlags: int = NEWEY_WEST_MAXLAGS) -> dict:
    """X: list of feature vectors, NO constant column (added here)."""
    X_with_const = sm.add_constant(X, has_constant="add")
    model = sm.OLS(y, X_with_const).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})
    names = ["const"] + feature_names
    return {
        "n": int(model.nobs),
        "newey_west_maxlags": maxlags,
        "r_squared": round(float(model.rsquared), 4),
        "coefficients": {
            name: {
                "coef": round(float(model.params[i]), 6),
                "t": round(float(model.tvalues[i]), 4),
                "p": round(float(model.pvalues[i]), 4),
            }
            for i, name in enumerate(names)
        },
    }


def spec3_surprise_on_lagged_index(rows: list[dict]) -> dict:
    y = [r["surprise_bp"] for r in rows]
    X = [[r["lagged_index"]] for r in rows]
    return ols_newey_west(y, X, ["lagged_index"])


def spec3_surprise_on_lagged_index_and_skew(rows: list[dict]) -> dict:
    y = [r["surprise_bp"] for r in rows]
    X = [[r["lagged_index"], r["lagged_skew"]] for r in rows]
    return ols_newey_west(y, X, ["lagged_index", "lagged_skew"])


def spec2_ordered_logit_lr_test(rows: list[dict], records: list[dict]) -> dict:
    """In-sample ordered logit of the 3-class decision on
    implied_change_bp, with and without the lagged index. Likelihood-ratio
    test: LR = 2*(loglik_full - loglik_restricted), chi-square(1) under H0
    that the index coefficient is zero."""
    outcome_by_doc = {r["doc_id"]: r["outcome"] for r in records}
    y, X_restricted, X_full = [], [], []
    for r in rows:
        outcome = outcome_by_doc.get(r["meeting"])
        if outcome is None:
            continue
        y.append(OUTCOME_CODES[outcome])
        X_restricted.append([r["implied_change_bp"]])
        X_full.append([r["implied_change_bp"], r["lagged_index"]])

    if len(y) < MIN_OBSERVATIONS_FOR_LR_TEST or len(set(y)) < 2:
        return {
            "n": len(y), "converged": False,
            "note": f"too little data for a reliable ordered-logit fit ({len(y)} observations, {len(set(y))} classes)",
        }

    fit_restricted = fit_ordered_logit(X_restricted, y)
    fit_full = fit_ordered_logit(X_full, y)

    if not fit_restricted.converged or not fit_full.converged:
        return {
            "n": len(y), "converged": False,
            "note": "one or both ordered-logit fits did not converge - LR test not computed",
        }

    from pipeline.predict.ordered_logit import _neg_log_likelihood
    import numpy as np
    ll_restricted = -_neg_log_likelihood(
        np.concatenate([fit_restricted.beta, [fit_restricted.tau[0], np.log(fit_restricted.tau[1] - fit_restricted.tau[0])]]),
        np.array(X_restricted), y,
    )
    ll_full = -_neg_log_likelihood(
        np.concatenate([fit_full.beta, [fit_full.tau[0], np.log(fit_full.tau[1] - fit_full.tau[0])]]),
        np.array(X_full), y,
    )
    lr_stat = 2 * (ll_full - ll_restricted)
    from scipy.stats import chi2
    p_value = 1 - chi2.cdf(lr_stat, df=1)

    return {
        "n": len(y),
        "converged": True,
        "log_likelihood_restricted_implied_change_only": round(ll_restricted, 4),
        "log_likelihood_full_plus_lagged_index": round(ll_full, 4),
        "lr_statistic": round(lr_stat, 4),
        "degrees_of_freedom": 1,
        "p_value": round(p_value, 4),
    }
