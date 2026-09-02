"""One catalogue of every reader-facing figure on every surface of the site.

Site layer, read-only. This module is the single source of truth for every
number a reader sees on index.html, methodology.html, README.md, the share
card and the episode annotations. `pipeline/build_fallbacks.py` writes the
values into `<!-- fig:NAME -->...<!-- /fig:NAME -->` regions in the markup;
`pipeline/tests/test_site_figures.py` reads the same catalogue back and fails
if a surface and its source file have drifted apart.

Nothing here is retyped. Values come from three kinds of source, and each
figure records which:

  * a published data file (data/index.json, data/ladder_v1.json,
    data/inference_v1.json, data/validation_v1.json, data/track_record.json,
    the newest data/predictions/lock-*.json) - a *result*;
  * a frozen specification constant, imported read-only from the science
    layer (pipeline/predict, pipeline/market, pipeline/ladder,
    pipeline/inference) - a *choice*, not a result;
  * arithmetic over the above, where the page states the arithmetic itself
    (e.g. "95 - 2 - 1 = 92").

Importing the science layer is explicitly permitted by CLAUDE.md ("Site and
context work may import these modules read-only"); nothing here writes.

ROUNDING POLICY (DECISIONS.md 2026-08-30, restated and enforced 2026-09-02)
---------------------------------------------------------------------------
Stated once, here, and mirrored by the JavaScript renderers in index.html:

    scores (Brier, log score, skill)   4 decimal places
    coefficients and t-statistics      2 decimal places
    p-values                           4 decimal places
    index values                       3 decimal places
    probabilities                      whole percentages (call card, OIS panel,
                                       track record)

Six decimal places on a coefficient whose p-value is 0.03 asserts a precision
the estimate does not have. Full precision stays in the JSON, which every
page links to. Every negative figure is written with a true minus sign
(U+2212), never a hyphen; the census test fails on a hyphen used as a minus.

Run:  python -m pipeline.site_figures        # prints the catalogue
"""
import html
import json
import statistics
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from pipeline.build_market_history import LOCK_DATE_OFFSET_DAYS
from pipeline.inference import MIN_OBSERVATIONS_FOR_LR_TEST, NEWEY_WEST_MAXLAGS
from pipeline.ladder import MIN_TRAINING_EXAMPLES, SIMULATION_SEED, SIMULATION_TRIALS
from pipeline.market.ois_history import find_nearest_available_date
from pipeline.predict.lock import MAX_CURVE_STALENESS_BUSINESS_DAYS
from pipeline.predict.market_probs import ASSUMED_MOVE_BP, LOCK_OFFSET_DAYS
from pipeline.predict.ordered_logit import N_CLASSES
from pipeline.site_context import UPCOMING_MEETINGS

ROOT = Path(__file__).resolve().parents[1]

# One source for the byline. Footer, meta author, README, share card and
# CITATION.cff all read this; none of them carries its own copy.
AUTHOR = {
    "name": "Jake Foulkes",
    "email": "jakefoulkes@aol.com",
    "affiliation": "BSc Economics, Loughborough University",
    "site": "https://jakefoulkes1.github.io/mpc-index/",
    "repo": "https://github.com/jakefoulkes1/mpc-index",
}

MINUS = "&minus;"          # for HTML surfaces
MINUS_CHAR = "−"      # the same character, for Markdown and JSON

# The rounding policy as code. PLACES is the only place a precision is set.
PLACES = {"score": 4, "coef": 2, "t": 2, "p": 4, "index": 3}


def load(rel: str):
    return json.loads((ROOT / rel).read_text())


def gb_date(iso: str) -> str:
    """The site's fmtDate: en-GB day, full month, year, from the date part
    of the string as written (no time-zone shift)."""
    d = datetime.fromisoformat(iso[:10])
    return f"{d.day} {d.strftime('%B')} {d.year}"


def gb_month(iso: str) -> str:
    d = datetime.fromisoformat(iso[:10])
    return f"{d.strftime('%B')} {d.year}"


def gb_stamp_utc(iso: str) -> str:
    """An instant, in the site's date format, to the second, explicitly UTC.
    Matches fmtUTCStamp() in index.html: "28 July 2026, 19:08:36 UTC"."""
    utc = datetime.fromisoformat(iso).astimezone(timezone.utc)
    return f"{utc.day} {utc.strftime('%B')} {utc.year}, {utc.strftime('%H:%M:%S')} UTC"


def signed(value: float, places: int) -> str:
    """A number for prose: a real minus sign, not a hyphen."""
    return f"{value:.{places}f}".replace("-", MINUS)


def score(value: float) -> str:
    return signed(value, PLACES["score"])


def coef(value: float) -> str:
    return signed(value, PLACES["coef"])


def tstat(value: float) -> str:
    return signed(value, PLACES["t"])


def pval(value: float) -> str:
    return f"{value:.{PLACES['p']}f}"


def index_value(value: float) -> str:
    return f"{value:.{PLACES['index']}f}"


def pct(value: float) -> str:
    return f"{value * 100:.0f}%"


