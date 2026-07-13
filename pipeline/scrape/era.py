"""Scrape the full Aug 2015-Jun 2026 minutes era.

The MPC met monthly through 2015, then moved to 8 meetings/year ("Super
Thursday") from 2016 onward. Rather than hardcode which months have a
meeting, this just tries every month in the range and tolerates 404s for
months with no meeting.

Governed by DECISIONS.md: 2026-07-11 (era corpus - schedule discovered by
trying, two URL slug patterns, suspect-parse threshold).

Run on your own machine:
    python -m pipeline.scrape.era
"""
import requests

from pipeline.scrape.minutes import scrape_month

START = (2015, 8)
END = (2026, 6)
MONTHS = ["january", "february", "march", "april", "may", "june",
          "july", "august", "september", "october", "november", "december"]
MIN_WORDS = 1000


def month_range(start: tuple[int, int], end: tuple[int, int]):
    year, month = start
    while (year, month) <= end:
        yield year, MONTHS[month - 1]
        month += 1
        if month > 12:
            month = 1
            year += 1


def main() -> None:
    scraped, missing, suspect = [], [], []
    for year, month in month_range(START, END):
        try:
            path = scrape_month(year, month)
        except requests.exceptions.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status == 404:
                print(f"{year}-{month}: no meeting (404)")
                missing.append((year, month))
            else:
                print(f"{year}-{month}: HTTP error {status}, skipping")
                missing.append((year, month))
            continue
        word_count = len(path.read_text().split())
        scraped.append((year, month, word_count))
        if word_count < MIN_WORDS:
            print(f"{year}-{month}: SUSPECT PARSE ({word_count} words < {MIN_WORDS})")
            suspect.append((year, month, word_count))

    print("\n--- era scrape summary ---")
    print(f"scraped: {len(scraped)}")
    print(f"no meeting / error: {len(missing)}")
    print(f"suspect parses (<{MIN_WORDS} words): {len(suspect)}")
    for year, month, wc in suspect:
        print(f"  {year}-{month}: {wc} words")


if __name__ == "__main__":
    main()
