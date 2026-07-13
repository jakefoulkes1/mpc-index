"""Expanding-window benchmark ladder: L0 (always-hold) through L4
(member-level simulation), each fit on strictly prior meetings only and
evaluated on the next. See DECISIONS.md, 2026-07-11, for every modelling
choice below - several are genuine judgment calls where the task's own
wording left room for more than one reading, flagged as such.

Outcomes are coded 3-class by SIGN only {cut, hold, hike} - a 50bp move
counts the same as a 15bp move in the same direction, per instruction.

L3's `index_level` and vote `skew` are BOTH the PREVIOUS meeting's values,
not the target meeting's own. The task's wording explicitly lags skew
("last meeting's vote skew") but doesn't say so for index_level. A
meeting's own minutes (and therefore its own abg_net_index) are published
SIMULTANEOUSLY with its own decision - using a meeting's own index to
"forecast" its own decision would not be a real forecast at all, and
would be a fundamentally different (leaky) use of the data than every
other analysis in this project (pipeline/validate.py is explicitly
contemporaneous-not-predictive; this ladder is the first genuinely
predictive use). Lagging both features uniformly is the reading applied
here - logged prominently, not silently assumed.

L4 (member-level) blends two distributions per member with EQUAL weight
(0.5/0.5), introducing no new fitted parameter beyond what's listed:
(a) the pooled state-transition matrix (fit on strictly prior meetings),
    applied to that member's own most recent prior state;
(b) the same two-state +-25bp market-implied distribution already used
    for m0, applied at the per-member level (hawkish_dissent<->hike,
    with_majority<->hold, dovish_dissent<->cut).
Members with no prior history default to a deterministic "with_majority"
(100% hold), per instruction, with no market blending (nothing to blend
with). Committee-level outcome is a Monte Carlo simulation (fixed seed,
so the ladder is reproducible) of all voting members' individual draws,
aggregated by plurality (ties split equally among the tied outcomes).
"""
import csv
import datetime as dt
import json
import random
from pathlib import Path

from pipeline.decision_label import classify_decision
from pipeline.member_behaviour import classify as classify_member_state
from pipeline.member_behaviour import transition_counts as member_transition_counts
from pipeline.predict.market_probs import ASSUMED_MOVE_BP
from pipeline.predict.ordered_logit import fit_ordered_logit, predict_proba

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "data" / "index.json"
VOTES_PATH = ROOT / "data" / "votes.csv"
MARKET_HISTORY_PATH = ROOT / "data" / "market_history.csv"

EVAL_START = "2019-01-01"
OUTCOME_CODES = {"cut": 0, "hold": 1, "hike": 2}
CODE_TO_OUTCOME = {v: k for k, v in OUTCOME_CODES.items()}
STATE_TO_OUTCOME = {"hawkish_dissent": "hike", "with_majority": "hold", "dovish_dissent": "cut"}
# Same tolerance as pipeline/validate.py's corpus<->votes.csv date join.
MAX_DAY_TOLERANCE = 3
SIMULATION_TRIALS = 5000
SIMULATION_SEED = 42
MIN_TRAINING_EXAMPLES = 10  # below this, an ordered-logit fit isn't attempted at all


def load_raw_votes() -> dict[str, list[dict]]:
    """meeting_date -> list of that meeting's member rows (from votes.csv)."""
    by_date: dict[str, list[dict]] = {}
    with open(VOTES_PATH) as fh:
        for row in csv.DictReader(fh):
            by_date.setdefault(row["meeting_date"], []).append(row)
    return by_date


