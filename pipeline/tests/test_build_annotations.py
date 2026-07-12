"""Unit + contract tests for the site-only annotations build step
(pipeline/build_annotations.py -> data/annotations.json).

Same spirit as test_site_context.py: pure-parser unit tests plus a contract
test that the REAL committed data/annotations.json has every field the
Episodes section reads, so the section can't silently break from drift.
"""
import json
from pathlib import Path

import pytest

from pipeline.build_annotations import build, load_episodes, parse_annotation

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_TOP = {"schema", "episodes"}
REQUIRED_EPISODE = {"title", "date", "body"}


def test_parse_annotation_reads_headers_then_body():
    text = "title: The hold that wasn't\ndate: 2021-11-04\n\nBody line one.\n\nBody line two."
    out = parse_annotation(text, "2021-11-x.md")
    assert out["title"] == "The hold that wasn't"
    assert out["date"] == "2021-11-04"
    assert out["body"] == "Body line one.\n\nBody line two."


def test_parse_annotation_missing_header_hard_stops():
    with pytest.raises(ValueError, match="missing required header"):
        parse_annotation("title: no date here\n\nbody", "bad.md")


def test_load_episodes_sorts_newest_first(tmp_path):
    (tmp_path / "2020-01-older.md").write_text("title: Older\ndate: 2020-01-30\n\nx")
    (tmp_path / "2021-11-newer.md").write_text("title: Newer\ndate: 2021-11-04\n\ny")
    episodes = load_episodes(tmp_path)
    assert [e["date"] for e in episodes] == ["2021-11-04", "2020-01-30"]
    assert episodes[0]["slug"] == "2021-11-newer"


def test_build_shape_with_synthetic_dir(tmp_path):
    (tmp_path / "2021-11-x.md").write_text("title: X\ndate: 2021-11-04\n\nbody")
    data = build(annotations_dir=tmp_path, generated_utc="2026-01-01T00:00:00+00:00")
    assert not (REQUIRED_TOP - data.keys())
    assert data["episodes"] and not (REQUIRED_EPISODE - data["episodes"][0].keys())


def test_real_annotations_json_has_every_field_the_section_reads():
    path = ROOT / "data" / "annotations.json"
    if not path.exists():
        return  # not generated in this checkout yet
    data = json.loads(path.read_text())
    assert not (REQUIRED_TOP - data.keys()), f"annotations.json missing: {REQUIRED_TOP - data.keys()}"
    for ep in data["episodes"]:
        assert not (REQUIRED_EPISODE - ep.keys()), f"episode missing: {REQUIRED_EPISODE - ep.keys()}"
