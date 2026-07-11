"""Parse the Bank's mpcvoting.xlsx into data/votes.csv.

One row per (meeting, member): the member's preferred Bank Rate against the
decided rate, plus meeting-level skew and dissent counts (repeated on every
row for that meeting - a standard denormalised CSV, easy to load and group).

skew = average(preferred rates of all voting members) - decided rate,
following Apel & Blix Grimaldi (2012) p.13 (after Gerlach-Kristen 2004):
skew = average(r_j) - r. Positive skew = committee leaned for a higher rate
than decided (hawkish dissent); negative = leaned lower (dovish dissent).

The sheet's own date column is the meeting's PUBLISHED/announcement date,
not the meeting_end date - confirmed by cross-checking known dates (e.g.
2026-06-18 matches minutes-2026-06's `published` field, not its
`meeting_end` of 2026-06-17). Rates are decimals (0.0375 = 3.75%), kept as
given in the source.

Run:  python -m pipeline.build_votes
"""
import csv
import datetime as dt
import json
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
XLSX_PATH = ROOT / "data" / "raw" / "mpcvoting.xlsx"
INDEX_PATH = ROOT / "data" / "index.json"
OUT = ROOT / "data" / "votes.csv"

HEADER_ROW = 4
LABEL_COLUMNS = {"Current members", "Past members"}
# Matches this repo's scraped era (see DECISIONS.md). A few pre-2015 rows
# record a dissent as qualitative "Increase"/"Decrease" text with no rate
# (e.g. 1998), which the era filter also sidesteps.
ERA_START = dt.date(2015, 8, 1)
ERA_END = dt.date(2026, 7, 1)


def load_member_columns(ws) -> dict[int, str]:
    columns = {}
    for cell in ws[HEADER_ROW]:
        if cell.value and cell.value not in LABEL_COLUMNS:
            name = " ".join(str(cell.value).split())  # collapse embedded newlines
            columns[cell.column - 1] = name
    return columns


def parse_meetings(ws, member_columns: dict[int, str]) -> list[dict]:
    meetings = []
    for row in ws.iter_rows(min_row=HEADER_ROW + 1, values_only=True):
        date, decided = row[1], row[2]
        if not isinstance(date, dt.datetime) or not isinstance(decided, (int, float)):
            continue
        if not (ERA_START <= date.date() < ERA_END):
            continue
        votes = {}
        for i, name in member_columns.items():
            v = row[i]
            if v is None:
                continue
            if not isinstance(v, (int, float)):
                print(f"log: {date.date()}: {name}'s vote is non-numeric ({v!r}) - excluded from skew/dissent counts")
                continue
            votes[name] = v
        if not votes:
            continue
        preferred = list(votes.values())
        skew = sum(preferred) / len(preferred) - decided
        hawkish_dissents = sum(1 for r in preferred if r > decided)
        dovish_dissents = sum(1 for r in preferred if r < decided)
        meetings.append({
            "meeting_date": date.date().isoformat(),
            "decided_rate": decided,
            "skew": round(skew, 6),
            "hawkish_dissents": hawkish_dissents,
            "dovish_dissents": dovish_dissents,
            "votes": votes,
        })
    return meetings


def reconcile_against_corpus(meetings: list[dict]) -> None:
    if not INDEX_PATH.exists():
        print("no index.json to reconcile against - skipping reconciliation")
        return
    corpus = json.loads(INDEX_PATH.read_text())
    corpus_published = {d["published"] for d in corpus["documents"] if d["published"]}
    sheet_dates = {m["meeting_date"] for m in meetings}

    era_start, era_end = "2015-08-01", "2026-07-01"
    corpus_only = sorted(d for d in corpus_published if era_start <= d < era_end and d not in sheet_dates)
    sheet_only = sorted(d for d in sheet_dates if era_start <= d < era_end and d not in corpus_published)

    print(f"reconciliation (published date == voting-sheet meeting date, {era_start} to {era_end}):")
    print(f"  in corpus, no matching voting-sheet row ({len(corpus_only)}): {corpus_only}")
    print(f"  in voting sheet, no matching corpus document ({len(sheet_only)}): {sheet_only}")


def main() -> None:
    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
    ws = wb["Bank Rate Decisions"]
    member_columns = load_member_columns(ws)
    meetings = parse_meetings(ws, member_columns)

    with open(OUT, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["meeting_date", "decided_rate", "member", "preferred_rate",
                          "skew", "hawkish_dissents", "dovish_dissents"])
        for m in meetings:
            for member, preferred in sorted(m["votes"].items()):
                writer.writerow([m["meeting_date"], m["decided_rate"], member, preferred,
                                  m["skew"], m["hawkish_dissents"], m["dovish_dissents"]])

    print(f"wrote {OUT} ({len(meetings)} meetings, {sum(len(m['votes']) for m in meetings)} member-votes)")
    reconcile_against_corpus(meetings)


if __name__ == "__main__":
    main()
