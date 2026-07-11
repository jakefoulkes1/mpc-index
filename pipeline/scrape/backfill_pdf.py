"""Backfill full minutes text for Summary-only HTML pages via the Bank's PDF minutes.

Until August 2021 the Bank published the Monetary Policy Summary on the HTML
page and the full Minutes only as a separate linked PDF; from August 2021 it
started publishing the full minutes inline in HTML. Detected empirically by
inspecting live pages, not assumed - see DECISIONS.md.

For every data/raw/*.txt file that is Summary-only (little or no text after
the "Minutes of the Monetary Policy Committee meeting ending on" heading),
this script downloads the matching PDF, extracts its text with pdfplumber,
and replaces the raw .txt with the full text. Origin is recorded per file in
data/raw/source_kind.json ("html" or "pdf") for build_index.py to read.

Run on your own machine:
    python -m pipeline.scrape.backfill_pdf
"""
import json
import re
import time
from pathlib import Path

import pdfplumber
import requests

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PDF_DIR = RAW / "pdf"
SOURCE_KIND_PATH = RAW / "source_kind.json"
HEADERS = {"User-Agent": "mpc-index research scraper (contact: jakefoulkes@aol.com)"}

FILENAME_RE = re.compile(r"^(\d{4})-(\d{2})-minutes\.txt$")
MONTH_NAMES = ["january", "february", "march", "april", "may", "june",
               "july", "august", "september", "october", "november", "december"]
# The March 2020 special/emergency meeting PDF heads with "Minutes of the
# special Monetary Policy Committee" instead of the usual phrasing.
HEADING_RE = re.compile(r"Minutes of the(?: special)? Monetary Policy Committee")
# Words found after the heading; below this the page is Summary-only.
SUMMARY_ONLY_THRESHOLD = 400


def is_summary_only(text: str) -> bool:
    m = HEADING_RE.search(text)
    if not m:
        return True
    return len(text[m.end():].split()) < SUMMARY_ONLY_THRESHOLD


def pdf_urls(year: int, month_num: int) -> list[str]:
    """Candidate PDF URLs, most common pattern first.

    Most months: "<month>-<year>.pdf". A few (2015-08, 2015-12, 2017-06)
    instead use "minutes-<month>-<year>.pdf" - discovered by checking the
    live HTML page's own PDF link after the first pattern 404d.
    """
    month = MONTH_NAMES[month_num - 1]
    base = f"https://www.bankofengland.co.uk/-/media/boe/files/monetary-policy-summary-and-minutes/{year}"
    return [f"{base}/{month}-{year}.pdf", f"{base}/minutes-{month}-{year}.pdf"]


def extract_pdf_text(path: Path) -> str:
    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def main() -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    source_kind = json.loads(SOURCE_KIND_PATH.read_text()) if SOURCE_KIND_PATH.exists() else {}

    replaced, failed = [], []
    for path in sorted(RAW.glob("*.txt")):
        m = FILENAME_RE.match(path.name)
        if not m:
            continue
        text = path.read_text()
        if not is_summary_only(text):
            source_kind.setdefault(path.name, "html")
            continue

        year, month_num = int(m.group(1)), int(m.group(2))
        pdf_path = PDF_DIR / f"{path.stem}.pdf"
        resp, url, last_exc = None, None, None
        for candidate_url in pdf_urls(year, month_num):
            try:
                candidate_resp = requests.get(candidate_url, headers=HEADERS, timeout=30)
                candidate_resp.raise_for_status()
                resp, url = candidate_resp, candidate_url
                break
            except requests.exceptions.RequestException as exc:
                last_exc = exc
            finally:
                time.sleep(2.0)

        if resp is None:
            print(f"{path.name}: PDF fetch failed ({last_exc}) - left as summary-only")
            failed.append(path.name)
            continue

        pdf_path.write_bytes(resp.content)
        pdf_text = extract_pdf_text(pdf_path)
        word_count = len(pdf_text.split())
        if word_count < SUMMARY_ONLY_THRESHOLD:
            print(f"{path.name}: PDF extraction still short ({word_count} words) - not replacing, flagging")
            failed.append(path.name)
            continue
        path.write_text(pdf_text)
        source_kind[path.name] = "pdf"
        replaced.append(path.name)
        print(f"{path.name}: replaced with PDF text ({word_count} words)  {url}")

    SOURCE_KIND_PATH.write_text(json.dumps(source_kind, indent=2, sort_keys=True) + "\n")
    print(f"\nreplaced: {len(replaced)}  failed/left summary-only: {len(failed)}")
    if failed:
        print("failed/left as summary-only:", failed)


if __name__ == "__main__":
    main()
