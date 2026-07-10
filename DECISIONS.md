# Decisions log

Every methodological choice gets a dated line here, before it is used.
Changes apply forward only; nothing is retrofitted. Locked calls are never touched.

## 2026-07-05 — repo created
- **Thesis:** does the tone of MPC communication carry information about the next
  Bank Rate decision beyond what the OIS/SONIA curve already prices? Null = no.
  Either answer is the result.
- **Starter lexicon is plumbing, not research.** `pipeline/score/lexicon/starter_v0.json`
  exists only to test the pipeline end to end. The research baseline is the
  Apel & Blix Grimaldi (2012) lexicon implemented verbatim (target: week 2).
  No index level produced by starter_v0 will be used in any analysis or claim.
- **Negation window = 3 tokens** before a matched term flips its sign.
  Known-crude (misses e.g. "do not see a compelling case to increase Bank Rate");
  parameter to revisit alongside the A&BG implementation.
- **Raw texts are gitignored.** Derived scores and hashes are public; full source
  texts stay local, with links to bankofengland.co.uk as the public reference,
  pending a check of the Bank's re-publication terms.
- **Site lives at repo root** (index.html + data/index.json) for zero-config
  GitHub Pages. May move to /site with a deploy action later.
- **Scope of era:** scrape the post-August-2015 "Super Thursday" HTML era first
  (covers the whole 2016–2026 evaluation window). Pre-2015 PDFs deferred to August.

## 2026-07-11 — era corpus, Aug 2015–Jun 2026

- **Meeting schedule discovered by trying, not hardcoded.** `pipeline/scrape/era.py`
  requests every month from Aug 2015 to Jun 2026 and tolerates 404s for months
  with no meeting. Result: 92 documents scraped, 39 months with no meeting (404),
  matching the known shift from monthly MPC meetings (through 2015-2016) to the
  8-per-year "Super Thursday" schedule (2017 on).
- **Two URL slug patterns exist and both are tried.** 2015-2016 pages live at
  `.../<year>/mpc-<month>-<year>`; 2017 onward at `.../<year>/<month>-<year>`.
  Discovered by checking a 404 against Bank of England search results for a
  known August 2015 minutes page. `scrape_month` in `pipeline/scrape/minutes.py`
  tries the plain slug first, then falls back to the `mpc-`-prefixed slug on a
  404, rather than hardcoding a year cutoff.
- **Suspect-parse threshold: <1,000 words.** 23 of the 92 documents fall under
  this (mostly 2017-2021 minutes, which were genuinely shorter in that era, not
  parse failures on inspection). Flagged in scrape output, not excluded or
  reparsed - a judgement call for later, not this pass.
- **`published = meeting_end + 1 day`**, per instruction, replacing the old
  MANIFEST's literal scraped "Published on" date. Cross-checked against the
  actual "Published on" text present in 90 of 92 documents: matches in 87,
  off by one extra day in 3 (2020-08, 2021-06, 2021-11 - likely weekend/holiday
  slippage in the Bank's actual publication schedule). The rule is applied
  uniformly regardless; the 3-document gap is logged here, not silently fixed.
- **decision/vote parsed from the first sentence containing both "voted" and
  "Bank Rate"** (not necessarily the same sentence as "meeting ending on" -
  those two are split across sentences in some 2021 documents). Vote split
  handles three source phrasings: "voted by a majority of A-B to...",
  "voted A-B to..." (2017 short-form summary pages), and "voted unanimously
  to...". En dash and em dash vote splits (introduced in newer pages, e.g.
  "7–2") are normalised to a plain hyphen.
- **Two fields left deliberately null rather than guessed:**
  - `2015-10`: meeting_end/published null - the source sentence reads "meeting
    ending on 6 October," with no year stated in the text at all.
  - `2022-09`: vote null (decision still parses) - the actual split was a
    three-way vote (5 for +50bp, 3 for +75bp, 1 for +25bp) described in prose
    in the following sentence, not representable as a single "A-B" pair.
- **meeting_end date phrasing varies slightly across eras** ("ending on
  <date>" is standard; a few 2016 pages drop the "on"). The parser regex
  accepts both; still requires a 4-digit year to accept a match.