def load_records() -> list[dict]:
    """Chronological list of meeting records (Aug 2015-present) with every
    field every model needs. `index_level` and `skew` are each meeting's
    OWN values - lagging happens where features are built, not here."""
    corpus = json.loads(INDEX_PATH.read_text())
    docs = sorted(
        (d for d in corpus["documents"] if d["published"] and d["decision"]),
        key=lambda d: d["published"],
    )

    market = {}
    with open(MARKET_HISTORY_PATH) as fh:
        for row in csv.DictReader(fh):
            market[row["meeting"]] = row

    votes_by_date = load_raw_votes()
    vote_dates_sorted = sorted(dt.date.fromisoformat(d) for d in votes_by_date)

    records = []
    for doc in docs:
        m0_row = market.get(doc["doc_id"])
        if m0_row is None:
            continue  # market_history.csv covers every corpus meeting - tested
        published = dt.date.fromisoformat(doc["published"])
        nearest = min(vote_dates_sorted, key=lambda v: abs((v - published).days))
        votes_date = nearest.isoformat() if abs((nearest - published).days) <= MAX_DAY_TOLERANCE else None
        member_rows = votes_by_date.get(votes_date, []) if votes_date else []
        skew = float(member_rows[0]["skew"]) if member_rows else None

        records.append({
            "doc_id": doc["doc_id"],
            "date": doc["published"],
            "scheduled": m0_row["scheduled"] == "True",
            "outcome": classify_decision(doc["decision"]),
            "implied_change_bp": float(m0_row["implied_change_bp"]),
            "m0_probs": {"p_cut": float(m0_row["p_cut"]), "p_hold": float(m0_row["p_hold"]), "p_hike": float(m0_row["p_hike"])},
            "index_level": doc["abg_net_index"],
            "skew": skew,
            "votes_date": votes_date,
            "member_roster": [r["member"] for r in member_rows],
        })
    return records


# ---- L0 / L1 -----------------------------------------------------------

def l0_always_hold(_train, _target) -> dict:
    return {"p_cut": 0.0, "p_hold": 1.0, "p_hike": 0.0}


def l1_market_only(_train, target) -> dict:
    return dict(target["m0_probs"])


# ---- L2 / L3 (ordered logit) -------------------------------------------

def _standardize(X: list[list[float]]) -> tuple[list[list[float]], list[float], list[float]]:
    """z-score each feature column on the TRAINING data only (never the
    target), so the degenerate-parameter check in ordered_logit.py is
    comparing coefficients on a comparable scale regardless of a
    feature's raw units - without this, e.g. skew (raw values ~1e-3) and
    implied_change_bp (raw values ~1e1) would need wildly different
    coefficient magnitudes for an equally "healthy" fit, and every L3 fit
    was spuriously flagged degenerate before this was added. See
    DECISIONS.md, 2026-07-11."""
    n_features = len(X[0])
    means = [sum(row[j] for row in X) / len(X) for j in range(n_features)]
    stds = []
    for j in range(n_features):
        var = sum((row[j] - means[j]) ** 2 for row in X) / len(X)
        stds.append(var ** 0.5 if var > 0 else 1.0)
    X_std = [[(row[j] - means[j]) / stds[j] for j in range(n_features)] for row in X]
    return X_std, means, stds


def _fit_and_predict(train_X: list[list[float]], train_y: list[int], x: list[float]) -> tuple[dict | None, str]:
    if len(train_X) < MIN_TRAINING_EXAMPLES or len(set(train_y)) < 2:
        return None, f"too little training data ({len(train_X)} examples, {len(set(train_y))} classes)"
    X_std, means, stds = _standardize(train_X)
    fit = fit_ordered_logit(X_std, train_y)
    if not fit.converged:
        return None, f"did not converge: {fit.message}"
    x_std = [(x[j] - means[j]) / stds[j] for j in range(len(x))]
    return predict_proba(fit, x_std), "ok"


def l2_market_logit(train: list[dict], target: dict) -> tuple[dict | None, str]:
    X = [[r["implied_change_bp"]] for r in train]
    y = [OUTCOME_CODES[r["outcome"]] for r in train]
    return _fit_and_predict(X, y, [target["implied_change_bp"]])


