"""Contract test: does data/index.json (and the dry-run prediction file)
actually contain every field index.html's JavaScript reads?

This is the safeguard the site didn't have when it silently drifted out of
sync with the abg_2012 schema cutover earlier in this project (see
DECISIONS.md) - a live-site investigation found the site was actually fine
(WebFetch's non-JS-executing crawler was giving a false "stuck on
Loading..." impression, not a real bug - confirmed by rendering the exact
deployed HTML+JSON with a real JS-executing browser), but the underlying
risk (index.html and build_index.py's schema silently diverging) is real
and worth guarding against going forward. See DECISIONS.md, 2026-08-08.

The required-field lists below are maintained by hand against index.html's
actual `doc.xxx` / `data.xxx` / `p.xxx` / `m0.xxx` reads - update both
together if either changes.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Every data.<field> and doc.<field> index.html's renderLatest()/renderChart() read.
REQUIRED_TOP_LEVEL_FIELDS = {"documents", "neutral_value", "lexicon"}
REQUIRED_DOCUMENT_FIELDS = {
    "doc_id", "meeting_end", "published", "decision", "vote",
    "abg_net_index", "abg_hawk", "abg_dove", "sha256", "source_url",
}

# Every p.<field> and m0.<field> index.html's renderCallCard() reads.
REQUIRED_PREDICTION_FIELDS = {
    "point_call", "meeting_announcement", "lock_timestamp", "rationale",
    "m0_market_only", "index_current", "index_current_doc_id",
    "index_trailing_mean", "index_trailing_n",
}
REQUIRED_M0_FIELDS = {"p_cut", "p_hold", "p_hike", "assumed_move_bp"}

# Every d.<field> index.html's renderLadder() reads.
REQUIRED_LADDER_FIELDS = {
    "schema", "eval_start", "n_scheduled", "n_specials",
    "log_score_probability_clip", "headline_scores_scheduled_only",
}
REQUIRED_LADDER_MODEL_FIELDS = {"mean_brier", "mean_log_score", "n"}
LADDER_MODELS = ("L0", "L1", "L2", "L3", "L4")


def test_index_json_has_every_field_the_site_reads():
    data = json.loads((ROOT / "data" / "index.json").read_text())
    missing_top = REQUIRED_TOP_LEVEL_FIELDS - data.keys()
    assert not missing_top, f"data/index.json is missing top-level field(s) the site reads: {missing_top}"

    assert data["documents"], "data/index.json has no documents to check"
    for doc in data["documents"]:
        missing = REQUIRED_DOCUMENT_FIELDS - doc.keys()
        assert not missing, f"{doc.get('doc_id', '?')} is missing field(s) the site reads: {missing}"


def test_dryrun_prediction_has_every_field_the_call_card_reads():
    path = ROOT / "data" / "predictions" / "dryrun-2026-07.json"
    if not path.exists():
        return  # nothing to check yet if it hasn't been generated in this checkout
    payload = json.loads(path.read_text())
    missing = REQUIRED_PREDICTION_FIELDS - payload.keys()
    assert not missing, f"{path.name} is missing field(s) the call card reads: {missing}"

    m0_missing = REQUIRED_M0_FIELDS - payload["m0_market_only"].keys()
    assert not m0_missing, f"{path.name}'s m0_market_only is missing field(s) the call card reads: {m0_missing}"


def test_ladder_json_has_every_field_the_results_section_reads():
    path = ROOT / "data" / "ladder_v1.json"
    if not path.exists():
        return  # nothing to check yet if it hasn't been generated in this checkout
    data = json.loads(path.read_text())
    missing = REQUIRED_LADDER_FIELDS - data.keys()
    assert not missing, f"{path.name} is missing field(s) the Results section reads: {missing}"

    scores = data["headline_scores_scheduled_only"]
    for model in LADDER_MODELS:
        assert model in scores, f"{path.name}'s headline_scores_scheduled_only is missing model {model}"
        missing_fields = REQUIRED_LADDER_MODEL_FIELDS - scores[model].keys()
        assert not missing_fields, f"{path.name}'s {model} entry is missing field(s): {missing_fields}"
