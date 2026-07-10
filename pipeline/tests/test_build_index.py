from pathlib import Path

from pipeline.build_index import parse_entry

FIX = Path(__file__).parent / "fixtures"


def test_parses_june_2026_manifest_fields(tmp_path):
    text = (FIX / "june_2026_summary_excerpt.txt").read_text()
    raw = tmp_path / "2026-06-minutes.txt"
    raw.write_text(text)

    entry = parse_entry(raw)

    assert entry["doc_id"] == "minutes-2026-06"
    assert entry["meeting_end"] == "2026-06-17"
    assert entry["published"] == "2026-06-18"
    assert entry["decision"] == "maintain Bank Rate at 3.75%"
    assert entry["vote"] == "7-2"
    assert entry["source_url"] == (
        "https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes/2026/june-2026"
    )


def test_unrecognised_filename_returns_none(tmp_path):
    raw = tmp_path / "notes.txt"
    raw.write_text("irrelevant")
    assert parse_entry(raw) is None
