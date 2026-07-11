from pathlib import Path

from pipeline.build_index import parse_entry
from pipeline.score.abg import score_document as score_document_abg

FIX = Path(__file__).parent / "fixtures"

# Fields index.html's renderChart() reads off each document with a
# `published` date - see index.html's renderChart function.
CHART_REQUIRED_FIELDS = {"doc_id", "published", "decision", "abg_net_index"}


def test_parses_june_2026_manifest_fields(tmp_path):
    text = (FIX / "june_2026_summary_excerpt.txt").read_text()
    raw = tmp_path / "2026-06-minutes.txt"
    raw.write_text(text)

    entry = parse_entry(raw, source_kind={})

    assert entry["doc_id"] == "minutes-2026-06"
    assert entry["meeting_end"] == "2026-06-17"
    assert entry["published"] == "2026-06-18"
    assert entry["decision"] == "maintain Bank Rate at 3.75%"
    assert entry["vote"] == "7-2"
    assert entry["source_url"] == (
        "https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes/2026/june-2026"
    )
    assert entry["source_kind"] == "html"
    assert entry["word_count"] == len(text.split())


def test_source_kind_from_sidecar(tmp_path):
    raw = tmp_path / "2019-12-minutes.txt"
    raw.write_text("meeting ending on 18 December 2019, the MPC voted unanimously to maintain Bank Rate at 0.75%.")
    entry = parse_entry(raw, source_kind={"2019-12-minutes.txt": "pdf"})
    assert entry["source_kind"] == "pdf"


def test_unrecognised_filename_returns_none(tmp_path):
    raw = tmp_path / "notes.txt"
    raw.write_text("irrelevant")
    assert parse_entry(raw, source_kind={}) is None


def test_proposition_fallback_recovers_package_of_measures_decision(tmp_path):
    text = (
        "At its meeting ending on 3 August 2016 the Committee discussed a package of measures. "
        "The Governor invited the Committee to vote on the propositions that: "
        "Bank Rate be reduced by 25 basis points to 0.25%; "
        "The Bank of England introduce a Term Funding Scheme. "
        "The Committee voted unanimously in favour of the propositions on Bank Rate and the Term Funding Scheme."
    )
    raw = tmp_path / "2016-08-minutes.txt"
    raw.write_text(text)

    entry = parse_entry(raw, source_kind={})

    assert entry["decision"] == "reduce Bank Rate by 25 basis points to 0.25%"
    assert entry["vote"] == "unanimous"
    assert "propositions that" in entry["raw_vote_text"]


def test_proposition_fallback_requires_both_halves(tmp_path):
    # Proposition stated but never confirmed adopted - must stay null, not guess.
    text = (
        "meeting ending on 3 August 2016 "
        "The Governor invited the Committee to vote on the propositions that: "
        "Bank Rate be reduced by 25 basis points to 0.25%."
    )
    raw = tmp_path / "2016-08-minutes.txt"
    raw.write_text(text)

    entry = parse_entry(raw, source_kind={})

    assert entry["decision"] is None
    assert entry["vote"] is None


def test_document_record_has_chart_required_fields(tmp_path):
    text = (FIX / "june_2026_summary_excerpt.txt").read_text()
    raw = tmp_path / "2026-06-minutes.txt"
    raw.write_text(text)

    entry = parse_entry(raw, source_kind={})
    entry.update(score_document_abg(text))

    assert CHART_REQUIRED_FIELDS <= entry.keys()
    assert entry["published"] is not None
    assert isinstance(entry["abg_net_index"], float)
