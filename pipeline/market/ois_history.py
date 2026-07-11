"""Full Aug 2015-present history of the Bank's daily OIS forward curve and
SONIA, for the historical market benchmark (see DECISIONS.md, 2026-08-01).

Merges every era file in oisddata.zip into one date-indexed lookup (see
pipeline/market/ois.py for the file/sheet layout - the "archive files ...
by year" turned out to be one multi-era zip, not one file per calendar
year; see DECISIONS.md). HARD STOP if any era file can't be parsed with
one of the known sheet names: unlike latest_forward_curve() (which only
needs the CURRENT era and can skip an older file using a different
layout), a full history needs EVERY era file to parse, so a
missing/malformed sheet here is a hard stop, not a skip.

Run:  python -m pipeline.market.ois_history
"""
import datetime as dt
import time

import requests

from pipeline.market.ois import (
    FORWARD_SHEET_NAMES,
    HEADERS,
    SONIA_CSV_URL,
    SONIA_SERIES_CODE,
    _read_forward_curve_sheet,
    download_ois_zip,
    parse_sonia_csv,
)


def load_full_curve_history() -> dict[dt.date, dict]:
    """{date: {"maturities_months", "forward_rates_pct", "source_file",
    "sheet"}} merged across every era file in oisddata.zip."""
    oisdata_dir = download_ois_zip()
    xlsx_files = sorted(oisdata_dir.glob("*.xlsx"))
    if not xlsx_files:
        raise ValueError(f"HARD STOP: oisddata.zip extracted no .xlsx files into {oisdata_dir}")

    history: dict[dt.date, dict] = {}
    for path in xlsx_files:
        parsed = _read_forward_curve_sheet(path, sheet_names=FORWARD_SHEET_NAMES)
        if parsed is None:
            raise ValueError(
                f"HARD STOP: {path.name} has none of the known sheet names {FORWARD_SHEET_NAMES} - "
                f"a full history needs every era file to parse, unlike the latest-only lookup."
            )
        sheet_name, maturities, rows = parsed
        for date, rates in rows:
            history[date] = {
                "maturities_months": maturities,
                "forward_rates_pct": rates,
                "source_file": path.name,
                "sheet": sheet_name,
            }
    return history


def load_full_sonia_history(start: dt.date) -> dict[dt.date, float]:
    date_from = start.strftime("%d/%b/%Y")
    url = SONIA_CSV_URL.format(date_from=date_from, code=SONIA_SERIES_CODE)
    resp = requests.get(url, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    time.sleep(2.0)
    return dict(parse_sonia_csv(resp.text))


def find_nearest_available_date(available_dates: set[dt.date], target: dt.date, max_walk: int = 10) -> tuple[dt.date, int]:
    """Walks backward from target one calendar day at a time until it
    finds a date present in available_dates (a weekend or bank holiday
    simply isn't a key in either the curve or SONIA history, so this one
    mechanism covers both without a separate holiday calendar). Returns
    (date_used, days_walked_back) - walked > 0 is logged by the caller."""
    candidate = target
    walked = 0
    while candidate not in available_dates:
        candidate -= dt.timedelta(days=1)
        walked += 1
        if walked > max_walk:
            raise ValueError(f"HARD STOP: no available date found within {max_walk} days at or before {target}")
    return candidate, walked
