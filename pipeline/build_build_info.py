"""Builds data/build_info.json: when the site was last updated, taken from
git rather than from a hand-typed date.

Site layer, additive: reads nothing but `git log`, writes one NEW json file,
touches no existing schema and nothing under data/predictions/.

The stamp names the commit that was HEAD when this script ran, so the
correct order on a release day is: commit the content, then run this, then
commit data/build_info.json and the two rewritten stamps on their own. That
second commit changes no prose, so the stamp always points at the commit the
reader is actually looking at. See DECISIONS.md, 2026-07-30.

As well as the json, this rewrites the static `<!-- fallback:buildinfo -->`
stamp in both HTML pages - index.html, which also refreshes it by fetch, and
methodology.html, which runs no JavaScript and has only the static one. They
are rewritten here rather than by hand because
pipeline/tests/test_static_fallback.py asserts they match the json, and a
hand-edit is exactly the step that gets forgotten.

Run:  python -m pipeline.build_build_info
"""
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "build_info.json"
PAGES = (ROOT / "index.html", ROOT / "methodology.html")
COMMIT_URL = "https://github.com/jakefoulkes1/mpc-index/commit/"


def _git(*args: str) -> str:
    """Run a git command in the repo and return its stripped stdout.

    Raises rather than falling back to a guessed value: a wrong "last
    updated" date is worse than no build_info.json at all.
    """
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def collect() -> dict:
    return {
        "schema": "build-info-v1",
        "last_commit_sha": _git("log", "-1", "--format=%H"),
        "last_commit_short_sha": _git("log", "-1", "--format=%h"),
        # Committer date, ISO-8601 with offset: the moment the commit last
        # entered this history, which is what "last updated" means to a reader.
        "last_commit_iso": _git("log", "-1", "--format=%cI"),
        "last_commit_subject": _git("log", "-1", "--format=%s"),
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": (
            "Written by pipeline/build_build_info.py from git log -1 at the time "
            "it ran. Not a claim about the data's vintage - data/index.json "
            "carries its own generated_utc."
        ),
    }


def stamp_html(info: dict) -> str:
    """The stamp sentence, in the site's own date format."""
    d = datetime.fromisoformat(info["last_commit_iso"])
    shown = f"{d.day} {d.strftime('%B')} {d.year}"
    return (
        f'Site last updated {shown} (<a\n'
        f'      href="{COMMIT_URL}{info["last_commit_sha"]}"'
        f'><code>{info["last_commit_short_sha"]}</code></a>).'
    )


def rewrite_stamps(info: dict) -> list[str]:
    """Replace the sentence inside each page's fallback:buildinfo region.

    Only the text between the markers is touched - the surrounding markup,
    including index.html's #build-note span, is left exactly as it is.
    """
    sentence = stamp_html(info)
    touched = []
    for page in PAGES:
        html = page.read_text()
        pattern = re.compile(
            r"(<!--\s*fallback:buildinfo\b.*?-->.*?)"
            r"(Site last updated .*?\)\.)"
            r"(.*?<!--\s*/fallback:buildinfo\s*-->)",
            re.S,
        )
        new, n = pattern.subn(lambda m: m.group(1) + sentence + m.group(3), html)
        if n != 1:
            raise ValueError(
                f"{page.name}: expected exactly 1 fallback:buildinfo stamp, found {n}"
            )
        if new != html:
            page.write_text(new)
            touched.append(page.name)
    return touched


def main() -> None:
    info = collect()
    OUT.write_text(json.dumps(info, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  {info['last_commit_short_sha']}  {info['last_commit_iso']}  {info['last_commit_subject']}")
    touched = rewrite_stamps(info)
    print(f"  stamps rewritten: {', '.join(touched) if touched else 'none (already current)'}")


if __name__ == "__main__":
    main()
