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

## 2026-07-18 — corpus audit: full-text repair + special meetings

- **Root cause of the 30 (later found: 52) short documents, confirmed by
  fetching 3 live pages, not guessed:** the Bank published the Monetary
  Policy Summary and full Minutes as two separate documents - summary on the
  HTML page, full minutes only in a linked PDF - until August 2021, when it
  started publishing the full minutes inline in HTML. The word-count
  threshold (<1,000) had actually undercounted the problem: several
  Summary-only pages (e.g. the March 2020 Covid summary at 1,625 words)
  exceed 1,000 words on the strength of the summary alone while still
  missing the full minutes entirely. The real test used from here on is
  "words found after the 'Minutes of the Monetary Policy Committee meeting
  ending on' heading" (`pipeline/scrape/backfill_pdf.py:is_summary_only`),
  not a raw word-count cutoff.
- **52 of 93 documents (Aug 2015 - Jun 2021) backfilled from the Bank's PDF
  minutes**, via `pipeline/scrape/backfill_pdf.py` + `pdfplumber` (added to
  requirements.txt). PDF URLs follow one of two patterns discovered by
  probing: `<month>-<year>.pdf` (most months) or `minutes-<month>-<year>.pdf`
  (2015-08, 2015-12, 2017-06) - the script tries both. Same 2s polite-sleep
  discipline as the HTML scraper.
- **`source_kind` ("html" | "pdf") and `word_count` added to every document
  record**, so anyone using index.json can see which documents were
  reconstructed from PDF vs scraped inline. Recorded in a local, gitignored
  sidecar (`data/raw/source_kind.json`, inside the already-gitignored
  `data/raw/`) that `build_index.py` reads at build time - consistent with
  raw texts already being local-only; only the derived fields in index.json
  are public.
- **Corpus reconciled against the Bank's own sitemap**
  (bankofengland.co.uk/sitemap/minutes) rather than trusted on the strength
  of era.py's month-by-month probing alone. Every regular month-slug meeting
  in the Bank's listing matched our corpus exactly (zero missing, zero
  extra) within the Aug 2015-Jun 2026 window.
- **One special meeting added: the 10 March 2020 emergency meeting**
  (first Covid-19 rate cut, 50bp to 0.25% + Term Funding Scheme), found via
  the sitemap reconciliation at a non-month-slug URL
  (`.../2020/13march-2020`), not discoverable by era.py's normal probing.
  Saved as `data/raw/2020-03-10-special-minutes.txt`, `doc_id
  minutes-2020-03-10-special`, `type special_minutes`. Its `source_url` is
  looked up from a small explicit table (`SPECIAL_SOURCE_URLS` in
  build_index.py) since it doesn't fit the standard slug-reconstruction
  formula - extend that table if more special meetings turn up reconciling
  other eras.
- **The 19 March 2020 special-meeting page is deliberately NOT added as a
  separate document.** It is a brief pre-announcement summary (566 words,
  no full minutes); the Bank later published the full minutes for that
  decision combined with the regularly scheduled 25 March meeting in a
  single document, which we already had (`minutes-2020-03`, confirmed by
  its own heading: "Minutes of the special Monetary Policy Committee
  meeting on 19 March 2020 and the Monetary Policy Committee meeting ending
  on 25 March"). Treating the 19 March summary as a second corpus entry
  would double-count that decision.
- **`raw_vote_text` field added to every document**: the verbatim sentence
  decision/vote were parsed from, whenever `find_vote_sentence` finds one -
  kept even when decision/vote don't fully parse, so no information is
  lost. Populated for 92 of 93 documents (all but the special meeting, whose
  vote sentence never states "Bank Rate" in the same clause as "voted").
- **Two documents keep a deliberately null vote, now with a preserved
  `raw_vote_text`:**
  - `2016-08`: the post-Brexit "package of measures" (Bank Rate cut bundled
    with a new Term Funding Scheme, corporate bond purchases and a QE
    expansion) is announced as "voted unanimously in favour of the
    propositions on Bank Rate and the Term Funding Scheme" - no single
    "voted ... to X%" clause exists to parse.
  - `2022-09`: a genuine three-way vote split (5 for +50bp, 3 for +75bp, 1
    for +25bp) - not representable as a single "A-B" pair. Unchanged from
    the previous entry; decision still parses.
- **`2015-10`'s meeting_end/published resolved itself** once the PDF
  backfill replaced the summary-only text: the PDF states "meeting ending on
  6 October 2015" (year included), where the HTML summary had omitted the
  year entirely. No manual date fix was needed. This was the one document
  that had fallen out of the 92-document series in the previous pass
  (excluded because meeting_end couldn't be parsed, so no `published` date
  existed to sort the series by) - now included, bringing the series to all
  93 documents.
- **Case-insensitive "Bank Rate" matching.** One PDF (2016-04) renders it
  "Bank rate" (lowercase r); `find_vote_sentence` now matches
  case-insensitively. Fixed a real false-null, not a new special case.
- **Post-repair word counts: zero documents under 1,000 words** (previous
  low was 679; new low is 2,606, in the short 2024 minutes). No individual
  per-document explanations needed since none remain under threshold.
