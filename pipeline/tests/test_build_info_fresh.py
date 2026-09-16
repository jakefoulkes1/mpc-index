"""Guard: data/build_info.json must describe the commit it ships with.

The footer's "Site last updated" line is generated data, not a live read, so
it goes stale silently. On 2026-08-05 it had been sitting at a750062 for five
days across two content commits, and the site looked like a broken deploy when
it was in fact serving the tip of main correctly.

The invariant this enforces is narrow and mechanical:

    build_info.json names HEAD

with exactly one allowance - HEAD may be the *stamp commit* for the commit
build_info.json names. That is the documented two-step in
pipeline/build_build_info.py: commit the content, run the script, commit the
stamp alone, so the stamp points at the content commit a reader is looking at
rather than at the commit that only carries the stamp.

The practical consequence, which is the point: a content commit is not
publishable on its own. Run `python -m pipeline.build_build_info` and commit
the stamp before pushing, and push both together.

The one other unstamped state is the lock commit itself. LOCKDAY rule 4 puts
the stamp *after* the `lock-*` tag so the tag stays on the commit that adds
the lock file, which means the suite runs on that commit - on the tag ref,
and on main for the push that carried it - with build_info.json naming the
content commit before it (HEAD~2, stamped by HEAD~1). On 16 September 2026
that reported a failure that was not one. A commit that adds a
data/predictions/lock-*.json file is recognised here and held to that shape
instead.

See DECISIONS.md, 2026-08-10 and 2026-09-17.
"""
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BUILD_INFO = ROOT / "data" / "build_info.json"

# A stamp commit may touch these and nothing else.
STAMP_ONLY_FILES = {"data/build_info.json", "index.html", "methodology.html"}


def git(*args: str) -> str | None:
    """Stripped stdout, or None if the command fails (no git, shallow clone)."""
    try:
        result = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return result.stdout.strip()


def _adds_a_lock_file() -> bool:
    """True when HEAD adds a data/predictions/lock-*.json - the lock commit."""
    added = (git("diff", "--name-only", "--diff-filter=A", "HEAD~1", "HEAD") or "").split()
    return any(
        f.startswith("data/predictions/lock-") and f.endswith(".json") for f in added
    )


def test_build_info_names_head_or_is_one_stamp_commit_behind():
    head = git("rev-parse", "HEAD")
    if head is None:
        pytest.skip("not a git checkout - cannot verify the build_info stamp")

    named = json.loads(BUILD_INFO.read_text())["last_commit_sha"]
    if named == head:
        return  # the normal, fully-stamped state

    parent = git("rev-parse", "HEAD~1")
    if parent is None:
        pytest.skip(
            "git history too shallow to check the stamp-commit allowance "
            "(CI needs actions/checkout with fetch-depth: 0)"
        )

    if _adds_a_lock_file():
        # The lock commit: unstamped by design (LOCKDAY rule 4), so the tag
        # sits on it. build_info must then name the content commit before
        # it, with HEAD~1 the stamp for that commit.
        grandparent = git("rev-parse", "HEAD~2")
        assert named == grandparent, (
            f"HEAD adds a lock file, so it is the unstamped lock commit; "
            f"data/build_info.json should name HEAD~2 ({(grandparent or '?')[:7]}) "
            f"but names {named[:7]}. The stamp before the lock was skipped - "
            f"see LOCKDAY rule 4."
        )
        changed = set((git("diff", "--name-only", "HEAD~2", "HEAD~1") or "").split())
        extra = changed - STAMP_ONLY_FILES
        assert not extra, (
            f"HEAD is the lock commit, but HEAD~1 is not a stamp-only commit: "
            f"it also changes {sorted(extra)}. The records before a lock need "
            f"their own stamp commit, then the lock."
        )
        return

    assert named == parent, (
        f"data/build_info.json names {named[:7]}, which is neither HEAD ({head[:7]}) "
        f"nor its parent ({parent[:7]}). The footer will claim the site was last "
        f"updated at the wrong commit. Fix: python -m pipeline.build_build_info, "
        f"then commit data/build_info.json and the two rewritten stamps."
    )

    changed = set((git("diff", "--name-only", "HEAD~1", "HEAD") or "").split())
    extra = changed - STAMP_ONLY_FILES
    assert not extra, (
        f"data/build_info.json names HEAD's parent, which is only allowed when HEAD "
        f"is a stamp-only commit, but HEAD also changes: {sorted(extra)}. "
        f"Re-run python -m pipeline.build_build_info and commit the stamp."
    )


def test_build_info_stamp_fields_agree_with_the_named_commit():
    """The short sha, date and subject must actually belong to that commit -
    a stamp assembled from mismatched parts would pass the test above."""
    head = git("rev-parse", "HEAD")
    if head is None:
        pytest.skip("not a git checkout")

    info = json.loads(BUILD_INFO.read_text())
    sha = info["last_commit_sha"]

    assert sha.startswith(info["last_commit_short_sha"]), (
        f"short sha {info['last_commit_short_sha']} is not a prefix of {sha}"
    )
    for field, fmt in (("last_commit_iso", "%cI"), ("last_commit_subject", "%s")):
        actual = git("log", "-1", f"--format={fmt}", sha)
        if actual is None:
            pytest.skip(f"commit {sha[:7]} not in this checkout")
        assert info[field] == actual, (
            f"build_info.json {field} is {info[field]!r} but commit {sha[:7]} "
            f"has {actual!r}"
        )