def neutral(value: float) -> str:
    """The index's neutral midpoint, one decimal place ("1.0"). Mirrors
    fmtNeutral() in index.html."""
    return f"{value:.1f}"


def clip(value: float) -> str:
    """The log-score probability floor, e.g. 1e&minus;9. Python's repr pads the
    exponent ("1e-09") where JavaScript's does not ("1e-9"); this is the one
    form both write, with a true minus sign. Mirrors fmtClip() in index.html."""
    mantissa, _, exponent = f"{value:e}".partition("e")
    mantissa = mantissa.rstrip("0").rstrip(".")
    return f"{mantissa}e{int(exponent)}".replace("-", MINUS)


def prediction_file() -> str:
    """The prediction file the site displays: the newest lock-* file.

    Derived from the directory rather than typed, so a new lock is picked up
    by the next build and nothing has to be edited by hand. Hard-stops if no
    locked call exists - the site never silently falls back to a dry run.
    """
    locks = sorted((ROOT / "data" / "predictions").glob("lock-*.json"))
    if not locks:
        raise SystemExit("no data/predictions/lock-*.json - nothing to display as the call")
    return f"data/predictions/{locks[-1].name}"


def next_meeting_after(iso: str) -> str:
    """The first date in the Bank's published calendar strictly after `iso`.

    The calendar is the transcription in pipeline/site_context.py
    (DECISIONS.md 2026-08-10). Data-based rather than clock-based: the "next"
    meeting is the one after the latest locked call, which is the same on
    every machine and every day until the next lock file exists.
    """
    later = sorted(m for m in UPCOMING_MEETINGS if m > iso[:10])
    if not later:
        raise SystemExit(
            f"no meeting after {iso[:10]} in pipeline/site_context.py UPCOMING_MEETINGS - "
            f"transcribe the Bank's next calendar before building"
        )
    return later[0]


def lock_date_for(meeting_iso: str) -> str:
    """Announcement minus LOCK_DATE_OFFSET_DAYS calendar days: the convention
    build_market_history.py uses for every historical lock date."""
    d = date.fromisoformat(meeting_iso) - timedelta(days=LOCK_DATE_OFFSET_DAYS)
    return d.isoformat()


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
    """Every figure on any surface, as the string the surface should show.

    Negative values carry the HTML entity for the minus sign; use plain()
    for a Markdown or JSON surface.
    """
    index = load("data/index.json")
    ladder = load("data/ladder_v1.json")
    inf = load("data/inference_v1.json")
    validation = load("data/validation_v1.json")
    track = load("data/track_record.json")
    pred_path = prediction_file()
    lock = load(pred_path)

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

    locked = [r for r in track["records"] if r["kind"] == "locked"]
    next_meeting = next_meeting_after(lock["meeting_announcement"])

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
        "index_generated": gb_date(index["generated_utc"]),
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
        "log_clip": clip(ladder["log_score_probability_clip"]),
        "l3_skill": score(scores["L3"]["skill_vs_l1"]),
        "l3_fallback_windows": str(sum(1 for line in ladder["fallback_log"] if "L3" in line)),
        "l3_windows": str(ladder["n_meetings"]),
        # ---- inference (data/inference_v1.json), rounded for prose ----
        "nw_lags": str(inf["newey_west_maxlags"]),
        "spec3_n": str(n_spec3),
        "spec3_coef": coef(li["coef"]),
        "spec3_t": tstat(li["t"]),
        "spec3_p": pval(li["p"]),
        "frag_start": gb_date(frag["start_date"]),
        "frag_n": str(frag["results"]["n"]),
        "frag_coef": coef(frag_li["coef"]),
        "frag_t": tstat(frag_li["t"]),
        "frag_p": pval(frag_li["p"]),
        "spec2_lr": f"{lr['lr_statistic']:.4f}",
        "spec2_p": pval(lr["p_value"]),
        # The page states this subtraction, so the page should get it done
        # rather than asserted: corpus, less the specials, less the first
        # document (no preceding decision to measure a surprise from).
        "spec3_arithmetic": (
            f"{n_corpus} {MINUS} {n_specials} {MINUS} 1 = {n_spec3}"
        ),
        # ---- join tolerance (data/validation_v1.json) ----
        "join_tolerance_days": str(validation["max_day_tolerance"]),
        # ---- the locked call on display (newest data/predictions/lock-*) ----
        "lock_stamp_utc": gb_stamp_utc(lock["lock_timestamp"]),
        "lock_meeting": gb_date(lock["meeting_announcement"]),
        "lock_tag": Path(pred_path).stem,
        # ---- the record and the calendar ----
        "lock_count": str(len(locked)),
        "next_meeting": gb_date(next_meeting),
        "next_lock_date": gb_date(lock_date_for(next_meeting)),
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


def plain(catalogue: dict[str, str] | None = None) -> dict[str, str]:
    """The catalogue with entities resolved to characters, for Markdown and
    JSON surfaces (README.md, data/annotations.json)."""
    return {k: html.unescape(v) for k, v in (catalogue or figures()).items()}


def main() -> None:
    for name, value in figures().items():
        print(f"{name:26} {value}")


if __name__ == "__main__":
    main()
