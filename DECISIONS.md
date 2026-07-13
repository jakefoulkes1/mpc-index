# Decisions log

Every methodological choice gets a dated line here, before it is used.
Changes apply forward only; nothing is retrofitted. Locked calls are never touched.

## Table of contents

- 2026-07-05 — [repo created](#2026-07-05--repo-created)
- 2026-07-11 — [era corpus, Aug 2015–Jun 2026](#2026-07-11--era-corpus-aug-2015jun-2026)
- 2026-07-11 — [corpus audit: full-text repair + special meetings](#2026-07-11--corpus-audit-full-text-repair--special-meetings)
- 2026-07-11 — [A&BG (2012) baseline lexicon](#2026-07-11--abg-2012-baseline-lexicon)
- 2026-07-11 — [voting-record parsing and reconciliation](#2026-07-11--voting-record-parsing-and-reconciliation)
- 2026-07-11 — [first validation pass (v1)](#2026-07-11--first-validation-pass-v1)
- 2026-07-11 — [site: A&BG chart, retiring starter_v0 fields from the UI](#2026-07-11--site-abg-chart-retiring-starter_v0-fields-from-the-ui)
- 2026-07-11 — [19 March 2020 special meeting added](#2026-07-11--19-march-2020-special-meeting-added)
- 2026-07-11 — [validation join fixed: voting-sheet date is canonical](#2026-07-11--validation-join-fixed-voting-sheet-date-is-canonical)
- 2026-07-11 — [neutral_value published in index.json](#2026-07-11--neutral_value-published-in-indexjson)
- 2026-07-11 — [member-behaviour table (seeds Stage 4)](#2026-07-11--member-behaviour-table-seeds-stage-4)
- 2026-07-11 — [market benchmark: OIS forward curve + SONIA](#2026-07-11--market-benchmark-ois-forward-curve--sonia)
- 2026-07-11 — [market_probs: two-state ±25bp assumption](#2026-07-11--market_probs-two-state-25bp-assumption)
- 2026-07-11 — [lock and scoring machinery](#2026-07-11--lock-and-scoring-machinery)
- 2026-07-11 — [site call card + dry run](#2026-07-11--site-call-card--dry-run)
- 2026-07-11 — [smoothed-curve bias: quantified, offset convention chosen](#2026-07-11--smoothed-curve-bias-quantified-offset-convention-chosen)
- 2026-07-11 — [2 null-decision documents recovered](#2026-07-11--2-null-decision-documents-recovered)
- 2026-07-11 — [historical market benchmark: data/market_history.csv](#2026-07-11--historical-market-benchmark-datamarket_historycsv)
- 2026-07-11 — [decision classifier bug found and fixed: Bank-Rate-adjacent verb, not first word](#2026-07-11--decision-classifier-bug-found-and-fixed-bank-rate-adjacent-verb-not-first-word)
- 2026-07-11 — [Part B sanity checks](#2026-07-11--part-b-sanity-checks)
- 2026-07-11 — [scipy added, for the ordered logit models only](#2026-07-11--scipy-added-for-the-ordered-logit-models-only)
- 2026-07-11 — [the benchmark ladder (first real backtest), L0-L4](#2026-07-11--the-benchmark-ladder-first-real-backtest-l0-l4)
- 2026-07-11 — [curve freshness fix](#2026-07-11--curve-freshness-fix)
- 2026-07-11 — [scheduled vs special meetings split; probability-clip logged](#2026-07-11--scheduled-vs-special-meetings-split-probability-clip-logged)
- 2026-07-11 — [live site investigation: false alarm, contract test added anyway](#2026-07-11--live-site-investigation-false-alarm-contract-test-added-anyway)
- 2026-07-11 — [data/surprises.csv](#2026-07-11--datasurprisescsv)
- 2026-07-11 — [the headline inference (Spec 3 OLS + Spec 2 ordered-logit LR test)](#2026-07-11--the-headline-inference-spec-3-ols--spec-2-ordered-logit-lr-test)
- 2026-07-11 — [Results section published to the site (ladder v1)](#2026-07-11--results-section-published-to-the-site-ladder-v1)
- 2026-07-11 — [lock rehearsal (dry run, fresh curve)](#2026-07-11--lock-rehearsal-dry-run-fresh-curve)
- 2026-07-12 — [site v2 (design, interactivity, context panel, annotations, methodology)](#2026-07-12--site-v2-design-interactivity-context-panel-annotations-methodology)
- 2026-07-12 — [evidence inspector (`pipeline/inspect.py`)](#2026-07-12--evidence-inspector-pipelineinspectpy)
- 2026-07-12 — [Track record section (`data/track_record.json`, `index.html`)](#2026-07-12--track-record-section-datatrack_recordjson-indexhtml)
- 2026-07-13 — [final polish: Spec 3 published, lexicon sparsity, repo front door](#2026-07-13--final-polish-spec-3-published-lexicon-sparsity-repo-front-door)
- 2026-07-13 — [ERRATUM: entry header dates corrected against commit evidence](#2026-07-13--erratum-entry-header-dates-corrected-against-commit-evidence)

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

## 2026-07-11 — corpus audit: full-text repair + special meetings

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

## 2026-07-11 — A&BG (2012) baseline lexicon

- **Source, retrieved and verified, not reconstructed from memory.** Apel &
  Blix Grimaldi (2012), "The Information Content of Central Bank Minutes",
  Sveriges Riksbank Working Paper No. 261. The SSRN/EconStor mirrors
  bot-blocked our scraper; the actual PDF came from the original
  riksbank.se URL listed on the paper's S-WoPEc/RePEc abstract page
  (swopec.hhs.se/rbnkwp/abs/rbnkwp0261.htm). Saved verbatim, with page
  references, to `pipeline/score/lexicon/abg_2012.json`.
- **The Net Index formula (p.10) and the term appendix (p.18) are images/
  table objects in the PDF, not extractable as plain text** - pdfplumber's
  text layer renders the formula as `[( ) ( )]` with the interior blank, and
  the appendix table's columns run together in plain-text extraction. Both
  were confirmed by cropping the PDF region to an image and reading it
  directly, not inferred: `Net Index = [(#hawk/(#hawk+#dove)) -
  (#dove/(#hawk+#dove))] + 1`, range [0, 2], 1 = neutral.
- **The paper's method is two-word noun+adjective bigrams, not a single-word
  sentiment list and not sentence-level.** "Higher inflation" = hawkish,
  "lower growth" = dovish. It counts over the whole document, with no
  sentence splitting at all - the earlier task wording assumed
  "(sentence-level)"; the paper itself does not do this, and "implement the
  paper's index construction as described in the paper" takes priority, so
  `pipeline/score/abg.py` matches the paper: no sentence splitting.
- **Core noun list used for the primary index: 7 nouns** (inflation, price,
  wage, oil price, cyclical position, growth, development), matching the
  paper's main Net Index (Table 1/2, p.9-10). The paper's 4-noun extension
  (employment, unemployment, recovery, cost) was only used for a robustness
  check ("Net Index Extended") in the original paper, not its primary
  result - stored in abg_2012.json for reference but not used by
  `abg.py`'s default index.
- **Adjective-noun adjacency and match direction: immediately adjacent,
  adjective-then-noun** ("higher inflation", not "inflation is higher").
  The paper doesn't state an explicit token window for the English
  translation; adjacency in the stated direction is the most literal
  reading of its own worked examples and is what's implemented. Logged as
  an interpretation, not verbatim from the paper.
- **No negation window, no sentence-level scoring, no other extras from
  `pipeline/score/dictionary.py` (starter_v0's machinery) applied to the
  A&BG index** - run plain, per instruction. `dictionary.py` and
  `starter_v0.json` remain in the repo (starter_v0 is how the walking
  skeleton was proven end-to-end) but are no longer used in `index.json` or
  any other output from this point on. `abg_2012` is now the only index
  used for analysis and claims, matching the original 2026-07-05 entry's
  intent.
- **index.json schema bumped to `index-v1`**: `net_hawkishness` /
  `hawkish_hits` / `dovish_hits` / `n_sentences` / `n_scored_sentences`
  (starter_v0 fields) replaced by `abg_hawk` / `abg_dove` /
  `abg_net_index` on every document and in the series.

## 2026-07-11 — voting-record parsing and reconciliation

- **`data/votes.csv` join key is the sheet's own date column, which is the
  meeting's PUBLISHED/announcement date, not `meeting_end`** - confirmed by
  cross-checking known dates (e.g. the sheet's 2026-06-18 row matches
  minutes-2026-06's `published` field exactly, while its `meeting_end` is
  2026-06-17). `skew = average(all voting members' preferred rate) -
  decided rate`, per the paper's own formula (p.13, after Gerlach-Kristen
  2004): `skew = average(r_j) - r`. `hawkish_dissents`/`dovish_dissents`
  count members whose preferred rate was above/below the decided rate.
- **Every voting member's preferred rate is recorded every meeting they sat
  on, not just dissenters'** - confirmed against a known case (June 2026:
  the sheet shows 7 members at 3.75% and 2 at 4%, exactly matching the
  corpus's own parsed "7-2" vote). This makes the per-member preferred-rate
  column meaningful for all 9-ish sitting members each meeting, not just
  the minority.
- **Era filter applied (Aug 2015-Jun 2026), same as the text corpus.** A
  few pre-2015 rows (not in our range) record a dissent as qualitative
  "Increase"/"Decrease" text with no specific rate; these are sidestepped
  by the era filter rather than needing special handling.
- **Reconciliation against the text corpus (`published` date, exact match)
  found only the same 4 one-day gaps already logged for the `meeting_end +
  1 day` publication-date rule** (2015-10, 2020-08, 2021-06, 2021-11) -
  independent confirmation from a second data source that the earlier
  finding was real, not a fluke of parsing.
- **One extra sheet-only date: 2020-03-19.** The voting sheet records the
  19 March 2020 emergency cut as its own distinct decision (with its own
  row and vote), even though the Bank's own minutes publication folded its
  text into the 25 March combined document (see the 2026-07-18 corpus-audit
  entry above, on why no separate 19 March text document was added). No
  action taken - the voting record and the text corpus are allowed to
  disagree on document boundaries; this is noted, not corrected.

## 2026-07-11 — first validation pass (v1)

- **Contemporaneous only, not predictive.** `pipeline/validate.py` compares
  a meeting's own minutes (abg_net_index) against that SAME meeting's own
  skew/dissents/decision - not the paper's own predictive framing (Net
  Index at t vs the rate decision at t+1). Matches the task's explicit
  scope ("do not build anything about... prediction yet - that is Stage
  3"). A lagged/predictive version is future work for Stage 3.
- **No scipy dependency added.** Pearson and Spearman implemented in plain
  Python (`pipeline/validate.py:pearson/spearman/rank`) rather than adding
  a new heavy dependency for two formulas.
- **87 of 93 corpus meetings joined to a voting-sheet row** (published date
  exact match). The 2020-03-10 special meeting and 2016-08 are excluded by
  construction (their `decision` field is null, so `load_corpus_by_published`
  never considers them a candidate at all). The other 4 unjoined are the
  known one-day `meeting_end+1` mismatches already logged in the corpus-audit
  and voting-record entries above (2015-10, 2020-08, 2021-06, 2021-11).
- **v1 result: weak positive correlation.** r(abg_net_index, skew) =
  0.181 (Pearson), 0.143 (Spearman), n=87. r(abg_net_index, net dissents)
  = 0.198 (Pearson), 0.152 (Spearman), n=87. Mean abg_net_index by decision:
  hike 1.44 (n=16), hold 0.97 (n=65), cut 1.00 (n=6) - directionally
  sensible (hikes read more hawkish) but a small, noisy signal on this
  first pass. Saved to `data/validation_v1.json`; not a claim of predictive
  power, just the first descriptive checkpoint.

## 2026-07-11 — site: A&BG chart, retiring starter_v0 fields from the UI

- **Hand-rolled inline SVG, no chart library, no CDN.** The site is static
  GitHub Pages with no build step; a CDN script is one more thing that can
  fail to load or change behind our back. The chart is built directly in
  `index.html`'s `renderChart()` from the same `data/index.json` fetch
  already used by the latest-document card.
- **Existing "latest scored document" card kept, but its JS updated to the
  new schema** - it was still reading `net_hawkishness`/`hawkish_hits`/
  `dovish_hits`/`n_sentences` (removed from index.json in the abg_2012
  cutover above), which would have silently broken the card. Now reads
  `abg_net_index`/`abg_hawk`/`abg_dove`.
  Displayed on the paper's own 0-2 scale (1 = neutral) with the
  hawkish/dovish colour and left/right position on the existing gradient
  bar recentred (`net = abg_net_index - 1`) so the bar's existing -1..+1
  visual language still works.
  Footer's stale "current lexicon is a plumbing placeholder" line corrected
  to name the A&BG citation.
- **Chart decision markers use the same hike/hold/cut classification as
  `pipeline/validate.py`** (first word of the `decision` field: "increase"
  = hike, "reduce" = cut, holds unmarked) - one classification rule, not
  two independently-maintained ones.

## 2026-07-11 — 19 March 2020 special meeting added

- **Diffing `data/votes.csv` against the corpus found exactly one genuinely
  missing meeting: 19 March 2020**, the second Covid-19 emergency decision
  (Bank Rate cut 0.25%->0.1%, +£200bn asset purchases). The raw diff showed
  5 votes-only dates, but 4 were already-known 1-day `meeting_end+1`
  mismatches (each paired with a corpus-only date exactly 1 day earlier) -
  excluding those pairs left exactly one unpaired date, confirming the
  expectation.
- **Re-verified, not assumed, that this meeting has no separate minutes
  PDF**, despite the task's premise that it does: re-fetched the live page
  (no `.pdf` link at all) and re-searched the Bank's sitemap for any
  19-March-specific minutes document - none exists. The page's own text
  confirms why: "The minutes of today's special meeting will be released
  at the same time" as the 25 March meeting's minutes - i.e. folded into
  the combined document we already have as `minutes-2020-03`, consistent
  with the 2026-07-18 entry's finding and decision not to duplicate that
  text under a second doc_id.
- **Added as its own document anyway**, using the Bank's brief "Monetary
  Policy Summary for the special Monetary Policy Committee meeting on 19
  March 2020" page (563 words, no full minutes) - a real, distinct,
  citable published document for this specific decision, not a duplicate
  of the 25 March text. `doc_id minutes-2020-03-19-special`, `type
  special_minutes`, `source_kind html`. Word count is genuinely low
  (563 < 1,000) for the same reason logged for every other pre-Aug-2021
  Summary-only page - no fuller text exists to backfill from here, since
  there is no PDF at all.
- **`MEETING_END_RE` broadened for a third real phrasing variant**: this
  page's only date-bearing heading reads "special Monetary Policy
  Committee meeting on 19 March 2020" (no "ending"). Added as an
  alternative prefix in the same regex, alongside the existing "meeting
  ending (on) <date>" pattern - not a new mechanism, same category of fix
  as the earlier "ending" vs "ending on" and case-insensitivity fixes.
- **`decision` field is a compound, verbatim sentence** ("increase [asset
  purchases]... and to reduce Bank Rate by 15 basis points to 0.1%") since
  the source sentence itself bundles an asset-purchase vote and a Bank
  Rate vote under one "voted unanimously to..." clause. Left as-is
  (accurate and unfabricated, just verbose) rather than hand-splitting it,
  consistent with not writing per-document special-case text.
- **`published` computed by the same uniform `meeting_end+1` rule as every
  other document (2020-03-20), not hand-corrected to the sheet's same-day
  announcement (2020-03-19).** The field-level rule stays uniform, applied
  forward only; the resulting known 1-day gap is handled at the join layer
  instead (`pipeline/validate.py`, see below), not by carving out a
  per-document exception in `build_index.py`.
- **New test: `test_date_reconciliation.py`.** Corpus `published` dates and
  `data/votes.csv` meeting dates now match one-to-one within a 1-day
  tolerance for the whole Aug 2015-Jun 2026 era (5 known 1-day gaps: the 4
  already-logged `meeting_end+1` mismatches plus this new special meeting,
  all real and individually explained above and in the 2026-07-18 entries
  - none silently absorbed).

## 2026-07-11 — validation join fixed: voting-sheet date is canonical

- **`pipeline/validate.py` no longer joins on exact match against our own
  `published` field.** It now treats each corpus document's `published`
  date as an approximate label and matches it to its NEAREST voting-sheet
  date, within a `MAX_DAY_TOLERANCE` of 3 days (comfortably above the
  largest known real gap of 1 day - see the two entries above). Every
  document that still can't be matched within tolerance is excluded AND
  individually logged (`join_to_votes` returns an `unmatched` list with the
  gap that caused the exclusion), not silently dropped.
- **Result: 92 of 92 candidate documents joined (0 unmatched)**, up from
  87 of 91 under the old exact-match join. The `index.json` `published`
  field itself is unchanged (still the uniform `meeting_end+1` rule,
  applied forward only) - only the validation join's matching logic
  changed.
- **Validation output filename stays `data/validation_v1.json`** (not
  renumbered) even though the internal `schema` field is now
  `validation-v2`, reflecting the join-logic and delta-index additions -
  the file is overwritten by each `python -m pipeline.validate` run either
  way, so a new filename would only be warranted for a result meant to
  stand alongside the old one for comparison, which isn't the case here.
- **Added `delta_index`**: `abg_net_index` minus the previous document's,
  in the corpus's own chronological order (not the previous *matched*
  document - the corpus's own sequence). Correlated against skew and net
  dissents the same way as the level. First document in the corpus has no
  `delta_index` (nothing to difference against) and is excluded only from
  the delta correlations, not the level ones.
- **Level vs delta result: level correlates weakly with skew/dissents
  (r=0.18/0.20, n=92); delta correlates barely at all (r=0.07/0.06,
  n=91).** The tone's absolute level in a given meeting's minutes is a
  (weak) better read on that meeting's own dissent pattern than the
  *change* in tone since the previous meeting is. Reported side by side in
  `data/validation_v1.json`, not chosen between - both are genuinely small
  effects at this stage, not evidence either framing is "the right one".

## 2026-07-11 — neutral_value published in index.json

- **Formula and range re-confirmed against the paper, unchanged**: Net
  Index = [(#hawk/(#hawk+#dove)) - (#dove/(#hawk+#dove))] + 1 (p.10,
  `pipeline/score/lexicon/abg_2012.json`), a ratio-type measure with a
  fixed theoretical range of [0, 2] and neutral at 1.0 (the ratio's own
  midpoint when hawk and dove counts are equal, not a fitted or sample
  statistic). No change to the formula itself - only its neutral point is
  now surfaced as data.
- **`NEUTRAL_VALUE = 1.0` added as a named constant in
  `pipeline/score/abg.py`** (used for both the empty-document fallback and
  as the source of truth for `index.json`'s new top-level `neutral_value`
  field), rather than a bare `1.0` scattered across `abg.py`,
  `build_index.py`, and `index.html`'s JS. The chart's neutral gridline
  and the latest-document card's recentring (`net = abg_net_index -
  neutral`) both now read `data.neutral_value` instead of a hardcoded `1`,
  so a future change to the formula's neutral point (there isn't one
  planned) wouldn't require hunting down every hardcoded copy.

## 2026-07-11 — member-behaviour table (seeds Stage 4)

- **Three-state coding, not binary.** Each member-meeting from
  `data/votes.csv` is coded `hawkish_dissent` (preferred > decided),
  `dovish_dissent` (preferred < decided), or `with_majority` (equal) -
  keeping direction distinguishable rather than collapsing to a plain
  dissent/no-dissent flag, since the paper's own `skew` measure and this
  repo's `hawkish_dissents`/`dovish_dissents` fields already treat
  direction as meaningful.
  A single "dissent" headline (`dissent_stickiness`) is still reported by
  collapsing the two dissent states together, since that's the plain-
  English number asked for - but the underlying 3-state matrix is what's
  saved, not thrown away.
- **Transition matrix is "next meeting this member actually voted at",
  not "next calendar meeting".** A member's own row-to-row sequence in
  `data/votes.csv`, sorted by date - naturally handles the (rare) case of
  a member missing a meeting, without needing to special-case gaps.
- **Pooled across all members, not computed per-member.** Most members sit
  for a few dozen meetings at most; a 3x3 transition matrix per member
  would have single-digit or zero counts in most cells. Pooling loses the
  "is member X personally sticky" question (deferred to Stage 4, which is
  explicitly what this table is seeding) but keeps every reported n
  large enough to read as a real proportion, not noise.
- **Descriptive only, explicitly**: no smoothing, no confidence intervals,
  no model fit. `dissent_stickiness` and the transition matrix are counts
  and empirical proportions from `data/votes.csv`, nothing else. Saved to
  `data/member_behaviour_v1.json`.
- **Headline result: dissent is genuinely sticky.** P(dissent again |
  dissented) = 0.475 (n=118) vs P(dissent | currently with majority) =
  0.094 (n=701) - roughly a 5x difference. Directionally sticky too:
  hawkish dissenters transition straight to dovish dissent 0% of the time
  (0/65) and vice versa (0/53) - dissenters who flip, flip to "with
  majority" first, never straight to the opposite direction, in this
  sample.

## 2026-07-11 — market benchmark: OIS forward curve + SONIA

- **Both sources parse cleanly - no hard stop triggered.** OIS:
  bankofengland.co.uk/statistics/yield-curves -> "oisddata.zip" (daily OIS
  data) -> sheet "1. fwds, short end" ("UK instantaneous OIS forward
  curve"), row 3 = maturities in whole months (1-60), each subsequent row
  one business day (date + forward rate per maturity, percent p.a.).
  SONIA: the Bank's Interactive Statistical Database CSV export, series
  code IUDSOIA.
- **The OIS zip contains one .xlsx per era, and older eras use a different
  sheet layout** (2009-2015's file has "1. fwd curve"/"2. spot curve", not
  "1. fwds, short end" at all) - confirmed by trying, not assumed.
  `latest_forward_curve()` tries every extracted file, skips (and logs)
  any without the expected sheet, and picks whichever remaining file has
  the most recent date - not a hardcoded filename like "2025 to
  present.xlsx", since era boundaries will themselves move in future
  years and a hardcoded name would silently go stale.
  Hard-stops only if NONE of the era files have a usable sheet.
- **The OIS file is a periodic snapshot, not literally live**: as of
  writing, its latest row is 2026-06-30 while SONIA's CSV export is current
  to 2026-07-08 - a real few-day publication lag between the two sources,
  not a bug. `market_probs.py` (next entry) must not assume the two
  `as_of_date`s match.
- **`fetch_sonia`'s HTTP call and `parse_sonia_csv`'s parsing are separate
  functions** (same pattern as `pipeline/build_votes.py`'s
  load_member_columns/parse_meetings split) specifically so the parser can
  be unit-tested against a fixture string without a live call - required
  by the task ("Unit-test with synthetic curve fixtures - no live calls
  inside tests"). Same reasoning applied to
  `_read_forward_curve_sheet(path)`, which takes a path rather than doing
  its own download, tested against a small synthetic workbook.
- **Raw downloads cached under `data/raw/market/`** (gitignored, same
  convention as `data/raw/` generally - only derived outputs are public).

## 2026-07-11 — market_probs: two-state ±25bp assumption

- **`pipeline/predict/market_probs.py` implements one documented,
  deliberately simple mapping from implied rate change to {cut, hold,
  hike} probabilities - not the only reasonable choice, and not fitted to
  anything.** implied_change_bp = (forward rate at the maturity bucket
  just after the meeting) - (current SONIA). A "two-state" assumption:
  the market is assumed to price a single possible move in ONE direction
  only (never a simultaneous hike probability and cut probability at the
  same meeting), of a fixed size (`ASSUMED_MOVE_BP = 25`, the Bank's usual
  step). `p_hike/p_cut = clip(|implied_change_bp| / 25, 0, 1)` in the
  appropriate direction; the remainder is `p_hold`. Real market-implied
  distributions can price partial/multi-directional moves or step sizes
  other than 25bp - this is a simplification, stated as one, not hidden.
- **"Maturity bucket just after the meeting"** = the first available
  monthly maturity whose distance from the curve's `as_of_date` is >= the
  distance to the meeting date (`bisect_left` on the sorted maturities
  list), clipped to the longest available maturity if the meeting is
  further out than the curve covers.
- **Unit-tested entirely against synthetic curve/SONIA dicts - no live
  HTTP calls in tests**, per instruction. `market_probs_for_meeting()`
  takes plain dicts shaped like `ois.latest_forward_curve()` /
  `ois.latest_sonia()`'s return values, not the fetch functions
  themselves, so tests never touch the network.

## 2026-07-11 — lock and scoring machinery

- **Running `pipeline/predict/lock.py` is not itself "the lock".** It
  writes a timestamped snapshot with `point_call`/`rationale` left as
  `null`/a `TODO(Jake)` placeholder - filling those in by hand, then
  committing the file, is what actually constitutes a locked call. The
  script's job is just to freeze the market-only reference (`m0`) and the
  index readings at a moment in time, reproducibly.
- **Reproducibility fields**: `code_version` (`git rev-parse HEAD`) and
  `input_hashes` (sha256 of `data/index.json` as it stood, plus a sha256
  of the OIS curve + SONIA snapshot actually used) - so a later reviewer
  can check exactly which corpus and market state a given lock was made
  against, without needing git history archaeology.
- **`index_trailing_mean` = mean of the last 4 documents' `abg_net_index`
  in the corpus's own published order** - a simple recency-weighted
  baseline for "how hawkish has tone been lately", not a fitted or
  seasonally-adjusted average. 4 was chosen as roughly a year's worth of
  the current 8-meetings-a-year schedule.
- **`build_prediction(meeting_date, curve=None, sonia=None)` accepts
  optional pre-fetched curve/sonia** so its output schema can be
  unit-tested without a live call (same dependency-injection pattern as
  `market_probs_for_meeting`) - defaults to live fetches when called from
  the CLI.
- **Brier score is the standard 3-class formula** (sum of squared
  differences between predicted probability and the {0,1} actual outcome
  indicator across all 3 classes), range [0, 2]. **Log score** is
  `-log(p_actual)`, floored at `p >= 1e-9` to avoid `-log(0)` for a
  confidently-wrong call.
- **`always_hold_reference`** is a fixed `p_hold=1` forecast, not fitted
  to the corpus's own hold/hike/cut base rates - the simplest possible
  baseline (predict the modal, most common outcome always), which any
  real forecast needs to beat. A base-rate-fitted reference is a
  reasonable future addition but wasn't asked for here.

## 2026-07-11 — site call card + dry run

- **The call card's dry-run vs locked styling is data-driven, not a
  hardcoded label.** `renderCallCard()` checks `point_call !== null`
  to decide which CSS class/badge to apply - a hatched, dashed-border,
  muted-gold "DRY RUN · NOT A FORECAST" badge when null, a solid gold
  border and "LOCKED CALL" badge (showing the actual point call and
  rationale) once a human fills `point_call` in. Same code renders both
  states correctly; verified visually with a synthetic locked payload
  before committing (not itself committed - see below).
- **Card fetches a fixed path, `data/predictions/dryrun-2026-07.json`**,
  not a directory listing (static GitHub Pages has no server-side
  directory index). A later real lock will need either overwriting this
  same path or updating the fetch path in index.html - a manual step, not
  automated, consistent with "running lock.py is not itself the lock".
- **Ran end-to-end with live data**: `python -m pipeline.predict.lock
  2026-07-30 dryrun-2026-07`. Result: OIS curve as of 2026-06-30 (3.7299%
  1-month forward) vs SONIA 3.7303% (2026-07-08) implies essentially no
  priced move (-0.04bp) -> p_hold=0.999, p_cut=0.001, p_hike=0.0 for the
  30 July announcement. A&BG index for the latest document (minutes-2026-06)
  is 1.714, well above its trailing 4-document mean of 1.054 (+0.661) -
  tone reads considerably more hawkish than its recent average, while the
  market itself prices almost no chance of a near-term move. This
  divergence is exactly the kind of gap the site's thesis is about - noted
  here as an observation, not a call. No point_call was made; this is
  m0 (market-only) only, per the task's explicit "DRY RUN and no locks
  today" instruction.
- **No `lock-*` named files, no git tag created** - the dry-run output is
  named `dryrun-2026-07.json`, distinguishing it structurally (not just
  by content) from any future actual locked call, which would need its
  own deliberately-named file.

## 2026-07-11 — smoothed-curve bias: quantified, offset convention chosen

- **Known limitation confirmed and quantified, not just asserted.** The
  Bank's published OIS forward curve is a fitted spline across maturities,
  which smooths over the discrete jump that actually happens in Bank Rate
  on a meeting date - the curve's value exactly AT the meeting understates
  the priced move and biases `implied_probs` toward hold. Quantified on
  today's live curve (2026-06-30) for the three upcoming meetings:
  implied_change_bp at-meeting vs +3 days vs 2-week-average was -0.04 /
  0.25 / 0.76 (30 Jul), 5.70 / 6.08 / 6.66 (17 Sep), 12.44 / 12.86 / 13.50
  (5 Nov) - a small but real and monotonic effect in the expected
  direction under today's fairly flat curve; expected to be larger under
  more steeply sloped historical curves (e.g. the 2021-2023 hiking cycle),
  to be confirmed once Part B's historical build runs.
- **Convention chosen: forward rate 3 days after the meeting date
  (`LOCK_OFFSET_DAYS = 3`), linearly interpolated between the curve's
  adjacent whole-month buckets - not a 2-week average, and not the
  meeting date itself.** The 2-week-average alternative was computed and
  rejected: it recovers slightly more of the bias (see numbers above), but
  during the Aug 2015-2016 monthly-MPC era a 2-week window is roughly HALF
  the inter-meeting gap, risking real contamination from the NEXT
  meeting's own priced expectations - a bigger problem for a benchmark
  that must run across that entire era than the extra ~0.5-0.6bp of bias
  correction is worth. +3 days is safely inside even the shortest
  historical gap (~4 weeks).
- **Interpolation is required for either convention to mean anything, not
  optional.** The curve's maturities are whole months only; "nearest
  bucket after" (the previous implementation) would make a 3-day shift
  either do nothing (if the meeting isn't near a bucket boundary) or jump
  an entire month's worth of curve (if it is) - neither reflects a "3 days
  later" quantity. `interpolated_forward_rate()` now does linear
  interpolation between the two adjacent whole-month buckets for an
  arbitrary real-valued maturity; `forward_rate_for_date()` evaluates it
  at `meeting_date + 3 days`, converted to months via the existing
  average-days-per-month convention. Same data source as before (the
  Bank's own OIS spreadsheet) - only the evaluation point within that
  curve changed, per instruction ("do not switch data sources").
- **Applied everywhere**: this is the only forward-rate lookup function in
  the codebase (`pipeline/predict/market_probs.py`), used by both the
  live dry-run card and (from here on) the historical backtest in Part B
  - one convention, not two parallel implementations.
- **`lock_offset_days` added to `market_probs_for_meeting()`'s output**
  so any consumer (site, CSV, tests) can see which convention a given
  probability was computed under, without needing to read this entry.
- **Diagnostic table run against today's live data (2026-06-30 curve,
  SONIA 3.7303% as of 2026-07-08) found NO horizon-indexing bug**: hike
  probability increases monotonically and sensibly with horizon (0.0% at
  30 Jul, ~29-31% at 17 Sep, ~63-65% at 5 Nov, varying slightly by
  convention above) - the anticipated failure mode ("hike probability ~0
  even at November despite an upward-sloping curve") was checked for and
  not found; bucket selection was also spot-checked across a 0.5-24 month
  range and confirmed monotonic. No fix was needed for this; the
  investigation is recorded so the check isn't silently skipped.

## 2026-07-11 — 2 null-decision documents recovered

- **The 94-corpus/94-voting-sheet join reporting only 92 candidates was
  exactly the 2 already-logged null-decision documents** (`minutes-2016-08`
  and `minutes-2020-03-10-special`) - both excluded from
  `load_corpus_documents()` by construction (it requires both `published`
  and `decision`). No undocumented exclusion existed; confirmed by
  listing every document with `decision is None` and finding exactly
  these two, matching 94 - 2 = 92.
- **Both recovered from a real, shared pattern, not guessed.** Both are
  "package of measures" meetings (2016-08's post-Brexit stimulus; 2020-03-10's
  first Covid-19 emergency cut) where the actual VOTE_RE-matched sentence
  ("voted unanimously in favour of the propositions") never restates the
  rate, but an earlier sentence does: "The Governor invited the Committee
  to vote on the propositions that: Bank Rate [should be/be] reduced by N
  basis points to X%". `try_proposition_fallback()` in `build_index.py`
  only fires when BOTH halves of this pair are found - the proposition
  statement AND a later "voted (unanimously | by a majority of A-B) in
  favour of ... propositions" confirming it was adopted - so it can't
  attach a rate to a proposition that was never actually put to a vote,
  or vice versa. Tested for both the happy path and the "proposition
  stated but never confirmed" case explicitly staying null.
- **Result: 2016-08 = "reduce Bank Rate by 25 basis points to 0.25%",
  unanimous. 2020-03-10-special = "reduce Bank Rate by 50 basis points to
  0.25%", unanimous.** Both match known history. Validation join now
  covers all 94 of 94 candidate documents (up from 92 of 92, since the
  candidate pool itself grew by the 2 recovered documents).
- **This is a general mechanism, not two special cases hardcoded per
  document** - if a future meeting uses the same Governor's-proposition
  phrasing, it will be recovered automatically without a code change.

## 2026-07-11 — historical market benchmark: data/market_history.csv

- **"Archive files ... by year" turned out to be one multi-era zip, not
  one file per calendar year** - confirmed by re-reading the yield curves
  page's own text ("Daily overnight index swap curve: archive data")
  rather than assumed: it's the same `oisddata.zip` already used for the
  live dry-run, containing "2009 to 2015", "2016 to 2024", "2025 to
  present" era files. No new download endpoint was needed.
- **The 2009-2015 era file names its forward-curve sheet "1. fwd curve"
  instead of "1. fwds, short end"** (used by the 2016+ files) - checked
  by hand and confirmed structurally identical (same maturity-months row,
  same layout). `pipeline/market/ois.py`'s `_read_forward_curve_sheet`
  now accepts a tuple of candidate sheet names and tries each in order,
  used with both names for the full-history build and just the current
  name for the live lookup.
- **Full history requires every era file to parse - hard stop, not skip.**
  `latest_forward_curve()` (live lookup) can safely skip an era file with
  neither known sheet name, since it only needs the most recent one. The
  new `load_full_curve_history()` (Part B) hard-stops instead if any era
  file matches neither name - a full Aug 2015-present history silently
  missing a whole era would be a much worse failure than the live lookup
  skipping old data it was never going to use anyway.
- **Lock date = announcement - 2 calendar days**, walked back one day at a
  time if that date isn't present in the curve data (a weekend or bank
  holiday is simply absent as a row - no separate UK holiday calendar was
  built; the data itself is the trading calendar). Same mechanism used
  for the SONIA lookup at the lock date. `find_nearest_available_date()`
  in `pipeline/market/ois_history.py`, capped at a 10-day walk-back before
  hard-stopping (never silently substitutes an arbitrarily old date).
- **In practice, zero walk-backs occurred across all 94 meetings.** MPC
  announcements are (with rare exception) Thursdays, so announcement-2d
  lands on a Tuesday - essentially never a UK bank holiday, and December
  meetings land well clear of Christmas/New Year (checked by hand:
  earliest Dec lock date across the corpus is 8 Dec, latest 18 Dec).
  Confirmed this is a real property of the MPC calendar, not a silent
  bug in the walk-back logic (also unit-tested directly with a synthetic
  weekend gap).
- **`forward_rate_for_date` from `pipeline/predict/market_probs.py` is
  reused unchanged** for the historical build (curve `as_of_date` = lock
  date, `meeting_date` = announcement) - one implementation of the
  LOCK_OFFSET_DAYS=3 convention for both the live card and the historical
  backtest, per the earlier instruction not to have two parallel
  conventions.
- **`build_rows()` is a pure function** (curve/SONIA history passed in,
  no I/O) so it's unit-tested against synthetic fixtures including an
  explicit weekend-gap walk-back case, without a live call; `main()`
  wires it to the real downloads. `data/market_history.csv` columns:
  `meeting, lock_date, sonia, forward, implied_change_bp, p_cut, p_hold,
  p_hike, source_file`.
- **Result: all 94 corpus meetings covered, no hard stops.** Notable
  sanity spot-check: Dec 2022 (height of the 2022 hiking cycle) shows
  `p_hike = 1.0` (implied change 62.31bp, well over the assumed 25bp
  move, clipped) - the kind of result that should show up at the extremes
  and does.

## 2026-07-11 — decision classifier bug found and fixed: Bank-Rate-adjacent verb, not first word

- **Found while running the Part-B sanity checks, not before**: the
  "5 most-wrong meetings" table initially put `minutes-2020-03-19-special`
  in 2nd place as a supposed "hike" the market gave 0% probability to -
  but that meeting was actually a CUT (Bank Rate 0.25%->0.1%). Its
  `decision` text is a compound sentence - "increase the Bank of
  England's holdings of [assets] ... and to reduce Bank Rate by 15 basis
  points to 0.1%" - and every classifier in the codebase
  (`pipeline/validate.py`, index.html's chart markers) took the FIRST
  WORD of the decision string ("increase") rather than the verb actually
  adjacent to "Bank Rate" ("reduce"). One document, out of all 94, was
  affected - checked by running the new classifier against every
  document's decision text and diffing against the old first-word
  result: exactly this one mismatch, no others.
- **Fixed with one shared function, not three separate patches.**
  `pipeline/decision_label.py:classify_decision()` finds the verb
  immediately before "Bank Rate" via regex
  (`(increase|reduce|maintain)\w*\s+Bank Rate`), not the first word of
  the string. `pipeline/validate.py` and index.html's chart-marker JS
  both now use this one rule (the JS re-implements the same regex, since
  it can't import Python) instead of two independently-maintained
  first-word copies that could drift apart again.
- **Downstream corrections**: `mean_abg_index_by_decision.cut.n` in
  `data/validation_v1.json` went from 6 to 9 (the 2 decisions recovered
  earlier this session plus this reclassification), `hike.n` unaffected.
  The "5 most-wrong" sanity check (below) now correctly shows Nov and Dec
  2021, as expected, instead of being pushed down by this misclassified
  entry.

## 2026-07-11 — Part B sanity checks

- **(a) Mean p_hike at lock across the 14 consecutive hikes (Dec 2021 -
  Aug 2023): 0.9225** - far above the corpus-wide hike base rate of
  0.1702 (16 of 94 meetings), as expected: the market correctly priced
  near-certain hikes through most of the cycle (12 of 14 meetings show
  p_hike = 1.0, i.e. an implied change >= the assumed 25bp move size).
  The two exceptions are informative, not noise: Dec 2021 (p_hike=0.29,
  the first hike of the cycle, not yet fully anticipated - see below) and
  Mar 2023 (p_hike=0.625, during the SVB/Credit Suisse banking-stress
  week, when a hike was less certain).
- **(b) Five most-wrong meetings (highest 1 - p(actual outcome)):**
  1. `minutes-2016-07` (actual hold, p_cut=1.0, p_actual=0.0) - the
     market was CERTAIN of a post-referendum cut that didn't arrive until
     August's "package of measures" the following month.
  2. `minutes-2023-09` (actual hold, p_hike=0.889, p_actual=0.111) - the
     Bank held for the first time after 14 straight hikes; the market
     hadn't caught up to the pause.
  3. `minutes-2021-12` (actual hike, p_hold=0.710, p_actual=0.290) - the
     first hike of the cycle, one meeting after the market had just been
     burned by November's hold (below) - underpriced.
  4. `minutes-2021-11` (actual hold, p_hike=0.688, p_actual=0.312) - the
     well-known "dovish surprise": the market had priced a near-certain
     hike and the Committee held.
  5. `minutes-2020-03-19-special` (actual cut, p_hold=0.612,
     p_actual=0.388) - the second Covid-19 emergency cut, days after the
     first; the two-state model's 25bp assumed-move size understates how
     large emergency moves can be (this one was 15bp, priced against a
     0.1%-away curve reading that had just also absorbed the 10 March
     cut - a genuinely unusual week, not a fitting error).
  Nov 2021 and Dec 2021 both appear, as expected. All five are real,
  independently-recognisable market surprises, not artefacts.

## 2026-07-11 — scipy added, for the ordered logit models only

- **scipy added as a dependency, deliberately narrower in scope than it
  sounds.** The earlier choice (2026-07-25) to implement Pearson/Spearman
  by hand rather than add scipy still stands for those - they're
  closed-form formulas, not worth a dependency. An ordered logistic
  regression MLE fit (L2/L3 in the benchmark ladder) is a different order
  of complexity: a numerically stable iterative optimizer with a genuine
  convergence/non-convergence distinction (which the task's own wording
  anticipates - "if an ordered-logit window fails to converge"). Writing
  a bespoke Newton-Raphson/IRLS implementation by hand would be
  re-deriving what scipy.optimize already does robustly, with more risk
  of a subtle numerical bug than the dependency is worth.
- **`pipeline/predict/ordered_logit.py`: proportional-odds model, 3
  classes (cut/hold/hike), fit by direct MLE** (`scipy.optimize.minimize`,
  BFGS) rather than an existing statsmodels/sklearn ordinal-regression
  implementation - kept to the one additional dependency, not two.
  Cutpoint ordering (tau_0 < tau_1) is enforced by reparameterising
  tau_1 = tau_0 + exp(delta) and fitting unconstrained.
- **Convergence check is two-part, not just scipy's own success flag.**
  Tested against synthetic data: a hard, noiseless 3-class threshold (no
  overlap anywhere) is a genuine quasi-complete-separation case where the
  optimizer can keep improving the likelihood by pushing a cutpoint
  towards +-infinity - it reports `success=True` while landing on a
  degenerate fit. Added a second check (`|any fitted parameter| > 50`) to
  catch this specifically; a fit failing either check is `converged =
  False`. Verified this actually fires on the deterministic-threshold
  test case and does NOT fire on realistic noisy synthetic data or a
  well-separated-but-still-noisy case (unit-tested for both).

## 2026-07-11 — the benchmark ladder (first real backtest), L0-L4

- **Outcomes coded by SIGN only, magnitude ignored**, per instruction: a
  50bp move counts the same as a 15bp move in the same direction. Uses
  the same `classify_decision()` as everywhere else in the codebase (one
  classifier, see the earlier 2026-08-01 entry on the first-word bug).
- **Evaluation window: Jan 2019-present, 62 meetings.** Training starts
  from the very first corpus document (Aug 2015) for every evaluation
  meeting - "fit on strictly prior meetings only" means the training set
  grows with each step (`records[:i]`), never using meeting i or later.
- **L3's `index_level` and `skew` are BOTH the PREVIOUS meeting's values,
  not the target's own - a judgment call, not a literal reading of the
  task text, and flagged prominently (module docstring, this entry, and
  the final report).** The task's wording explicitly lags skew ("last
  meeting's vote skew") but not index_level. A meeting's own minutes (and
  therefore its own `abg_net_index`) are published SIMULTANEOUSLY with
  its own decision - using them to "forecast" that same decision would
  not be a real forecast, and would be a fundamentally different (leaky)
  use of the index than everywhere else in this project
  (`pipeline/validate.py` is explicitly contemporaneous-not-predictive).
  Lagging both features uniformly, the same way skew already is, is the
  reading applied here. If a literal (unlagged) reading was actually
  intended, this is where to look to change it -
  `pipeline/ladder.py:l3_market_index_skew_logit`.
- **scipy added for L2/L3's ordered logit** - see the separate 2026-08-01
  "scipy added" entry above for the full reasoning and the two-part
  convergence check.
- **Feature standardisation (z-score, fit on training data only) was
  necessary, not optional - found by running the ladder, not assumed.**
  The first real run flagged 61 of 62 L3 windows as "degenerate"
  (`|param| > 50`), which turned out to be a scale artefact, not genuine
  non-convergence: `skew`'s raw values are ~1e-3, `implied_change_bp`'s
  are ~1e1, so a perfectly healthy fit needs wildly different-magnitude
  coefficients across features, easily tripping a threshold calibrated
  for unit-scale inputs. Standardising each feature column (subtract
  training mean, divide by training std - never touching the target
  during the standardisation itself, only applying the same
  transformation to it afterwards) fixed this: fallbacks dropped from 61
  of 62 to 11 of 62, and the remaining 11 are all evaluation meetings
  BEFORE March 2020 - the corpus's first-ever cut. Before that date, any
  training window has literally zero cut examples, which is exactly the
  "rare cuts early on" non-convergence the task itself anticipated -
  confirmed as a real, expected fallback, not a bug, by checking that
  every remaining fallback date precedes the first cut.
- **L4 member-level model, several judgment calls, all logged**
  (`pipeline/ladder.py` module docstring has the full reasoning):
  - Pooled transition matrix (not per-member - same reasoning as
    `pipeline/member_behaviour.py`), refit at each evaluation step on
    strictly prior votes only.
  - Each member's "previous state" = their own most recent state before
    the target meeting (from the expanding-window-filtered voting
    history), not their state AT the target meeting (that would be the
    answer being predicted).
  - "Plus implied_change_bp" implemented as an equal-weight (0.5/0.5)
    blend of the transition-matrix distribution and the same two-state
    +-25bp market-implied distribution already used for `m0`, reused at
    the per-member level (`hawkish_dissent<->hike`,
    `with_majority<->hold`, `dovish_dissent<->cut`). No new fitted
    parameter introduced beyond what's listed.
  - "Members with no history default to majority": implemented literally
    as a deterministic 100% with_majority/hold distribution for a
    member's first-ever appearance, with no market blending (nothing to
    blend against) - tested explicitly.
  - Committee-level distribution: Monte Carlo simulation (5,000 trials,
    fixed seed = 42) of all voting members' independent draws, aggregated
    by plurality with ties split equally among tied leaders - the task's
    own wording ("simulate the nine votes") points at simulation rather
    than an exact combinatorial calculation, and a fixed seed makes it
    exactly reproducible (tested).
- **Result: L0/L1 as expected (L1 far ahead of always-hold); L2, L3, L4
  all score WORSE than L1 (market-only) on this first pass** - negative
  skill for all three (L2 -0.30, L3 -0.59, L4 -0.95). Not treated as a
  bug or "fixed" further: this is a legitimate finding for a genuinely
  first backtest, and consistent with the project's own null-result
  framing (market efficiency). L1's mapping from implied_change_bp to
  probabilities is correct by construction (the same clipped-linear rule
  IS how m0 itself is built); L2 has to re-discover an equivalent
  relationship from a modest, noisy sample via MLE, so underperforming a
  correct-by-construction baseline on Brier score over 62 meetings is
  expected, not surprising. L4 carries by far the most compounded
  modelling assumptions (pooled transition matrix estimated on a limited
  sample, an invented 0.5/0.5 blend weight, Monte Carlo sampling
  variance) and its larger underperformance is consistent with that.
  Saved to `data/ladder_v1.json`; explicitly NOT published to the site,
  per instruction - for review first.

## 2026-07-11 — curve freshness fix

- **Root cause of the stale 2026-06-30 curve: `ois.py` only ever read
  `oisddata.zip`, the multi-year ARCHIVE - which the Bank's own FAQ says
  is only refreshed "by close of business of the second working day of
  each month".** There is a SEPARATE file, "latest-yield-curve-data.zip"
  ("Latest yield curve data" on the yield curves page), updated daily,
  containing "OIS daily data current month.xlsx" with the current
  month's business days. `latest_forward_curve()` now downloads BOTH and
  picks the single freshest date across all candidate files - the same
  "pick by actual date, not by assumed filename" principle already used
  to choose among era files, just extended to a second source.
- **The latest-month zip bundles 4 different curve types that share a
  sheet NAME but not a row structure** (GLC Nominal/Real/Inflation gilt
  curves + OIS) - found by actually running it, not assumed: the GLC
  files have blank/formula-error cells for some dates in this snapshot,
  which isn't a malformed OIS file, it's simply not an OIS file. Filtered
  to filenames containing "OIS" for this specific zip (the era archive
  doesn't have this problem, its files are unambiguously OIS-only, so no
  filter was needed there).
- **`pick_freshest_curve(xlsx_files)` extracted as a pure function**
  (given a file list, no I/O beyond reading them) so the actual bug -
  "does the freshest file win regardless of which one happens to be
  checked first" - is directly unit-tested with two small fixture
  workbooks, one deliberately stale, one fresh.
- **`lock.py` freshness assertion**: `assert_curve_is_fresh(curve_as_of,
  today)` refuses (raises) if the curve is more than
  `MAX_CURVE_STALENESS_BUSINESS_DAYS = 2` business days old. Checked
  right before the file WRITE in `main()`, not inside
  `build_prediction()` - `build_prediction()` stays usable in tests with
  an arbitrary injected curve date without also needing to fake "today".
  Business-day counting (Mon-Fri) has no UK bank-holiday calendar, same
  limitation as `ois_history.py`'s walk-back logic elsewhere in this
  codebase - a holiday inside the window is silently counted as a
  business day, which makes this an UNDERcount of true staleness, never
  an overcount, so the check stays conservative in the safe direction.
  Fixture-tested for both the pass and hard-stop paths, using the actual
  stale/fresh dates from this real incident.

## 2026-07-11 — scheduled vs special meetings split; probability-clip logged

- **`scheduled` (bool) added to `data/market_history.csv` and every ladder
  record**: False for `special_minutes` (the two March 2020 emergency
  meetings), True otherwise. At lock time - 2 business days before the
  announcement - nobody could have pre-registered a forecast for a
  meeting whose existence hadn't been announced yet, so treating specials
  as ordinary pre-registered forecasts would overstate how "surprising"
  the market's miss on them really was (they weren't scheduled to be
  forecastable at all).
- **Headline ladder evaluation = scheduled meetings only (60 of 62);
  specials are a separate, clearly-labelled robustness line, never
  blended into the headline scores.** `pipeline/build_ladder.py` now
  reports `headline_scores_scheduled_only` and
  `specials_robustness_scores` as two distinct tables in
  `data/ladder_v1.json`, both computed by the same `score_models()`
  function on filtered subsets - one scoring function, not two.
- **`log_score_probability_clip` (the `LOG_SCORE_EPSILON = 1e-9` floor
  applied to p(actual outcome) before `-log(p)`, to avoid `-log(0)` for a
  confidently-wrong call) is now a top-level field in
  `data/ladder_v1.json`**, not just a constant buried in
  `pipeline/predict/score_outcomes.py` - a reader of the ladder output
  can now see exactly what floor the log scores were computed under
  without reading the source.

## 2026-07-11 — live site investigation: false alarm, contract test added anyway

- **Investigated thoroughly before concluding anything, per instruction not
  to assume.** Compared: (1) the live deployed `index.html` byte-for-byte
  against the local committed file (curl diff - identical); (2) the live
  `data/index.json` schema against what index.html's JS reads (every
  field present: doc_id, meeting_end, published, decision, vote,
  abg_net_index, abg_hawk, abg_dove, sha256, source_url, neutral_value,
  lexicon); (3) rendered the exact deployed HTML+JSON with a real
  JS-executing browser (this repo's own preview tooling, pointed at the
  identical content) - the call card, latest-document card, and chart all
  render correctly, zero console errors, zero failed network requests.
- **Root cause of the apparent "stuck on Loading..." symptom: WebFetch
  (used for the initial live-page check) doesn't execute JavaScript.**
  It was reading the STATIC placeholder text ("Loading data/index.json
  …", "Loading call card …") that exists in the raw HTML before any
  script runs, which is indistinguishable from a genuinely broken page to
  a non-JS-executing crawler. A false alarm, not a real bug - the
  underlying site is fine right now.
- **Contract test added anyway** (`pipeline/tests/test_site_contract.py`),
  since the RISK this test guards against is real even though no bug
  currently exists: this project already broke this exact contract once
  before, silently, during the starter_v0 -> abg_2012 schema cutover
  (2026-07-18 entries) - the "latest scored document" card was reading
  fields (`net_hawkishness`, `hawkish_hits`, `dovish_hits`) that had been
  removed from `index.json`, caught only by manual review, not a test.
  Asserts every field index.html's JS actually reads exists in the
  REAL committed `data/index.json` and `data/predictions/dryrun-2026-07.json`
  - not a synthetic fixture, so it catches drift in the actual published
  data, not just the parsing logic.

## 2026-07-11 — data/surprises.csv

- **`surprise_bp = actual_change_bp - implied_change_bp`**, scheduled
  meetings only (91 of 94 - excludes the 2 specials and the very first
  corpus meeting, which has no preceding decision to diff against).
  `implied_change_bp` reuses `data/market_history.csv`'s value, i.e. the
  same LOCK_OFFSET_DAYS=3 convention (see DECISIONS.md, 2026-08-01) - one
  implied-change number used everywhere, not recomputed differently here.
- **The actual rate-change HISTORY doesn't skip special meetings, only
  the output rows do.** If a scheduled meeting immediately follows a
  special one (as with 25 March 2020, immediately after the 19 March
  special cut), its `actual_change_bp` is correctly computed against the
  special meeting's decided rate, not silently against whatever scheduled
  meeting came before that - the rate itself doesn't know or care whether
  the previous decision was "schedulable"; only which forecasts could
  have been pre-registered is scheduling-dependent. Tested explicitly
  (a scheduled meeting's prev-rate reference correctly points at an
  intervening special meeting's rate).

## 2026-07-11 — the headline inference (Spec 3 OLS + Spec 2 ordered-logit LR test)

- **statsmodels added as a new dependency, specifically and only for
  Newey-West HAC standard errors.** Not something worth hand-deriving
  (unlike the plain Pearson/Spearman kept dependency-free earlier) - HAC
  covariance estimation has enough subtlety (lag-length choice, small-
  sample corrections) that a well-tested library implementation is the
  right call here, same reasoning as adding scipy for the ordered logit.
- **`NEWEY_WEST_MAXLAGS = 4`**: roughly half a year of overlap at the
  MPC's current ~8-meetings/year cadence. A documented choice, not the
  only reasonable one - kept the same for both the full sample (n=91) and
  the smaller fragility subsample (n=23), rather than re-tuning per
  sample, so the two results are at least comparable on that axis.
- **Lagged features (`lagged_index`, `lagged_skew`) use the PREVIOUS
  meeting's value**, identical convention and identical reasoning to the
  benchmark ladder's L3 (2026-08-01 entry) - a meeting's own minutes
  publish simultaneously with its own decision, so using them unlagged
  wouldn't reflect information available before that meeting's outcome
  was known.
- **Spec 2's ordered-logit LR test needed its own minimum-sample guard**
  (`MIN_OBSERVATIONS_FOR_LR_TEST = 10`, same threshold and same reasoning
  as `pipeline/ladder.py`'s `MIN_TRAINING_EXAMPLES`) - found while writing
  the fragility-check test: without it, a 1-observation fit could report
  a spurious `converged=True` (trivially "successful" only because
  there's too little data to fail on), which would have made the
  Sep-2023-present subsample's report misleadingly confident rather than
  correctly flagged as too-small-to-fit.
- **Results, full sample (n=91 scheduled meetings, Aug 2015-present):**
  Spec 3 (surprise_bp ~ lagged_index): coefficient -2.16, t=-2.15,
  **p=0.032** - nominally significant at 5%. Sign is negative: a more
  hawkish lagged index is associated with a MORE NEGATIVE surprise (the
  actual decision came in more dovish than the market had priced),
  reported as observed, not interpreted further here. Adding lagged skew
  barely moves the index coefficient (still p=0.037) and skew itself is
  not significant (p=0.469). Spec 2 (ordered logit of the 3-class
  decision, with vs without the lagged index): LR=0.47, **p=0.49** - NOT
  significant. The two specs disagree (OLS on the continuous surprise
  finds something; the ordered logit on the discrete decision does not) -
  both reported, neither suppressed to make a cleaner story.
- **Fragility check (Sep 2023-present, n=23, post-hiking-cycle): the
  full-sample Spec 3 result does NOT replicate.** Coefficient -3.44,
  t=-1.47, p=0.142 - not significant at any conventional threshold. Spec
  2's ordered logit didn't even converge at this sample size (correctly
  caught by the new guard above, not silently reported as a
  success). This is exactly the kind of check that should be run before
  treating the full-sample p=0.032 as a stable finding, and it doesn't
  survive - reported honestly, not hidden or explained away.
- **Saved to `data/inference_v1.json`, NOT referenced anywhere in
  index.html or otherwise published** - confirmed by grep - per
  instruction, for review first.

## 2026-07-11 — Results section published to the site (ladder v1)

- **New "Results: benchmark ladder" card**, fetching `data/ladder_v1.json`
  and rendering the SCHEDULED-ONLY headline table (L0-L4: mean Brier,
  mean log score, skill vs L1, n) - the specials robustness line and the
  full per-meeting breakdown stay in the JSON file, not duplicated on the
  site (linked via `data/ladder_v1.json` in the caveat text instead).
- **Framing paragraph is a deliberately visible draft, not a finished
  one.** Wrapped in `<em>` with an explicit "[DRAFT - Jake to rewrite ...]"
  prefix, per instruction that this paragraph gets rewritten in his own
  words - the placeholder text describes what the table shows factually
  (mechanically, not persuasively) so it's usable as a starting point,
  but is unambiguously marked as not final.
- **Standing caveat text is permanent, not part of the draft**: "the
  market benchmark (L1) is the bar... matching or beating L0 is not the
  test" - stays regardless of how the framing paragraph above it gets
  rewritten, since it's a methodological statement about how to read the
  table, not commentary on the specific numbers.
- **Contract test extended** (`test_ladder_json_has_every_field_the_results_section_reads`)
  to cover the new card's fields, same pattern as the existing index.json/
  prediction-file contract tests - the Results section can't silently
  break from schema drift either.
- **Visually verified with a real JS-executing browser** (this repo's own
  preview tooling) before considering this done: table renders correctly,
  L1's row highlighted in accent colour, zero console errors, zero failed
  network requests.

## 2026-07-11 — lock rehearsal (dry run, fresh curve)

- **`python -m pipeline.predict.lock 2026-07-30 rehearsal-2026-07`** run
  end to end with the now-fixed fresh-curve pipeline. Curve as of
  2026-07-09 (1 business day old at run time) - the freshness assertion
  passed without needing to be bypassed, the first real end-to-end proof
  the freshness fix works outside of fixture tests.
  Result: `p_hold=0.9729`, `p_hike=0.0271`, `p_cut=0.0`
  (`implied_change_bp=0.68`) for the 30 July announcement.
- **Saved as `data/predictions/rehearsal-2026-07.json`** - not `lock-*`,
  no git tag - this is a rehearsal of the machinery, not a locked call.
  The site's `PREDICTION_FILE` constant still points at
  `dryrun-2026-07.json`, unchanged; the rehearsal file exists
  independently to prove the process works, not to replace what the live
  card displays.
- **Confirmed the call card renders it correctly in dry-run styling**
  without changing what the live site actually displays: fetched
  `rehearsal-2026-07.json` and ran it through the site's own unmodified
  `renderCallCard()` function in a real browser - `dry-run` classes and
  the "DRY RUN - NOT A FORECAST" badge applied correctly (same code path
  already used for `dryrun-2026-07.json`, since both files share the same
  `point_call: null` schema).

## 2026-07-12 — site v2 (design, interactivity, context panel, annotations, methodology)

Site-only session, hard constraint: nothing in `pipeline/score`,
`pipeline/market`, `pipeline/predict`, the lexicon, or any existing data
schema was modified; the original 83 tests stayed green throughout (now 93
with new site tests). New site work imports the science-layer modules
read-only and only ever writes NEW json files.

- **Design pass on `index.html`**: reordered to a clear hierarchy (call card
  -> the index -> market & macro context -> results -> episodes ->
  methodology), merged the old standalone "latest scored document" card into
  the index card as its lead reading, added a type scale, tabular numerals,
  mobile responsiveness, an inline-SVG favicon (data URI, no external file),
  page `<title>`/description/Open Graph/theme-color meta, and a real footer
  (GitHub links, "not investment advice", auto-populated generated date).
  All existing element IDs and data-loading JS preserved. Stale badge "Beta ·
  walking skeleton" corrected to "Beta · pre-registered".
- **Chart interactivity, hand-rolled (no chart library, no CDN)**: hover
  tooltip (document, published date, index value, and the decision that
  *followed* - i.e. the NEXT meeting's decision, the thesis-relevant one,
  since a meeting's own decision is already its marker); toggleable overlays
  for decision markers and a Bank Rate step line on its own right-hand axis;
  neutral reference line kept labelled. One decision classifier shared with
  the rest of the codebase (the verb adjacent to "Bank Rate", re-implemented
  in JS since it can't import `pipeline/decision_label.py`).
- **NEW exporter `pipeline/site_context.py` -> `data/site_context.json`**,
  labelled "Context - not model inputs" (a `context_not_model_inputs: true`
  flag in the JSON and a visible badge on the site). Three series:
  (a) the OIS-implied path for the next three scheduled meetings (30 Jul /
  17 Sep / 5 Nov 2026, from the Bank's published calendar - see the
  2026-08-01 entry - hardcoded as CONTEXT labels, not a model input),
  computed via the SAME `market_probs_for_meeting` rule used for m0 and the
  benchmark; (b) Bank Rate history as a step chart, from `data/votes.csv`'s
  `decided_rate`; (c) the 2-year nominal gilt yield (latest + a 12-month
  daily sparkline), read from the Bank's GLC Nominal curve files (the
  current-month file already downloaded by `ois.download_latest_month_zip`
  plus a NEW polite download of `glcnominalddata.zip`, same 2s-sleep
  discipline). The 24-month spot point was found in the "3. spot, short end"
  sheet; **it parsed cleanly, no HARD STOP triggered** - but the reader path
  raises rather than approximating if the sheet/column ever goes missing.
- **Annotations machinery, site layer only**: markdown episodes live in
  `site/annotations/YYYY-MM-slug.md` (two header lines `title:`/`date:` then
  a markdown body). A build step (`pipeline/build_annotations.py`) scans them
  into `data/annotations.json`, newest-first, which the "Episodes" section
  fetches and renders with a tiny safe markdown subset (paragraphs, headings,
  bold/italic, links, bullet lists) - **a build step, not client-side
  directory listing, because static GitHub Pages has no directory index**;
  same "everything the site reads is a data/*.json" pattern as the rest of
  the project. Exactly one placeholder file, `2021-11-the-hold-that-wasnt.md`,
  marked `TODO(Jake)` - all real episode text is written by Jake, never
  generated here. A missing `title:`/`date:` header HARD STOPs.
- **`methodology.html`** added: self-contained companion page (own trimmed
  copy of the site styles, no shared external stylesheet, to keep both pages
  zero-dependency), with five section stubs marked `TODO(Jake)` - Data, Index
  construction, Market benchmark, Evaluation, Limitations - wired into the
  index footer nav. A one-line footnote under the OIS probability bars
  ("forward-implied probabilities reflect risk premia as well as
  expectations") links to `methodology.html#limitations`.
- **`CLAUDE.md` added at the repo root** with the standing rules (read
  DECISIONS.md first; every choice gets a dated forward-only entry; never
  modify `data/predictions/lock-*`; the science layer is off-limits unless a
  prompt says otherwise; one plain-English line before each command for a
  beginner maintainer; never fabricate/approximate - HARD STOP and ask).
- **New site tests (site layer only), 10 added, 93 total**: contract tests
  that `data/site_context.json` and `data/annotations.json` carry every field
  the front-end reads (same guard as `test_site_contract.py`), plus pure-
  helper unit tests (bank-rate dedup, era-file year parsing, gilt 12-month
  windowing, OIS-path shape, annotation header parsing incl. the HARD-STOP
  path) - none make live calls.

## 2026-07-12 — evidence inspector (`pipeline/inspect.py`)
- New tooling module for drafting/inspection only, never read by the site.
  Imports `pipeline/score/abg.py`'s tokeniser (`_TOKEN`), lexicon loader
  (`load_abg_lexicon`) and noun-matcher (`_noun_matches_at`) verbatim rather
  than reimplementing the matching logic, so its per-term breakdown can never
  silently drift from the scorer's own aggregate counts. A test
  (`pipeline/tests/test_inspect.py`) asserts this reconciliation on both a
  synthetic string (portable, no dependency on local raw text) and, when raw
  text is present locally, the real corpus against `data/index.json`'s
  `abg_hawk`/`abg_dove` fields - the task brief referred to these as
  `hawkish_hits`/`dovish_hits`, which was the retired `starter_v0`/
  `dictionary.py` field naming; checked the actual current schema rather than
  writing a test against field names that no longer exist.
- **"Trailing N documents" for this module means strictly the N documents
  published *before* the target**, not including it. This is a deliberate
  choice distinct from `pipeline/predict/lock.py`'s own `index_trailing_mean`
  convention (last N documents including the current one, used on the site's
  call card) - lock.py is off-limits this session (`pipeline/predict`) and is
  unchanged. For `inspect.py`'s purpose (does this document look unusual
  against its own recent history?) including the document in its own
  baseline would dilute the comparison, so a strictly-prior window was used
  instead, for both the trailing-mean display and the `--vs-trailing`
  frequency comparison.
- `--vs-trailing` is descriptive only (raw counts and deltas vs a simple
  average) - no significance testing, per instruction.

## 2026-07-12 — Track record section (`data/track_record.json`, `index.html`)
- New `pipeline/build_track_record.py` (site layer, additive) reads
  `data/predictions/*.json` (never writes to them) and writes a flat summary
  to `data/track_record.json`, which a new "Track record" section on the
  site fetches - same build-step pattern as `pipeline/build_annotations.py`,
  needed because static GitHub Pages has no directory index to discover the
  prediction files on its own.
- **"Locked" is determined purely by filename prefix (`lock-`)**, matching
  the existing project convention in `CLAUDE.md` ("Files under
  `data/predictions/lock-*` are never modified once written"). Any other
  filename (`dryrun-*`, `rehearsal-*`, anything else) renders as a
  non-locked draft with a distinct badge. This means any future `lock-*.json`
  file picks up the locked styling automatically, with no code change
  needed.
- **Brier column shows `scores.m0_market_only.brier_score`, not a
  point-call-specific score.** Checked `pipeline/predict/score_outcomes.py`:
  it only scores the m0 market-only reference and an always-hold baseline -
  `point_call` is a categorical single guess with no probability
  distribution of its own, so there is currently no Brier defined for it.
  Rather than fabricate one (e.g. treating the point call as a degenerate
  100%-confidence forecast), the site labels the column "Brier (m0)" and the
  section's framing text says why. Revisit if/when Jake decides how a point
  call should be converted into a scoreable distribution - that's a
  methodological choice for `pipeline/predict`, out of scope this session.
- Empty-state note ("First pre-registered call: 30 July 2026.") shows
  whenever no record has `kind == "locked"` yet - both current files
  (`dryrun-2026-07.json`, `rehearsal-2026-07.json`) are drafts, so it
  currently always shows alongside the two draft rows, not instead of them.
- New tests: `pipeline/tests/test_build_track_record.py` (unit tests on
  synthetic prediction files + a contract test on the real
  `data/track_record.json`, same pattern as `test_build_annotations.py`).
  Verified rendering locally in a real browser (`preview_*` tools): both
  draft rows render with correct badges/values, empty-state note shows, no
  console errors.

## 2026-07-13 — final polish: Spec 3 published, lexicon sparsity, repo front door

- **The headline inference (Spec 3 + Spec 2) is now published to the site's
  Results section**, ending the "NOT published - for review first" status
  from the headline-inference entry (2026-07-11, formerly misdated
  2026-08-08 - see the erratum below). Values are rendered verbatim from
  `data/inference_v1.json` by index.html's JS (no re-rounding, no
  re-derivation); the fragility non-replication and Spec 2's null are shown
  in the same sentence as the full-sample p-value, never separated from it.
  A one-line plain-English caption sits under both the ladder table and the
  Spec 3 line, each marked DRAFT for JF to revise.
- **Lexicon-sparsity statistic computed read-only and quoted on
  methodology.html#limitations**: per document, total_hits = abg_hawk +
  abg_dove from `data/index.json`; across all 94 documents the median is 2
  hits, Q1 = 1, Q3 = 3 (IQR = 2), min 0, max 12. Computed by the additive
  script `pipeline/lexicon_sparsity.py` (reads index.json, writes nothing,
  imports nothing from the science layer). Quartiles use
  `statistics.quantiles(n=4, method="inclusive")` - the median-inclusive
  convention - stated on the page rather than left implicit.
- **methodology.html's five stubs replaced with a factual specification
  sheet** (Data / Index construction / Market benchmark / Evaluation /
  Limitations), every claim traceable inline to code or a dated entry in
  this file; every section carries a DRAFT marker - the interpretive
  discussion is Jake's to write, not generated.
- **Repo front door for an academic reader**: README rewritten (research
  question, pipeline diagram, headline ladder + Spec 3 numbers copied
  verbatim from the JSON files, quickstart, repo map, limitations pointer);
  CITATION.cff added; a GitHub Actions workflow runs pytest on every push -
  tests only, it never rebuilds data and never touches
  `data/predictions/`; repo description/topics set via gh. A dated table
  of contents was added to the top of this file and the two 2026-07-12
  headers' dash style normalised - no entry wording, dates or meaning
  changed.
- **Date oddity in earlier headers**: noticed during this session that
  entries dated 2026-08-01/2026-08-08 sat before entries dated 2026-07-12
  in file order. Investigated against commit evidence the same day and
  corrected - see the erratum entry below for the full table and the root
  cause.

## 2026-07-13 — ERRATUM: entry header dates corrected against commit evidence

Header dates in this file had been written from an assumed weekly session
cadence instead of the system clock: `git log --follow -p` shows every
misdated entry was actually committed on 11-12 July 2026, while the headers
claimed dates up to four weeks later. Each header below was corrected in
place to the date of the commit that introduced it; **no entry wording was
changed**. Body-text cross-references to the old dates (in earlier entries,
committed docstrings, and data/*.json notes) resolve via this table. The
2026-07-05 "repo created" header predates the first commit (b66db84,
2026-07-10) and cannot be verified from git; it is not future-dated and no
evidence contradicts it, so it is left unchanged. Root cause: dates were
recalled from memory/assumed schedule and never checked with `date` — a
rule now added to CLAUDE.md, with a pytest guard
(`pipeline/tests/test_decisions_dates.py`) that fails on any future-dated
entry.

| Entry | Wrong date | Corrected date | Evidencing commit |
|---|---|---|---|
| corpus audit: full-text repair + special meetings | 2026-07-18 | 2026-07-11 | 69f4593 |
| A&BG (2012) baseline lexicon | 2026-07-18 | 2026-07-11 | 8d56446 |
| voting-record parsing and reconciliation | 2026-07-18 | 2026-07-11 | 8d56446 |
| first validation pass (v1) | 2026-07-18 | 2026-07-11 | 8d56446 |
| site: A&BG chart, retiring starter_v0 fields from the UI | 2026-07-18 | 2026-07-11 | 8d56446 |
| 19 March 2020 special meeting added | 2026-07-25 | 2026-07-11 | 32659bd |
| validation join fixed: voting-sheet date is canonical | 2026-07-25 | 2026-07-11 | 32659bd |
| neutral_value published in index.json | 2026-07-25 | 2026-07-11 | 32659bd |
| member-behaviour table (seeds Stage 4) | 2026-07-25 | 2026-07-11 | 32659bd |
| market benchmark: OIS forward curve + SONIA | 2026-07-25 | 2026-07-11 | 523e44d |
| market_probs: two-state ±25bp assumption | 2026-07-25 | 2026-07-11 | 523e44d |
| lock and scoring machinery | 2026-07-25 | 2026-07-11 | 523e44d |
| site call card + dry run | 2026-07-25 | 2026-07-11 | 523e44d |
| smoothed-curve bias: quantified, offset convention chosen | 2026-08-01 | 2026-07-11 | 329a5a9 |
| 2 null-decision documents recovered | 2026-08-01 | 2026-07-11 | 329a5a9 |
| historical market benchmark: data/market_history.csv | 2026-08-01 | 2026-07-11 | 329a5a9 |
| decision classifier bug found and fixed | 2026-08-01 | 2026-07-11 | 329a5a9 |
| Part B sanity checks | 2026-08-01 | 2026-07-11 | 329a5a9 |
| scipy added, for the ordered logit models only | 2026-08-01 | 2026-07-11 | 329a5a9 |
| the benchmark ladder (first real backtest), L0-L4 | 2026-08-01 | 2026-07-11 | 329a5a9 |
| curve freshness fix | 2026-08-08 | 2026-07-11 | 95a9af7 |
| scheduled vs special meetings split; probability-clip logged | 2026-08-08 | 2026-07-11 | 95a9af7 |
| live site investigation: false alarm, contract test added anyway | 2026-08-08 | 2026-07-11 | 95a9af7 |
| data/surprises.csv | 2026-08-08 | 2026-07-11 | 95a9af7 |
| the headline inference (Spec 3 OLS + Spec 2 ordered-logit LR test) | 2026-08-08 | 2026-07-11 | 95a9af7 |
| Results section published to the site (ladder v1) | 2026-08-08 | 2026-07-11 | 95a9af7 |
| lock rehearsal (dry run, fresh curve) | 2026-08-08 | 2026-07-11 | 95a9af7 |
| site v2 (design, interactivity, context panel, annotations, methodology) | 2026-08-08 | 2026-07-12 | c2356a2 |
| final polish: Spec 3 published, lexicon sparsity, repo front door | 2026-07-12 | 2026-07-13 | uncommitted (this session; `date` = 2026-07-13) |
