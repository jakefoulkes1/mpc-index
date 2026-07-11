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

## 2026-07-18 — A&BG (2012) baseline lexicon

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

## 2026-07-18 — voting-record parsing and reconciliation

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

## 2026-07-18 — first validation pass (v1)

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

## 2026-07-18 — site: A&BG chart, retiring starter_v0 fields from the UI

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

## 2026-07-25 — 19 March 2020 special meeting added

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

## 2026-07-25 — validation join fixed: voting-sheet date is canonical

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

## 2026-07-25 — neutral_value published in index.json

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

## 2026-07-25 — member-behaviour table (seeds Stage 4)

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

## 2026-07-25 — market benchmark: OIS forward curve + SONIA

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

## 2026-07-25 — market_probs: two-state ±25bp assumption

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

## 2026-07-25 — lock and scoring machinery

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

## 2026-07-25 — site call card + dry run

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
