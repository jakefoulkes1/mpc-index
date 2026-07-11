"""Builds data/surprises.csv: for every SCHEDULED meeting,
surprise_bp = actual_change_bp - implied_change_bp (at lock, using the
same LOCK_OFFSET_DAYS=3 convention as everywhere else - see DECISIONS.md,
2026-08-01).

actual_change_bp is the real Bank Rate change from the immediately
PRECEDING decision (whatever type that was - special or scheduled; the
rate itself doesn't care) to this meeting's decided rate. Special
meetings are excluded from the OUTPUT rows (can't have been pre-registered
forecasts - see DECISIONS.md, 2026-08-08) but still count as the
"previous decision" when a scheduled meeting immediately follows one, since
that's the actual rate history.

Run:  python -m pipeline.build_surprises
"""
import csv
from pathlib import Path

from pipeline.ladder import load_records

ROOT = Path(__file__).resolve().parents[1]
VOTES_PATH = ROOT / "data" / "votes.csv"
OUT = ROOT / "data" / "surprises.csv"
FIELDNAMES = ["meeting", "date", "decided_rate", "prev_decided_rate",
              "actual_change_bp", "implied_change_bp", "surprise_bp"]


def load_decided_rates() -> dict[str, float]:
    rates = {}
    with open(VOTES_PATH) as fh:
        for row in csv.DictReader(fh):
            rates[row["meeting_date"]] = float(row["decided_rate"])
    return rates


def build_rows(records: list[dict], decided_rates: dict[str, float]) -> list[dict]:
    """records must be in chronological order (as load_records() returns)."""
    rows = []
    prev_rate = None
    for r in records:
        rate = decided_rates.get(r["votes_date"]) if r["votes_date"] else None
        if rate is not None and prev_rate is not None and r["scheduled"]:
            actual_change_bp = round((rate - prev_rate) * 10000, 2)
            surprise_bp = round(actual_change_bp - r["implied_change_bp"], 2)
            rows.append({
                "meeting": r["doc_id"],
                "date": r["date"],
                "decided_rate": rate,
                "prev_decided_rate": prev_rate,
                "actual_change_bp": actual_change_bp,
                "implied_change_bp": r["implied_change_bp"],
                "surprise_bp": surprise_bp,
            })
        if rate is not None:
            prev_rate = rate
    return rows


def main() -> None:
    records = load_records()
    decided_rates = load_decided_rates()
    rows = build_rows(records, decided_rates)
    if not rows:
        raise ValueError("HARD STOP: no surprise rows built - check votes.csv/records alignment")

    with open(OUT, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {OUT} ({len(rows)} scheduled meetings)")


if __name__ == "__main__":
    main()
