"""Build data/index.json from cached raw documents.

v0 walking skeleton: an explicit MANIFEST lists the documents. The week-1
scraper replaces this with discovery over the whole Aug 2015-present era.

Run:  python -m pipeline.build_index
"""
import datetime as dt
import hashlib
import json
from pathlib import Path

from pipeline.score.dictionary import load_lexicon, score_document

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "index.json"

MANIFEST = [
    {
        "doc_id": "minutes-2026-06",
        "type": "minutes",
        "meeting_end": "2026-06-17",
        "published": "2026-06-18",
        "decision": "hold at 3.75%",
        "vote": "7-2 (two for +25bp)",
        "source_url": "https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes/2026/june-2026",
        "file": "2026-06-minutes.txt",
    },
]


def main() -> None:
    lexicon = load_lexicon()
    documents, series = [], []
    for entry in MANIFEST:
        path = RAW / entry["file"]
        if not path.exists():
            print(f"skip (missing raw file): {path}")
            continue
        text = path.read_text()
        record = {k: v for k, v in entry.items() if k != "file"}
        record["sha256"] = hashlib.sha256(text.encode()).hexdigest()
        record.update(score_document(text, lexicon))
        documents.append(record)
        series.append({
            "date": entry["published"],
            "net_hawkishness": record["net_hawkishness"],
            "doc_id": entry["doc_id"],
        })

    payload = {
        "schema": "index-v0",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "lexicon": "starter_v0 (plumbing only - see DECISIONS.md; A&BG replaces it)",
        "documents": documents,
        "series": sorted(series, key=lambda row: row["date"]),
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {OUT} ({len(documents)} document(s))")


if __name__ == "__main__":
    main()
