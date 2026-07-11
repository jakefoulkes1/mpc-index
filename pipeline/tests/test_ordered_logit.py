import random

from pipeline.predict.ordered_logit import fit_ordered_logit, predict_proba


def test_converges_on_noisy_separable_data_and_is_monotonic():
    random.seed(1)
    X, y = [], []
    for _ in range(60):
        bp = random.uniform(-30, 30)
        if bp > 12:
            label = 2
        elif bp < -12:
            label = 0
        else:
            label = 1
        # add a little label noise so it's not perfectly separable
        if random.random() < 0.1:
            label = random.choice([0, 1, 2])
        X.append([bp])
        y.append(label)

    fit = fit_ordered_logit(X, y)
    assert fit.converged

    low = predict_proba(fit, [-20])
    mid = predict_proba(fit, [0])
    high = predict_proba(fit, [20])
    assert low["p_cut"] > mid["p_cut"] > high["p_cut"]
    assert high["p_hike"] > mid["p_hike"] > low["p_hike"]
    for probs in (low, mid, high):
        assert abs(sum(probs.values()) - 1.0) < 1e-6


def test_flags_degenerate_fit_on_deterministic_threshold_data():
    # A hard, noiseless threshold across all 3 classes (no overlap anywhere)
    # is the quasi-complete-separation case: the optimizer can keep
    # improving the likelihood by pushing a cutpoint to +-infinity, so it
    # "succeeds" numerically while landing on a degenerate, huge-magnitude
    # fit - exactly the failure mode the degenerate-parameter check exists
    # to catch (see module docstring).
    random.seed(2)
    X, y = [], []
    for _ in range(60):
        bp = random.uniform(-30, 30)
        if bp > 10:
            label = 2
        elif bp < -10:
            label = 0
        else:
            label = 1
        X.append([bp])
        y.append(label)
    fit = fit_ordered_logit(X, y)
    assert fit.converged is False


def test_all_same_class_is_a_well_behaved_fit():
    X = [[random.uniform(-5, 5)] for _ in range(10)]
    y = [1] * 10
    fit = fit_ordered_logit(X, y)
    assert fit.converged
    probs = predict_proba(fit, [0])
    assert probs["p_hold"] > 0.9
