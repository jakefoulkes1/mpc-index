from pathlib import Path

from pipeline.build_index import parse_entry

FIX = Path(__file__).parent / "fixtures"


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
