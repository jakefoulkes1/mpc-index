"""Site-only track-record build step -> data/track_record.json.

NEW, additive, site-layer only. Reads data/predictions/*.json (written by
pipeline/predict/lock.py - off-limits to modify this session) and writes a
flat, site-shaped summary that index.html's "Track record" section fetches.
Same "everything the site reads is a data/*.json" pattern as
pipeline/build_annotations.py: static GitHub Pages has no directory index,
so the front-end can't discover data/predictions/*.json files on its own.

Read-only with respect to data/predictions/*.json - this script never
writes back into that directory, and files under data/predictions/lock-*
are never modified once written (see CLAUDE.md). "locked" here is
determined purely by filename prefix ("lock-"), matching that same
project-wide convention; anything else (dryrun-*, rehearsal-*, ...) is
rendered as a non-locked draft.

Brier note: pipeline/predict/score_outcomes.py only scores the m0
market-only reference forecast (and an always-hold baseline) - point_call
is a categorical single guess, not a probability distribution, so there is
currently no Brier score defined for the point_call itself. The "brier"
field below is m0's, labelled accordingly on the site. See DECISIONS.md.

Run:  python -m pipeline.build_track_record
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREDICTIONS_DIR = ROOT / "data" / "predictions"
OUT_PATH = ROOT / "data" / "track_record.json"

REQUIRED_FIELDS = (
    "meeting_announcement", "lock_timestamp", "point_call",
    "m0_market_only", "outcome",
)


def _kind_of(filename: str) -> str:
    if filename.startswith("lock-"):
        return "locked"
    if filename.startswith("rehearsal-"):
        return "rehearsal"
    if filename.startswith("dryrun-"):
        return "dryrun"
    return "other"


def load_prediction_summary(path: Path) -> dict:
    payload = json.loads(path.read_text())
    missing = set(REQUIRED_FIELDS) - payload.keys()
    if missing:
        raise ValueError(
            f"HARD STOP: {path.name} is missing field(s) {missing} - "
            f"not a well-formed prediction-v1 file, refusing to guess."
        )
    m0 = payload["m0_market_only"]
    scores = payload.get("scores")
    return {
        "filename": path.name,
        "kind": _kind_of(path.name),
        "meeting_announcement": payload["meeting_announcement"],
        "lock_timestamp": payload["lock_timestamp"],
        "point_call": payload["point_call"],
        "m0_market_only": {
            "p_cut": m0["p_cut"], "p_hold": m0["p_hold"], "p_hike": m0["p_hike"],
        },
        "outcome": payload["outcome"],
        "brier_m0": scores["m0_market_only"]["brier_score"] if scores else None,
    }


def build(predictions_dir: Path = PREDICTIONS_DIR) -> dict:
    records = [load_prediction_summary(p) for p in sorted(predictions_dir.glob("*.json"))]
    records.sort(key=lambda r: (r["meeting_announcement"], r["filename"]))
    return {
        "schema": "track-record-v1",
        "first_pre_registered_call": "2026-07-30",
        "records": records,
    }


def main() -> None:
    data = build()
    OUT_PATH.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Wrote {OUT_PATH.relative_to(ROOT)} with {len(data['records'])} record(s):")
    for r in data["records"]:
        print(f"  {r['filename']}  kind={r['kind']}  meeting={r['meeting_announcement']}")


if __name__ == "__main__":
    main()
