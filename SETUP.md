# Setup

## 1. Environment
```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Prove it works
```bash
pytest                           # full suite; fixtures only, no live calls
python -m http.server 8000       # then open http://localhost:8000
```
(The site must be viewed over http://, not file:// — the page fetches
data/*.json.)

## 3. Rebuilding derived data (optional, needs the raw cache)
The published `data/*.json` and `data/*.csv` files are committed, so you can
browse the site and run the tests without scraping anything. To rebuild them
from scratch you need the local raw cache (`data/raw/`, gitignored), which
you create yourself:
```bash
python -m pipeline.scrape.era        # full Aug 2015-present minutes era
python -m pipeline.scrape.votes      # the Bank's voting spreadsheet
python -m pipeline.build_index       # raw docs -> data/index.json
python -m pipeline.build_votes       # spreadsheet -> data/votes.csv
```
Put your email in the User-Agent in `pipeline/scrape/minutes.py` first —
polite scraping (one request at a time, 2s sleep) is part of the method.

## 4. House rules
- `DECISIONS.md` is the lab notebook: every methodological choice, dated,
  before use. Read it before changing anything.
- `pipeline/score`, `pipeline/market`, `pipeline/predict` and the lexicon
  are the frozen science layer — import them, never modify them.
- Files under `data/predictions/lock-*` are never modified once written.
