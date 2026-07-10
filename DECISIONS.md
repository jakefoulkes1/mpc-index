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
