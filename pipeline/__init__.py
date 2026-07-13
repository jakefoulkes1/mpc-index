"""MPC Communication Index pipeline.

Subpackages and layers:
  scrape/   fetch & cache Bank of England pages/PDFs (local, polite)
  parse/    HTML -> clean text
  score/    the A&BG (2012) tone index + lexicon   [science layer - frozen]
  market/   OIS forward curve + SONIA readers      [science layer - frozen]
  predict/  implied probabilities, lock, scoring   [science layer - frozen]
  tests/    the full suite; fixtures only, no live network calls

Top-level modules are orchestrators (build_*.py -> data/*.json|csv),
analyses (validate.py, ladder.py, inference.py, member_behaviour.py) and
tooling (inspect.py, decision_label.py, site_context.py).

The frozen science layer may be imported, never modified - see CLAUDE.md
and DECISIONS.md (every methodological choice has a dated entry there).
"""
