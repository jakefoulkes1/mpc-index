"""Builds data/market_history.csv: m0 market-implied {cut, hold, hike}
probabilities for every meeting in the text corpus (Aug 2015-present),
from the historical OIS forward curve + SONIA, using the same convention
as the live dry-run card (pipeline/predict/market_probs.py, LOCK_OFFSET_DAYS
= 3 days after the meeting - see DECISIONS.md, 2026-07-11).

Lock date (the curve snapshot used, as if this were locked ahead of the
announcement): announcement - LOCK_DATE_OFFSET_DAYS (2) calendar days; if
that isn't a trading day (weekend/holiday - simply absent from the data),
walks back to the nearest one that is, logged.

`scheduled` (bool): False for special_minutes (emergency meetings, e.g.
the March 2020 Covid cuts) - at "lock time" nobody could have registered
a forecast for a meeting whose existence wasn't yet announced, so these
can't be treated as ordinary pre-registered forecasts. True for every
regular minutes document. See DECISIONS.md, 2026-07-11.

Run:  python -m pipeline.build_market_history
"""
import csv
import datetime as dt
import json
from pathlib import Path

from pipeline.market.ois_history import (
    find_nearest_available_date,
    load_full_curve_history,
    load_full_sonia_history,
)
from pipeline.predict.market_probs import forward_rate_for_date, implied_probs

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "data" / "index.json"
OUT = ROOT / "data" / "market_history.csv"
LOCK_DATE_OFFSET_DAYS = 2
FIELDNAMES = ["meeting", "scheduled", "lock_date", "sonia", "forward", "implied_change_bp",
              "p_cut", "p_hold", "p_hike", "source_file"]


def build_rows(meetings: list[dict], curve_history: dict[dt.date, dict], sonia_history: dict[dt.date, float]) -> list[dict]:
    """Pure function (no I/O) so it can be unit-tested against synthetic
    curve/SONIA history - see pipeline/tests/test_build_market_history.py."""
    curve_dates = set(curve_history)
    sonia_dates = set(sonia_history)
    rows = []
    for doc in meetings:
        announcement = dt.date.fromisoformat(doc["published"])
        lock_date, walked = find_nearest_available_date(curve_dates, announcement - dt.timedelta(days=LOCK_DATE_OFFSET_DAYS))
        if walked:
            print(f"log: {doc['doc_id']}: lock_date walked back {walked} day(s) from "
                  f"announcement-{LOCK_DATE_OFFSET_DAYS}d (weekend/holiday) to {lock_date}")

        curve = curve_history[lock_date]
        sonia_date, sonia_walked = find_nearest_available_date(sonia_dates, lock_date)
        if sonia_walked:
            print(f"log: {doc['doc_id']}: SONIA walked back {sonia_walked} day(s) from lock_date to {sonia_date}")
        sonia_pct = sonia_history[sonia_date]

        rate = forward_rate_for_date(curve["maturities_months"], curve["forward_rates_pct"], lock_date, announcement)
        probs = implied_probs(rate, sonia_pct)

        rows.append({
            "meeting": doc["doc_id"],
            "scheduled": doc.get("type", "minutes") == "minutes",
            "lock_date": lock_date.isoformat(),
            "sonia": sonia_pct,
            "forward": round(rate, 4),
            "implied_change_bp": probs["implied_change_bp"],
            "p_cut": probs["p_cut"],
            "p_hold": probs["p_hold"],
            "p_hike": probs["p_hike"],
            "source_file": curve["source_file"],
        })
    return rows


def main() -> None:
    corpus = json.loads(INDEX_PATH.read_text())
    meetings = sorted(
        (d for d in corpus["documents"] if d["published"]),
        key=lambda d: d["published"],
    )
    if not meetings:
        raise ValueError("HARD STOP: no published meetings found in data/index.json")

    curve_history = load_full_curve_history()
    earliest = dt.date.fromisoformat(meetings[0]["published"])
    sonia_history = load_full_sonia_history(earliest - dt.timedelta(days=30))

    rows = build_rows(meetings, curve_history, sonia_history)

    with open(OUT, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {OUT} ({len(rows)} meetings)")


if __name__ == "__main__":
    main()
