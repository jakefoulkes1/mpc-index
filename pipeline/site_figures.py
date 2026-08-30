"""One catalogue of every reader-facing figure on index.html and methodology.html.

Site layer, read-only. This module is the single source of truth for every
number a reader sees on either page. `pipeline/build_fallbacks.py` writes the
values into `<!-- fig:NAME -->...<!-- /fig:NAME -->` regions in the markup;
`pipeline/tests/test_site_figures.py` reads the same catalogue back and fails
if a page and its source file have drifted apart.

Nothing here is retyped. Values come from three kinds of source, and each
figure records which:

  * a published data file (data/index.json, data/ladder_v1.json,
    data/inference_v1.json, data/validation_v1.json) - a *result*;
  * a frozen specification constant, imported read-only from the science
    layer (pipeline/predict, pipeline/market, pipeline/ladder,
    pipeline/inference) - a *choice*, not a result;
  * arithmetic over the above, where the page states the arithmetic itself
    (e.g. "95 - 2 - 1 = 92").

Importing the science layer is explicitly permitted by CLAUDE.md ("Site and
context work may import these modules read-only"); nothing here writes.

Rounding policy (DECISIONS.md 2026-08-30): regression coefficients and
t-statistics are shown to 2 decimal places and p-values to 4, because six
decimal places on a coefficient with a p of 0.03 implies a precision the
estimate does not have. Full precision stays in the JSON, which the page
links to. Scores that the ladder itself publishes rounded (Brier, log score,
skill) are shown exactly as stored.

Run:  python -m pipeline.site_figures        # prints the catalogue
"""
import json
import statistics
from datetime import datetime
from pathlib import Path

from pipeline.build_market_history import LOCK_DATE_OFFSET_DAYS
from pipeline.inference import MIN_OBSERVATIONS_FOR_LR_TEST, NEWEY_WEST_MAXLAGS
from pipeline.ladder import MIN_TRAINING_EXAMPLES, SIMULATION_SEED, SIMULATION_TRIALS
from pipeline.market.ois_history import find_nearest_available_date
from pipeline.predict.lock import MAX_CURVE_STALENESS_BUSINESS_DAYS
from pipeline.predict.market_probs import ASSUMED_MOVE_BP, LOCK_OFFSET_DAYS
from pipeline.predict.ordered_logit import N_CLASSES

ROOT = Path(__file__).resolve().parents[1]

MINUS = "&minus;"


def load(rel: str):
    return json.loads((ROOT / rel).read_text())


def gb_date(iso: str) -> str:
    """The site's fmtDate: en-GB day, full month, year."""
    d = datetime.fromisoformat(iso[:10])
    return f"{d.day} {d.strftime('%B')} {d.year}"


def gb_month(iso: str) -> str:
    d = datetime.fromisoformat(iso[:10])
    return f"{d.strftime('%B')} {d.year}"


def signed(value: float, places: int) -> str:
    """A number for prose: a real minus sign, not a hyphen."""
    return f"{value:.{places}f}".replace("-", MINUS)


def walk_back_cap_days() -> int:
    """The walk-back cap is a default argument, not a module constant."""
    import inspect

    return inspect.signature(find_nearest_available_date).parameters["max_walk"].default


def sparsity() -> dict:
    """(hawkish + dovish) lexicon hits per document, quartiles included.

    Same computation as pipeline/lexicon_sparsity.py, which is the script
    the methodology page cites; duplicated here rather than imported so the
    catalogue has no dependency on a __main__-shaped helper.
    """
    docs = load("data/index.json")["documents"]
    hits = sorted(d["abg_hawk"] + d["abg_dove"] for d in docs)
    q1, med, q3 = statistics.quantiles(hits, n=4, method="inclusive")
    return {"median": med, "q1": q1, "q3": q3, "iqr": q3 - q1, "min": hits[0], "max": hits[-1]}


