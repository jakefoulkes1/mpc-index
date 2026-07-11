import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_market_history_covers_every_published_corpus_meeting():
    corpus = json.loads((ROOT / "data" / "index.json").read_text())
    corpus_ids = {d["doc_id"] for d in corpus["documents"] if d["published"]}

    with open(ROOT / "data" / "market_history.csv") as fh:
        history_ids = {row["meeting"] for row in csv.DictReader(fh)}

    missing = corpus_ids - history_ids
    assert missing == set(), f"corpus meetings missing from market_history.csv: {sorted(missing)}"
