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

from pipeline.score.abg import NEUTRAL_VALUE, load_abg_lexicon, score_document as score_document_abg
from pipeline.score.dictionary import split_sentences

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "index.json"
SOURCE_KIND_PATH = RAW / "source_kind.json"

FILENAME_RE = re.compile(r"^(\d{4})-(\d{2})-minutes\.txt$")
SPECIAL_FILENAME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-special-minutes\.txt$")
# Emergency/special meetings live at ad-hoc URLs, not the month-slug pattern -
# found by reconciling against the Bank's own sitemap, not guessed. Extend
# this table if more are found reconciling other eras. See DECISIONS.md.
SPECIAL_SOURCE_URLS = {
    "2020-03-10": "https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes/2020/13march-2020",
    "2020-03-19": "https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes/2020/monetary-policy-summary-for-the-special-monetary-policy-committee-meeting-on-19-march-2020",
}
# "ending on <date>" is the usual phrasing; a few 2016 pages drop the "on".
# The 19 March 2020 special-meeting summary uses neither - it has no full
# minutes text at all (see DECISIONS.md), only a page title reading
# "special Monetary Policy Committee meeting on <date>".
MEETING_END_RE = re.compile(
    r"(?:meeting ending (?:on )?|special Monetary Policy Committee meeting on )(\d{1,2} [A-Za-z]+ \d{4})"
)
# Vote split uses an ASCII hyphen in older pages, an en dash (–) in newer ones.
# "by a majority of A-B" is the usual phrasing; some 2017 summary pages drop
# it and just say "voted A-B to ...". The majority/unanimously qualifier is
# itself optional: a few multi-way splits (e.g. 5-3-1 three ways) are stated
# in prose in the next sentence instead, so here we can still parse the
# decision but must leave vote null rather than guess.
VOTE_RE = re.compile(
    r"voted(?: (?:(?:by a majority of )?(\d+[-–—]\d+)|(unanimously)))? to (.+)"
)
# Fallback for "package of measures" style meetings (e.g. 2016-08, the
# 2020-03-10 special) where the Bank Rate decision is stated as one of
# several Governor's propositions, confirmed later by a plain "voted ...
# in favour of the propositions" sentence that doesn't itself restate the
# rate - so VOTE_RE finds no single "voted ... to X" clause. Recovers real
# text, doesn't fabricate: only fires if BOTH the proposition statement
# AND its adoption are found. See DECISIONS.md.
PROPOSITION_RE = re.compile(
    r"propositions? that:\s*Bank Rate (?:should be |be )?(reduced|increased) by "
    r"(\d+(?:\.\d+)?) basis points?,? to (\d+(?:\.\d+)?)%"
)
PROPOSITION_CONFIRMED_RE = re.compile(
    r"voted (?:by a majority of (\d+[-–—]\d+)|(unanimously)) in favour of "
    r"(?:all (?:\w+ )?propositions?|the propositions?)"
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


def try_proposition_fallback(text: str) -> dict | None:
    """Recovers decision/vote from a Governor's-proposition + adoption
    pair when no single "voted ... to X" sentence exists. Returns None if
    either half of the pair isn't found - never guesses from one alone."""
    prop_m = PROPOSITION_RE.search(text)
    if not prop_m:
        return None
    confirm_m = PROPOSITION_CONFIRMED_RE.search(text)
    if not confirm_m:
        return None
    verb_past, magnitude, level = prop_m.groups()
    verb = "reduce" if verb_past == "reduced" else "increase"
    vote = re.sub(r"[–—]", "-", confirm_m.group(1)) if confirm_m.group(1) else "unanimous"
    return {
        "decision": f"{verb} Bank Rate by {magnitude} basis points to {level}%",
        "vote": vote,
        "raw_vote_text": f"{prop_m.group(0).strip()} [...] {confirm_m.group(0).strip()}",
    }


def find_vote_sentence(text: str) -> str | None:
    """First sentence stating the Bank Rate vote. Usually the same sentence as
    "meeting ending on", but some eras (e.g. 2021) split them in two. Case-
    insensitive: some PDF extractions render it "Bank rate" (lowercase r)."""
    for sentence in split_sentences(text):
        if "voted" in sentence and "bank rate" in sentence.lower():
            return sentence
    return None


def parse_entry(path: Path, source_kind: dict) -> dict | None:
    m = FILENAME_RE.match(path.name)
    special_m = SPECIAL_FILENAME_RE.match(path.name) if not m else None
    if not m and not special_m:
        return None

    if m:
        year, month_num = int(m.group(1)), int(m.group(2))
        doc_id = f"minutes-{year:04d}-{month_num:02d}"
        doc_type = "minutes"
        url = source_url(year, month_num)
    else:
        year, month_num, day = int(special_m.group(1)), int(special_m.group(2)), int(special_m.group(3))
        doc_id = f"minutes-{year:04d}-{month_num:02d}-{day:02d}-special"
        doc_type = "special_minutes"
        key = f"{year:04d}-{month_num:02d}-{day:02d}"
        url = SPECIAL_SOURCE_URLS.get(key)
        if url is None:
            print(f"log: {path.name}: no known source_url for special meeting {key} - source_url left null")

    text = path.read_text()

    entry = {
        "doc_id": doc_id,
        "type": doc_type,
        "meeting_end": None,
        "published": None,
        "decision": None,
        "vote": None,
        # Verbatim sentence the decision/vote were parsed from, whenever one is
        # found - kept even when decision/vote don't fully parse (e.g. a
        # multi-way split not representable as "A-B") so no information is lost.
        "raw_vote_text": None,
        "source_url": url,
        # "pdf" where the HTML page was Summary-only and full minutes were
        # backfilled from the Bank's PDF (pipeline/scrape/backfill_pdf.py);
        # "html" where the HTML page already had the full minutes inline.
        "source_kind": source_kind.get(path.name, "html"),
        "word_count": len(text.split()),
    }

    date_m = MEETING_END_RE.search(text)
    if date_m:
        meeting_end = dt.datetime.strptime(date_m.group(1), "%d %B %Y").date()
        entry["meeting_end"] = meeting_end.isoformat()
        entry["published"] = (meeting_end + dt.timedelta(days=1)).isoformat()
    else:
        print(f"log: {path.name}: 'meeting ending on' date unparseable (likely missing year in source text) - meeting_end/published left null")

    sentence = find_vote_sentence(text)
    if sentence is not None:
        entry["raw_vote_text"] = sentence.strip()
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
            print(f"log: {path.name}: vote/decision clause unparseable - trying proposition fallback")
    else:
        print(f"log: {path.name}: no vote sentence found - trying proposition fallback")

    if entry["decision"] is None:
        fallback = try_proposition_fallback(text)
        if fallback:
            entry.update(fallback)
            print(f"log: {path.name}: recovered decision/vote via Governor's-proposition fallback")
        else:
            print(f"log: {path.name}: decision/vote left null - no proposition fallback pattern found either")

    return entry


def main() -> None:
    abg_lexicon = load_abg_lexicon()
    source_kind = json.loads(SOURCE_KIND_PATH.read_text()) if SOURCE_KIND_PATH.exists() else {}
    documents, series = [], []
    for path in sorted(RAW.glob("*.txt")):
        entry = parse_entry(path, source_kind)
        if entry is None:
            print(f"skip (unrecognised filename): {path.name}")
            continue
        text = path.read_text()
        entry["sha256"] = hashlib.sha256(text.encode()).hexdigest()
        entry.update(score_document_abg(text, abg_lexicon))
        documents.append(entry)
        if entry["published"]:
            series.append({
                "date": entry["published"],
                "abg_net_index": entry["abg_net_index"],
                "doc_id": entry["doc_id"],
            })

    payload = {
        "schema": "index-v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "lexicon": "abg_2012 (Apel & Blix Grimaldi 2012, verbatim - see pipeline/score/lexicon/abg_2012.json and DECISIONS.md). starter_v0 remains in the repo as plumbing only and is no longer used in any output.",
        # Net Index = [(#hawk/(#hawk+#dove)) - (#dove/(#hawk+#dove))] + 1 (paper
        # p.10); ratio-type, fixed midpoint, range [0,2]. See DECISIONS.md.
        "neutral_value": NEUTRAL_VALUE,
        "documents": documents,
        "series": sorted(series, key=lambda row: row["date"]),
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {OUT} ({len(documents)} document(s), {len(series)} in series)")


if __name__ == "__main__":
    main()