def figures() -> dict[str, str]:
    """Every figure on either page, as the string the page should show."""
    index = load("data/index.json")
    ladder = load("data/ladder_v1.json")
    inf = load("data/inference_v1.json")
    validation = load("data/validation_v1.json")

    docs = index["documents"]
    specials = [d for d in docs if d["type"] != "minutes"]
    regular = [d for d in docs if d["type"] == "minutes"]
    published_years = [d["published"][:4] for d in docs]
    hits = sparsity()

    full = inf["full_sample"]["spec3_surprise_on_lagged_index"]
    li = full["coefficients"]["lagged_index"]
    frag = inf["fragility_check_subsample"]
    frag_li = frag["results"]["spec3_surprise_on_lagged_index"]["coefficients"]["lagged_index"]
    lr = inf["full_sample"]["spec2_ordered_logit_lr_test"]
    scores = ladder["headline_scores_scheduled_only"]

    n_corpus = len(docs)
    n_specials = len(specials)
    n_spec3 = full["n"]

    fig: dict[str, str] = {
        # ---- corpus (data/index.json) ----
        "corpus_n": str(n_corpus),
        "corpus_start_month": gb_month(min(d["published"] for d in docs)),
        "corpus_end_month": gb_month(max(d["published"] for d in docs)),
        "corpus_regular": str(len(regular)),
        "corpus_specials": str(n_specials),
        "corpus_pdf_reconstructed": str(
            sum(1 for d in regular if d["source_kind"] == "pdf")
        ),
        "corpus_2016_docs": str(published_years.count("2016")),
        "corpus_2017_docs": str(published_years.count("2017")),
        # ---- lexicon sparsity (data/index.json) ----
        "hits_median": f"{hits['median']:g}",
        "hits_iqr": f"{hits['iqr']:g}",
        "hits_q1": f"{hits['q1']:g}",
        "hits_q3": f"{hits['q3']:g}",
        "hits_min": str(hits["min"]),
        "hits_max": str(hits["max"]),
        # ---- ladder (data/ladder_v1.json) ----
        "eval_start": gb_date(ladder["eval_start"]),
        "n_evaluated": str(ladder["n_meetings"]),
        "n_scheduled": str(ladder["n_scheduled"]),
        "n_specials": str(ladder["n_specials"]),
        "log_clip": str(ladder["log_score_probability_clip"]),
        "l3_skill": signed(scores["L3"]["skill_vs_l1"], 4),
        "l3_fallback_windows": str(sum(1 for line in ladder["fallback_log"] if "L3" in line)),
        "l3_windows": str(ladder["n_meetings"]),
        # ---- inference (data/inference_v1.json), rounded for prose ----
        "nw_lags": str(inf["newey_west_maxlags"]),
        "spec3_n": str(n_spec3),
        "spec3_coef": signed(li["coef"], 2),
        "spec3_t": signed(li["t"], 2),
        "spec3_p": f"{li['p']:.4f}",
        "frag_start": gb_date(frag["start_date"]),
        "frag_n": str(frag["results"]["n"]),
        "frag_coef": signed(frag_li["coef"], 2),
        "frag_t": signed(frag_li["t"], 2),
        "frag_p": f"{frag_li['p']:.4f}",
        "spec2_lr": f"{lr['lr_statistic']:.4f}",
        "spec2_p": f"{lr['p_value']:.4f}",
        # The page states this subtraction, so the page should get it done
        # rather than asserted: corpus, less the specials, less the first
        # document (no preceding decision to measure a surprise from).
        "spec3_arithmetic": (
            f"{n_corpus} {MINUS} {n_specials} {MINUS} 1 = {n_spec3}"
        ),
        # ---- join tolerance (data/validation_v1.json) ----
        "join_tolerance_days": str(validation["max_day_tolerance"]),
        # ---- frozen specification constants, imported read-only ----
        "move_bp": f"{ASSUMED_MOVE_BP:g}",
        "lock_offset_days": str(LOCK_OFFSET_DAYS),
        "lock_date_offset_days": str(LOCK_DATE_OFFSET_DAYS),
        "walk_back_cap_days": str(walk_back_cap_days()),
        "curve_staleness_days": str(MAX_CURVE_STALENESS_BUSINESS_DAYS),
        "sim_trials": f"{SIMULATION_TRIALS:,}",
        "sim_seed": str(SIMULATION_SEED),
        "min_training_examples": str(MIN_TRAINING_EXAMPLES),
        "n_outcome_classes": str(N_CLASSES),
        "min_obs_lr_test": str(MIN_OBSERVATIONS_FOR_LR_TEST),
    }
    return fig


def main() -> None:
    for name, value in figures().items():
        print(f"{name:26} {value}")


if __name__ == "__main__":
    main()
