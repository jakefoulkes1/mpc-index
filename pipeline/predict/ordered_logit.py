"""Minimal ordered logistic regression (proportional-odds model) for a
3-class ordinal outcome {cut=0, hold=1, hike=2}, fit by direct MLE via
scipy.optimize.

scipy was added as a dependency specifically for this (see DECISIONS.md,
2026-08-01) - unlike the plain-Python Pearson/Spearman in
pipeline/validate.py (simple closed-form formulas), a numerically stable
ordinal-logit MLE fit is a different order of complexity, and re-deriving
scipy's own optimizer by hand would be reinventing something it already
does robustly.

Model: P(y <= j) = sigmoid(tau_j - x . beta), j in {0, 1} (2 cutpoints for
3 ordered classes). tau_0 < tau_1 is enforced by reparameterising
tau_1 = tau_0 + exp(delta), fit unconstrained.

Convergence: scipy's own optimizer success flag, PLUS a check for
degenerate (very large-magnitude) fitted parameters - the classic failure
mode for small/separated samples (e.g. a training window with zero or
very few cut outcomes) is the optimizer walking a threshold to a huge
value while nominally "succeeding". A caller should treat
`OrderedLogitFit.converged == False` as "fall back to another model for
this window" - this module doesn't decide the fallback policy itself.
"""
import math
from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize

N_CLASSES = 3  # cut, hold, hike
DEGENERATE_PARAM_THRESHOLD = 50.0


def _sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    ez = math.exp(z)
    return ez / (1.0 + ez)


@dataclass
class OrderedLogitFit:
    beta: np.ndarray
    tau: tuple[float, float]
    converged: bool
    message: str


def _class_probs(x: np.ndarray, beta: np.ndarray, tau: tuple[float, float]) -> list[float]:
    xb = float(np.dot(x, beta))
    c0 = _sigmoid(tau[0] - xb)
    c1 = _sigmoid(tau[1] - xb)
    p0 = c0
    p1 = max(c1 - c0, 0.0)
    p2 = max(1.0 - c1, 0.0)
    total = p0 + p1 + p2
    return [p0 / total, p1 / total, p2 / total]


def _neg_log_likelihood(params: np.ndarray, X: np.ndarray, y: list[int]) -> float:
    n_features = X.shape[1]
    beta = params[:n_features]
    tau0 = params[n_features]
    tau1 = tau0 + math.exp(params[n_features + 1])
    nll = 0.0
    for i, yi in enumerate(y):
        probs = _class_probs(X[i], beta, (tau0, tau1))
        nll -= math.log(max(probs[yi], 1e-12))
    return nll


def fit_ordered_logit(X: list[list[float]], y: list[int]) -> OrderedLogitFit:
    """X: feature vectors, no intercept column (the two cutpoints act as
    thresholds). y: ints in {0, 1, 2} = {cut, hold, hike}."""
    X_arr = np.array(X, dtype=float)
    n_features = X_arr.shape[1]
    x0 = np.zeros(n_features + 2)
    result = minimize(_neg_log_likelihood, x0, args=(X_arr, y), method="BFGS")

    beta = result.x[:n_features]
    tau0 = result.x[n_features]
    tau1 = tau0 + math.exp(result.x[n_features + 1])

    degenerate = bool(np.any(np.abs(result.x) > DEGENERATE_PARAM_THRESHOLD))
    converged = bool(result.success) and bool(np.all(np.isfinite(result.x))) and not degenerate
    message = result.message if not degenerate else f"{result.message} (degenerate: |param| > {DEGENERATE_PARAM_THRESHOLD})"
    return OrderedLogitFit(beta=beta, tau=(tau0, tau1), converged=converged, message=message)


def predict_proba(fit: OrderedLogitFit, x: list[float]) -> dict:
    p0, p1, p2 = _class_probs(np.array(x, dtype=float), fit.beta, fit.tau)
    return {"p_cut": p0, "p_hold": p1, "p_hike": p2}
