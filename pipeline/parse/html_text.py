"""HTML -> clean text for Bank of England pages (post-2015 era).

Input: raw page HTML (as cached under data/raw/html/ by pipeline/scrape).
Output: plain text with boilerplate/navigation stripped, ready for
pipeline/score and the metadata parsing in pipeline/build_index.

Governed by DECISIONS.md: 2026-07-11 (era corpus) and the 2026-07-11
corpus audit (Summary-only pages vs full minutes).
"""
import re
from bs4 import BeautifulSoup

_STRIP = ("script", "style", "nav", "header", "footer", "form", "noscript", "aside")


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main") or soup.find(id="main-content") or soup.body or soup
    for tag in main.find_all(_STRIP):
        tag.decompose()
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in main.get_text("\n").splitlines()]
    return "\n".join(ln for ln in lines if len(ln) > 2)
