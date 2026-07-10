"""Download the Bank's MPC voting-history spreadsheet (ground truth for validation).

Run on your own machine:  python -m pipeline.scrape.votes
"""
from pathlib import Path

import requests

URL = ("https://www.bankofengland.co.uk/-/media/boe/files/"
       "monetary-policy-summary-and-minutes/mpcvoting.xlsx")
ROOT = Path(__file__).resolve().parents[2]

if __name__ == "__main__":
    out = ROOT / "data" / "raw" / "mpcvoting.xlsx"
    out.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(URL, headers={"User-Agent": "mpc-index research scraper"}, timeout=60)
    resp.raise_for_status()
    out.write_bytes(resp.content)
    print(f"wrote {out} ({len(resp.content)//1024} KB)")