def l3_market_index_skew_logit(records: list[dict], train_end_idx: int, target_idx: int) -> tuple[dict | None, str]:
    """records/indices (not just a train list) because L3 needs each
    training example's OWN preceding record for its lagged features -
    see module docstring on why index_level/skew are lagged."""
    X, y = [], []
    for j in range(1, train_end_idx):  # j=0 has no predecessor to lag from
        prev = records[j - 1]
        if prev["index_level"] is None or prev["skew"] is None:
            continue
        X.append([records[j]["implied_change_bp"], prev["index_level"], prev["skew"]])
        y.append(OUTCOME_CODES[records[j]["outcome"]])

    prev = records[target_idx - 1]
    if prev["index_level"] is None or prev["skew"] is None:
        return None, "target's preceding meeting missing index_level/skew"
    x = [records[target_idx]["implied_change_bp"], prev["index_level"], prev["skew"]]
    return _fit_and_predict(X, y, x)


# ---- L4 (member-level simulation) --------------------------------------

def market_implied_state_distribution(implied_change_bp: float) -> dict:
    """Same two-state +-ASSUMED_MOVE_BP assumption as m0
    (pipeline/predict/market_probs.py), reused at the per-member level."""
    if implied_change_bp > 0:
        p_hike = max(0.0, min(1.0, implied_change_bp / ASSUMED_MOVE_BP))
        return {"hike": p_hike, "hold": 1 - p_hike, "cut": 0.0}
    if implied_change_bp < 0:
        p_cut = max(0.0, min(1.0, -implied_change_bp / ASSUMED_MOVE_BP))
        return {"cut": p_cut, "hold": 1 - p_cut, "hike": 0.0}
    return {"hold": 1.0, "hike": 0.0, "cut": 0.0}


def _prior_member_votes(votes_by_date: dict[str, list[dict]], before_date: str) -> dict[str, list[tuple[str, str]]]:
    member_votes: dict[str, list[tuple[str, str]]] = {}
    for date in sorted(d for d in votes_by_date if d < before_date):
        for row in votes_by_date[date]:
            state = classify_member_state(float(row["preferred_rate"]), float(row["decided_rate"]))
            member_votes.setdefault(row["member"], []).append((date, state))
    return member_votes


def _simulate_committee(member_distributions: list[dict], trials: int = SIMULATION_TRIALS, seed: int = SIMULATION_SEED) -> dict:
    rng = random.Random(seed)
    outcome_counts = {"cut": 0.0, "hold": 0.0, "hike": 0.0}
    for _ in range(trials):
        votes = {"cut": 0, "hold": 0, "hike": 0}
        for dist in member_distributions:
            r = rng.random()
            cum = 0.0
            chosen = "hike"  # floating-point safety net if cum never reaches r
            for label in ("cut", "hold", "hike"):
                cum += dist[label]
                if r < cum:
                    chosen = label
                    break
            votes[chosen] += 1
        top = max(votes.values())
        winners = [k for k, v in votes.items() if v == top]
        for w in winners:
            outcome_counts[w] += 1.0 / len(winners)
    total = sum(outcome_counts.values())
    return {f"p_{k}": v / total for k, v in outcome_counts.items()}


def l4_member_simulation(votes_by_date: dict[str, list[dict]], target: dict) -> dict | None:
    if not target["votes_date"] or not target["member_roster"]:
        return None
    prior_votes = _prior_member_votes(votes_by_date, target["votes_date"])
    counts = member_transition_counts(prior_votes)

    market_dist = market_implied_state_distribution(target["implied_change_bp"])
    member_distributions = []
    for member in target["member_roster"]:
        history = prior_votes.get(member)
        if not history:
            member_distributions.append({"cut": 0.0, "hold": 1.0, "hike": 0.0})  # no history -> default majority
            continue
        current_state = history[-1][1]
        row_total = sum(counts[current_state].values())
        if row_total == 0:
            member_distributions.append(market_dist)  # no transition data yet for this state
            continue
        transition_dist = {STATE_TO_OUTCOME[s]: counts[current_state][s] / row_total for s in counts[current_state]}
        blended = {k: 0.5 * transition_dist[k] + 0.5 * market_dist[k] for k in ("cut", "hold", "hike")}
        member_distributions.append(blended)

    result = _simulate_committee(member_distributions)
    return result
