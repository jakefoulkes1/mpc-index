"""Writes a prediction snapshot to data/predictions/<name>.json.

This is machinery for a FUTURE locked call - running this script is not
itself "the lock". `point_call` and `rationale` are deliberately left for
the human (Jake) to fill in by hand before the actual lock; the lock is
the timestamped, committed file plus his own written rationale, not this
script's output on its own. m0_market_only is a market-only reference
forecast (see pipeline/predict/market_probs.py) - not a call.

Run:  python -m pipeline.predict.lock <meeting_date YYYY-MM-DD> <output-name>
"""
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from pipeline.market.ois import latest_forward_curve, latest_sonia
from pipeline.predict.market_probs import market_probs_for_meeting

ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = ROOT / "data" / "index.json"
OUT_DIR = ROOT / "data" / "predictions"
TRAILING_N = 4
MAX_CURVE_STALENESS_BUSINESS_DAYS = 2


def business_days_between(start: dt.date, end: dt.date) -> int:
    """Count of business-day (Mon-Fri) steps from start to end. No UK bank
    holiday calendar (same limitation as pipeline/market/ois_history.py's
    walk-back, which relies on the data itself being absent on holidays
    rather than a calendar) - a holiday inside the window is silently
    counted as a business day here, making this an UNDERcount of true
    staleness, never an overcount."""
    if end < start:
        return -business_days_between(end, start)
    days = 0
    current = start
    while current < end:
        current += dt.timedelta(days=1)
        if current.weekday() < 5:
            days += 1
    return days


def assert_curve_is_fresh(curve_as_of: str, today: dt.date | None = None) -> None:
    """Refuses (raises) if the OIS curve is more than
    MAX_CURVE_STALENESS_BUSINESS_DAYS business days old. Called right
    before writing a lock file, not inside build_prediction() itself, so
    build_prediction() stays usable in tests with an arbitrary injected
    curve date without needing to fake "today" too."""
    today = today or dt.date.today()
    as_of = dt.date.fromisoformat(curve_as_of)
    stale_days = business_days_between(as_of, today)
    if stale_days > MAX_CURVE_STALENESS_BUSINESS_DAYS:
        raise ValueError(
            f"HARD STOP: refusing to write a lock file - OIS curve is {stale_days} "
            f"business day(s) old (curve as_of {as_of.isoformat()}, today {today.isoformat()}), "
            f"more than the {MAX_CURVE_STALENESS_BUSINESS_DAYS}-business-day limit. "
            f"Check pipeline/market/ois.py is pulling the current-month file, not just the archive."
        )


def git_hash() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception as exc:
        return f"unknown ({exc})"


def sha256_of_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def index_stats(n_trailing: int = TRAILING_N) -> dict:
    data = json.loads(INDEX_PATH.read_text())
    docs = sorted((d for d in data["documents"] if d["published"]), key=lambda d: d["published"])
    trailing = [d["abg_net_index"] for d in docs[-n_trailing:]]
    return {
        "index_current": docs[-1]["abg_net_index"],
        "index_current_doc_id": docs[-1]["doc_id"],
        "index_trailing_mean": round(sum(trailing) / len(trailing), 4),
        "index_trailing_n": len(trailing),
    }


def build_prediction(meeting_date: dt.date, curve: dict | None = None, sonia: dict | None = None) -> dict:
    """curve/sonia default to live fetches; pass them explicitly (as in
    the tests) to avoid a live call, e.g. for schema checks."""
    curve = curve if curve is not None else latest_forward_curve()
    sonia = sonia if sonia is not None else latest_sonia()
    m0 = market_probs_for_meeting(curve, sonia, meeting_date)

    ois_snapshot = json.dumps({"curve": curve, "sonia": sonia}, sort_keys=True).encode()
    return {
        "schema": "prediction-v1",
        "meeting_announcement": meeting_date.isoformat(),
        "lock_timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "code_version": git_hash(),
        "input_hashes": {
            "corpus_index_json_sha256": sha256_of_file(INDEX_PATH),
            "ois_snapshot_sha256": hashlib.sha256(ois_snapshot).hexdigest(),
        },
        "m0_market_only": m0,
        **index_stats(),
        "point_call": None,
        "rationale": "TODO(Jake) - written by me before lock",
        "outcome": None,
        "scores": None,
    }


def main() -> None:
    if len(sys.argv) != 3:
        print("usage: python -m pipeline.predict.lock <meeting_date YYYY-MM-DD> <output-name>")
        sys.exit(1)
    meeting_date = dt.date.fromisoformat(sys.argv[1])
    name = sys.argv[2]

    payload = build_prediction(meeting_date)
    assert_curve_is_fresh(payload["m0_market_only"]["curve_as_of"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{name}.json"
    out_path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {out_path}")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
