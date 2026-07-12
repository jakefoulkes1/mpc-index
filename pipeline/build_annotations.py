"""Site-only annotations build step -> data/annotations.json.

NEW, additive, site-layer only. Scans site/annotations/*.md (one file per
episode, named YYYY-MM-slug.md, with two header lines `title:` and `date:`
then a markdown body) and writes them newest-first into
data/annotations.json, which index.html's "Episodes" section fetches.

Why a build step rather than pure client-side fetching: static GitHub Pages
has no directory index, so the front-end can't discover the .md files on its
own. A generated JSON manifest is the same "everything the site reads is a
data/*.json" pattern the rest of this project already uses. Drop a new .md
file in site/annotations/, run `python -m pipeline.build_annotations`, and
it appears on the site.

The body is kept as raw markdown; index.html renders a small, safe subset
(paragraphs, headings, bold/italic, links, bullet lists) client-side - no
markdown library or CDN dependency added.

HARD STOP (never approximate): a .md file missing its title: or date: header
raises rather than being silently skipped or guessed at.

Run:  python -m pipeline.build_annotations
"""
import datetime as dt
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANNOTATIONS_DIR = ROOT / "site" / "annotations"
OUT_PATH = ROOT / "data" / "annotations.json"

HEADER_RE = re.compile(r"^(title|date):\s?(.*)$")


def parse_annotation(text: str, source_name: str) -> dict:
    """Parse leading `title:`/`date:` header lines, then the markdown body.
    HARD STOP if either header is missing - never fabricate a title or date."""
    lines = text.splitlines()
    headers: dict[str, str] = {}
    i = 0
    while i < len(lines):
        m = HEADER_RE.match(lines[i])
        if not m:
            break
        headers[m.group(1)] = m.group(2).strip()
        i += 1
    missing = {"title", "date"} - headers.keys()
    if missing:
        raise ValueError(
            f"HARD STOP: {source_name} is missing required header(s) {missing}. "
            f"Every episode needs a `title:` and `date:` line at the top."
        )
    body = "\n".join(lines[i:]).strip()
    return {"title": headers["title"], "date": headers["date"], "body": body}


def load_episodes(annotations_dir: Path = ANNOTATIONS_DIR) -> list[dict]:
    episodes = []
    for path in sorted(annotations_dir.glob("*.md")):
        parsed = parse_annotation(path.read_text(), path.name)
        parsed["slug"] = path.stem
        episodes.append(parsed)
    # newest first (date is YYYY-MM-DD, so a string sort is chronological);
    # slug is the stable tiebreaker for same-day episodes.
    episodes.sort(key=lambda e: (e["date"], e["slug"]), reverse=True)
    return episodes


def build(annotations_dir: Path = ANNOTATIONS_DIR, generated_utc: str = None) -> dict:
    generated_utc = generated_utc or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    return {
        "schema": "annotations-v1",
        "generated_utc": generated_utc,
        "episodes": load_episodes(annotations_dir),
    }


def main() -> None:
    data = build()
    OUT_PATH.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Wrote {OUT_PATH.relative_to(ROOT)} with {len(data['episodes'])} episode(s):")
    for e in data["episodes"]:
        print(f"  {e['date']}  {e['title']}  ({e['slug']})")


if __name__ == "__main__":
    main()
