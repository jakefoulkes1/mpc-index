# MPC Communication Index

[![tests](https://github.com/jakefoulkes1/mpc-index/actions/workflows/tests.yml/badge.svg)](https://github.com/jakefoulkes1/mpc-index/actions/workflows/tests.yml)

**Live site:** <https://jakefoulkes1.github.io/mpc-index/> ·
**Methodology:** <https://jakefoulkes1.github.io/mpc-index/methodology.html> ·
**Decision log:** [DECISIONS.md](DECISIONS.md)

## The question

Does the tone of the Bank of England Monetary Policy Committee's published
minutes carry information about the next Bank Rate decision beyond what
financial markets already price into the OIS/SONIA curve? Every MPC minutes
document from August 2015 to the present (94 documents) is scored with the
Apel & Blix Grimaldi (2012) hawkish/dovish dictionary index, exactly as
described in that paper. The benchmark is the market itself: probabilities
implied by the Bank's own published OIS forward curve. Models that add the
tone index are evaluated against that benchmark in an expanding-window
backtest, and — going forward — in pre-registered probabilistic calls locked
and timestamped before each announcement and scored after it, including the
misses. A null result (the market already prices everything the tone says)
is a finding about market efficiency, not a failure of the project.

## How it works

Five stages: scrape → score → benchmark → lock → score.

```
 Bank of England minutes            Bank of England OIS curve + SONIA
 (HTML pages + PDF backfill)        (published spreadsheets)
          |                                     |
   pipeline/scrape, pipeline/parse       pipeline/market
          |                                     |
          v                                     v
 A&BG (2012) tone index per document    market-implied probabilities
   pipeline/score/abg.py                  {cut, hold, hike} per meeting
          |                             pipeline/predict/market_probs.py
          v                                     |
   data/index.json  ---------------+------------+
                                   |
                                   v
                expanding-window benchmark ladder, L0-L4
                  pipeline/ladder.py -> data/ladder_v1.json
                                   |
                                   v
              lock: pre-registered call, frozen before the
              announcement (pipeline/predict/lock.py ->
              data/predictions/, never modified once locked)
                                   |
                                   v
              score after the announcement (Brier, log score)
                  pipeline/predict/score_outcomes.py
```

## Headline results

Values below are copied verbatim from [data/ladder_v1.json](data/ladder_v1.json)
and [data/inference_v1.json](data/inference_v1.json) — the JSON files are the
source of truth.

**Benchmark ladder** — scheduled meetings only, expanding-window evaluation
from 1 January 2019 (60 meetings; the two March 2020 emergency meetings are
reported separately in the JSON as a robustness line). Lower Brier / log
score is better; positive skill vs L1 would mean beating the market.

| Model | Description | Mean Brier | Mean log score | Skill vs L1 | n |
|---|---|---|---|---|---|
| L0 | always hold | 0.6667 | 6.9078 | — | 60 |
| L1 | market-only (OIS-implied, two-state ±25bp) | 0.0905 | 0.1454 | reference | 60 |
| L2 | ordered logit on the market-implied change | 0.1011 | 0.1701 | −0.1171 | 60 |
| L3 | L2 + lagged tone index + lagged vote skew | 0.1514 | 0.2664 | −0.6729 | 60 |
| L4 | member-level transition simulation, blended with market | 0.1644 | 0.263 | −0.8166 | 60 |

No model that adds the tone index beats the market-only benchmark (L1) in
this backtest.

**Spec 3** — OLS of the market surprise (actual minus market-implied rate
change, in basis points) on the previous meeting's tone index, Newey–West
standard errors (4 lags), full sample of 91 scheduled meetings:
coefficient −2.163349, t = −2.1499, **p = 0.0316**. On the post-hiking-cycle
subsample (from 1 September 2023, n = 23) the result does not replicate:
coefficient −3.441919, t = −1.4678, p = 0.1422. Spec 2, an ordered-logit
likelihood-ratio test of the same lagged index on the three-class decision,
finds nothing on the full sample: LR = 0.4726, p = 0.4918. The two
specifications disagree; both are reported.

**First pre-registered lock: 28 July 2026, 12:00, for the 30 July 2026
announcement.** Files under `data/predictions/lock-*` are permanent once
written, misses included.

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest                            # full suite, no live network calls
python -m http.server 8000        # then open http://localhost:8000
```

The site must be viewed over http://, not file:// — the page fetches
`data/*.json`. Rebuilding the derived data (`python -m pipeline.build_index`
and the other `pipeline.build_*` modules) requires the raw source cache,
which is local-only (see below). See [SETUP.md](SETUP.md) for scraping your
own copy.

## Repository map

```
pipeline/
  scrape/     fetch & cache Bank of England pages/PDFs (polite, run locally)
  parse/      HTML -> clean text
  score/      A&BG (2012) index (abg.py); lexicon/ holds the term lists
  market/     OIS forward curve + SONIA readers (Bank of England data)
  predict/    market-implied probabilities, lock machinery, scoring rules
  ladder.py   expanding-window benchmark ladder L0-L4
  inference.py         Spec 2 / Spec 3 statistical tests
  validate.py          contemporaneous tone-vs-votes checks
  build_*.py           orchestrators: raw inputs -> data/*.json|csv
  inspect.py           per-document evidence inspector (drafting tool)
  tests/      105 tests; fixtures only, no live network calls
data/
  raw/                 local cache of source texts (gitignored, never public)
  index.json           the published tone-index series
  market_history.csv   market-implied probabilities at lock date, per meeting
  ladder_v1.json       benchmark ladder results
  inference_v1.json    Spec 2 / Spec 3 results
  predictions/         one JSON per call; lock-* files are permanent
index.html       the site (static, GitHub Pages, no build step)
methodology.html specification sheet for data, index, benchmark, evaluation
site/annotations/     episode write-ups rendered by the site
DECISIONS.md     dated log of every methodological choice (append-only)
```

## Limitations

Documented limitations — risk premia embedded in OIS forwards, sparse
lexicon hits per document, the lexicon's 2012 vintage, small n, and the
disagreement between Spec 2 and Spec 3 — are listed factually on the
[methodology page](https://jakefoulkes1.github.io/mpc-index/methodology.html#limitations),
each traceable to a dated entry in [DECISIONS.md](DECISIONS.md).

## Notes

Not investment advice. Source documents © Bank of England, linked, not
republished; raw texts stay in a local gitignored cache and only derived
scores and hashes are published.
