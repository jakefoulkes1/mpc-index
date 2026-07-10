# MPC Communication Index

**Does the tone of Bank of England MPC communication carry information about the
next Bank Rate decision beyond what markets already price into the OIS/SONIA curve?**

Pre-registered probabilistic calls for each MPC decision, locked and timestamped
before the announcement, scored after it — including the misses. Null result = a
finding about market efficiency; positive result = information the market prices late.

## Status
- [x] Walking skeleton: one real document (June 2026 minutes) flows scrape → score → JSON → site
- [ ] Scrape the full Aug 2015–present minutes era
- [ ] Apel & Blix Grimaldi (2012) lexicon, implemented verbatim (replaces starter_v0)
- [ ] Voting-history ground truth (`mpcvoting.xlsx`) + tone-vs-skew validation
- [ ] OIS forward-curve benchmark
- [ ] First beta lock: **28 July 2026, 12:00**, for the 30 July announcement

## Quickstart
See `SETUP.md`. Short version: create a venv, `pip install -r requirements.txt`,
`pytest`, `python -m pipeline.build_index`, then `python -m http.server` and open
http://localhost:8000.

## Layout
```
pipeline/
  scrape/    fetch & cache Bank of England pages (run on your own machine)
  parse/     HTML -> clean text
  score/     sentence-level dictionary scoring (lexicon/ holds term lists)
  build_index.py   orchestrator: raw docs -> data/index.json
  tests/     golden-file tests; fixtures/ holds a short attributed excerpt
data/
  raw/       local cache of source texts (gitignored)
  index.json the published derived series
index.html   static front-end (GitHub Pages serves this)
DECISIONS.md dated log of every methodological choice
```

## Honesty notes
Not investment advice. Source documents © Bank of England, linked not republished.
The current lexicon is a plumbing placeholder — see DECISIONS.md.
