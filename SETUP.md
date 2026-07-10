# Setup & first commit

## 1. Environment
```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Prove it works
```bash
pytest                           # parser + scorer tests, incl. a real-text fixture
python -m pipeline.build_index   # rebuilds data/index.json from data/raw/
python -m http.server 8000       # then open http://localhost:8000
```
(The site must be viewed over http://, not file:// — the page fetches data/index.json.)

## 3. Scrape another document (your machine, not required to start)
```bash
python -m pipeline.scrape.minutes 2026 april
```
Then add a matching entry to MANIFEST in `pipeline/build_index.py` and rebuild.
Works for the Aug 2015–present era. Put your email in the User-Agent in
`pipeline/scrape/minutes.py` first — polite scraping is part of the method.

## 4. Your first commit — today
```bash
git init
git add -A
git commit -m "Walking skeleton: one document flows end to end"
```
Create a **public** GitHub repo named mpc-index, then:
```bash
git remote add origin https://github.com/YOURUSER/mpc-index.git
git branch -M main
git push -u origin main
```
Enable the site: repo Settings → Pages → Deploy from a branch → main → / (root).
Two minutes later the page is live at https://YOURUSER.github.io/mpc-index/

## 5. Make it yours
- Put your name in LICENSE and your email in the scraper User-Agent.
- Read `pipeline/score/dictionary.py` line by line (~90 lines). You will be asked
  to defend it; it must be yours.
- DECISIONS.md is your lab notebook. Every choice, dated, before use.
