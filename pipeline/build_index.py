"""Build data/index.json from cached raw documents.

Documents are discovered over data/raw/*.txt (one file per scraped meeting,
named YYYY-MM-minutes.txt by pipeline/scrape/era.py). For each document:
- meeting_end is parsed from the "At its meeting ending on <date>..." sentence.
- published is meeting_end + 1 day, the announcement-date rule for this era
  (see DECISIONS.md).
- decision and vote are parsed from the same sentence's "voted (by a majority
  of A-B | unanimously) to <decision clause>" construction.
Any field that doesn't parse is left null and logged - never guessed.

Run:  python -m pipeline.build_index
"""
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

from pipeline.score.dictionary import load_lexicon, score_document, split_sentences

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "index.json"

FILENAME_RE = re.compile(r"^(\d{4})-(\d{2})-minutes\.txt$")
# "ending on <date>" is the usual phrasing; a few 2016 pages drop the "on".
MEETING_END_RE = re.compile(r"meeting ending (?:on )?(\d{1,2} [A-Za-z]+ \d{4})")
# Vote split uses an ASCII hyphen in older pages, an en dash (–) in newer ones.
# "by a majority of A-B" is the usual phrasing; some 2017 summary pages drop
# it and just say "voted A-B to ...". The majority/unanimously qualifier is
# itself optional: a few multi-way splits (e.g. 5-3-1 three ways) are stated
# in prose in the next sentence instead, so here we can still parse the
# decision but must leave vote null rather than guess.
VOTE_RE = re.compile(
    r"voted(?: (?:(?:by a majority of )?(\d+[-–—]\d+)|(unanimously)))? to (.+)"
)
MONTH_NAMES = ["january", "february", "march", "april", "may", "june",
               "july", "august", "september", "october", "november", "december"]

# 2015-2016 pages use a "mpc-<month>-<year>" URL slug; 2017 on uses "<month>-<year>".
# Discovered empirically while writing pipeline/scrape/era.py - see DECISIONS.md.
PREFIXED_SLUG_LAST_YEAR = 2016


def source_url(year: int, month_num: int) -> str:
    month = MONTH_NAMES[month_num - 1]
    slug = f"mpc-{month}-{year}" if year <= PREFIXED_SLUG_LAST_YEAR else f"{month}-{year}"
    return f"https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes/{year}/{slug}"


def find_vote_sentence(text: str) -> str | None:
    """First sentence stating the Bank Rate vote. Usually the same sentence as
    "meeting ending on", but some eras (e.g. 2021) split them in two."""
    for sentence in split_sentences(text):
        if "voted" in sentence and "Bank Rate" in sentence:
            return sentence
    return None


def parse_entry(path: Path) -> dict | None:
    m = FILENAME_RE.match(path.name)
    if not m:
        return None
    year, month_num = int(m.group(1)), int(m.group(2))
    text = path.read_text()

    entry = {
        "doc_id": f"minutes-{year:04d}-{month_num:02d}",
        "type": "minutes",
        "meeting_end": None,
        "published": None,
        "decision": None,
        "vote": None,
        "source_url": source_url(year, month_num),
    }

    date_m = MEETING_END_RE.search(text)
    if date_m:
        meeting_end = dt.datetime.strptime(date_m.group(1), "%d %B %Y").date()
        entry["meeting_end"] = meeting_end.isoformat()
        entry["published"] = (meeting_end + dt.timedelta(days=1)).isoformat()
    else:
        print(f"log: {path.name}: 'meeting ending on' date unparseable (likely missing year in source text) - meeting_end/published left null")

    sentence = find_vote_sentence(text)
    if sentence is None:
        print(f"log: {path.name}: no vote sentence found - decision/vote left null")
        return entry

    vote_m = VOTE_RE.search(sentence)
    if vote_m:
        entry["decision"] = vote_m.group(3).strip().rstrip(".")
        if vote_m.group(1):
            # Normalise en/em dash vote splits to a plain hyphen for a consistent field.
            entry["vote"] = re.sub(r"[–—]", "-", vote_m.group(1))
        elif vote_m.group(2):
            entry["vote"] = "unanimous"
        else:
            print(f"log: {path.name}: decision parsed but vote split not stated as majority/unanimous (likely a multi-way split described in prose) - vote left null")
    else:
        print(f"log: {path.name}: vote/decision clause unparseable - left null")

    return entry


def main() -> None:
    lexicon = load_lexicon()
    documents, series = [], []
    for path in sorted(RAW.glob("*.txt")):
        entry = parse_entry(path)
        if entry is None:
            print(f"skip (unrecognised filename): {path.name}")
            continue
        text = path.read_text()
        entry["sha256"] = hashlib.sha256(text.encode()).hexdigest()
        entry.update(score_document(text, lexicon))
        documents.append(entry)
        if entry["published"]:
            series.append({
                "date": entry["published"],
                "net_hawkishness": entry["net_hawkishness"],
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
    print(f"wrote {OUT} ({len(documents)} document(s), {len(series)} in series)")


if __name__ == "__main__":
    main()
