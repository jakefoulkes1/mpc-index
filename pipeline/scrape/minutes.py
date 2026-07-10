"""Fetch and cache MPC Monetary Policy Summary & minutes pages (Aug 2015-present).

Run on your own machine:
    python -m pipeline.scrape.minutes 2026 april
Caches raw HTML to data/raw/html/ and extracted text to data/raw/.
One request at a time, identified User-Agent, 2s sleep: polite scraping is method.
"""
import hashlib
import sys
import time
from pathlib import Path

import requests

from pipeline.parse.html_text import html_to_text

BASE = "https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes"
HEADERS = {"User-Agent": "mpc-index research scraper (contact: jakefoulkes@aol.com)"}
MONTH_NUM = {m: i + 1 for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june",
     "july", "august", "september", "october", "november", "december"])}
ROOT = Path(__file__).resolve().parents[2]


def minutes_url(year: int, month: str, prefixed: bool = False) -> str:
    slug = f"mpc-{month.lower()}-{year}" if prefixed else f"{month.lower()}-{year}"
    return f"{BASE}/{year}/{slug}"


def scrape_month(year: int, month: str) -> Path:
    raw_html = ROOT / "data" / "raw" / "html"
    raw_html.mkdir(parents=True, exist_ok=True)
    url = minutes_url(year, month)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    if resp.status_code == 404:
        # 2015-2016 pages use a "mpc-<month>-<year>" slug instead of "<month>-<year>".
        time.sleep(2.0)
        alt_url = minutes_url(year, month, prefixed=True)
        alt_resp = requests.get(alt_url, headers=HEADERS, timeout=30)
        if alt_resp.status_code != 404:
            url, resp = alt_url, alt_resp
    resp.raise_for_status()
    time.sleep(2.0)
    stem = f"{year}-{MONTH_NUM[month.lower()]:02d}-minutes"
    (raw_html / f"{stem}.html").write_text(resp.text)
    text = html_to_text(resp.text)
    out = ROOT / "data" / "raw" / f"{stem}.txt"
    out.write_text(text)
    digest = hashlib.sha256(text.encode()).hexdigest()[:16]
    print(f"{url}\n -> {out}  sha256={digest}...  ({len(text.split())} words)")
    return out


if __name__ == "__main__":
    scrape_month(int(sys.argv[1]), sys.argv[2])
