# LOCKDAY — the beta lock for the 30 July 2026 MPC announcement

> **Read after the fact (2 September 2026).** This runbook was written before
> the July lock and is kept as written. Three things changed on the day and
> since:
>
> - The lock did **not** happen at 12:00. `lock-2026-07.json` carries
>   `lock_timestamp: 2026-07-28T19:08:36+00:00`, and the `lock-2026-07` tag is
>   dated 20:19:45 BST the same evening. Every surface now reads the timestamp
>   from the lock file; the 12:00 below was the plan, not the record.
> - Step 6 (editing `PREDICTION_FILE` in `index.html`) no longer exists. The
>   site displays the newest `data/predictions/lock-*.json` automatically:
>   after writing a lock file, run `.venv/bin/python -m pipeline.build_fallbacks`
>   (then `build_track_record` and `build_build_info` as before). The line
>   numbers quoted below are stale.
> - The September runbook is a separate document, to be written with the
>   pre-registration before the 15 September lock.


Two dated sections. **Tuesday 28 July, 12:00** is the lock. **Thursday 30 July,
just after 12:00** is the outcome. Everything below is typed by Jake, by hand,
from the repo root:

```
cd "/Users/jakefoulkes/Desktop/CB Project/mpc-index"
```

Rules that apply to both days:

- Run every Python command with `.venv/bin/python`, not `python3` — the system
  Python has none of this project's packages installed.
- If any step hard-stops or a test fails, **stop there**. Nothing on this page is
  worth forcing past a red check. There is no `--force` and no bypass flag for
  the freshness guard, by design.
- `point_call` and `rationale` are yours and only yours. No script writes them.

---

## Read this before you start — four things this runbook corrects

1. **There is no `--name` flag.** `lock.py` takes two positional arguments:
   the meeting date, then the output name. The correct command is
   `.venv/bin/python -m pipeline.predict.lock 2026-07-30 lock-2026-07`. Typing
   `--name lock-2026-07` would be read as the meeting date and fail on the spot.
2. **The site card will not flip to locked styling on its own.** `index.html`
   line 465 hardcodes `PREDICTION_FILE = 'data/predictions/dryrun-2026-07.json'`,
   whose `point_call` is null and always will be. Until you point that constant
   at the lock file (step 6 below), the card stays "DRY RUN · NOT A FORECAST"
   no matter what you lock. This was flagged as a manual step in DECISIONS.md
   on 2026-07-11 ("A later real lock will need... updating the fetch path in
   index.html") and this is that later lock.
3. **Thursday's `score_outcomes` step rewrites `lock-2026-07.json`.** CLAUDE.md
   says `lock-*` files are never modified once written. The narrow, intended
   exception is the two fields the schema leaves null for exactly this purpose:
   `outcome` and `scores`. Nothing else in that file may change, ever — not the
   probabilities, not the point call, not the rationale, not the hashes. The
   `lock-2026-07` git tag pushed on Tuesday is what proves the call as it stood
   before the announcement, which is why the tag goes up on Tuesday and not
   after.

4. **Never push a content commit on its own — it will fail CI.**
   `data/build_info.json` says which commit the site was built from, and
   `pipeline/tests/test_build_info_fresh.py` fails if it names anything but
   HEAD (or the commit right before a stamp-only commit). Every commit that
   changes content needs a stamp commit behind it:
   `python -m pipeline.build_build_info`, commit `data/build_info.json` plus
   the two rewritten HTML footers, then push both together. On Tuesday this
   goes **after** the tag (step 11b) so the tag stays on the lock commit; on
   Thursday it is part of step 6.

---

## Tuesday 28 July 2026, 12:00 — the lock

### 1. Get the latest repo state

Makes sure you are locking from the same code that is on GitHub:

```bash
git pull
```

### 2. Run the full test suite

107 tests. If the count differs or anything fails, stop and do not lock:

```bash
.venv/bin/python -m pytest -q
```

### 3. Write the lock file

Freezes the market reference and the index readings into
`data/predictions/lock-2026-07.json`. It fetches the live OIS curve and SONIA,
and refuses to write if the curve is more than 2 business days old:

```bash
.venv/bin/python -m pipeline.predict.lock 2026-07-30 lock-2026-07
```

Expect it to print `wrote .../data/predictions/lock-2026-07.json` followed by the
full JSON. In that output, check by eye:

- `"meeting_announcement": "2026-07-30"`
- `"curve_as_of"` is 2026-07-27 or 2026-07-28 (a `HARD STOP` message instead
  means the curve went stale — stop, do not lock, investigate)
- `"point_call": null` and `"rationale": "TODO(Jake) - written by me before lock"`
- `"lock_timestamp"` is in **UTC**, so at 12:00 BST it reads `11:00`. That is
  correct, not a bug.

### 4. Open the file and fill in your two fields

Opens it in TextEdit:

```bash
open -e data/predictions/lock-2026-07.json
```

Change **exactly two lines**, near the bottom, and nothing else:

- `"point_call": null` → one of `"hold"`, `"hike"`, or `"cut"`, in double quotes.
  For example: `"point_call": "hold",`
- `"rationale": "TODO(Jake) - written by me before lock"` → your own sentence or
  two, in your own words, in double quotes on one line. If your text contains a
  double quote, use a single quote instead — it keeps the JSON valid.

Do not touch `m0_market_only`, the hashes, `code_version`, `lock_timestamp`,
`outcome`, or `scores`. Save and close.

### 5. Syntax-check the file you just hand-edited

Prints the file back if the JSON is valid, and an error with a line number if a
comma or quote went missing:

```bash
.venv/bin/python -m json.tool data/predictions/lock-2026-07.json
```

### 6. Point the site's call card at the lock file

Open `index.html`, go to **line 465**, and change:

```
const PREDICTION_FILE = 'data/predictions/dryrun-2026-07.json';
```

to:

```
const PREDICTION_FILE = 'data/predictions/lock-2026-07.json';
```

That one-line edit is what makes the card read the locked call. Without it the
card keeps rendering the July dry run.

### 7. Rebuild the track-record table

Rescans `data/predictions/` and rewrites `data/track_record.json`, so the Track
record section gains a **Locked** row for 30 July alongside the dry-run and
rehearsal rows:

```bash
.venv/bin/python -m pipeline.build_track_record
```

### 8. Re-run the tests after your hand edits

Same 107 tests. This is the check that your JSON edit and the `index.html` edit
did not break the site contract:

```bash
.venv/bin/python -m pytest -q
```

### 9. Review exactly what you are about to commit

Should be three files: the new lock JSON, `index.html`, and
`data/track_record.json`:

```bash
git status --short && git diff
```

### 10. Commit

Stages everything and records the lock:

```bash
git add -A && git commit -m "Beta lock: 30 July 2026 MPC"
```

### 11. Tag the commit

An annotated tag, so the tag itself carries its own timestamp:

```bash
git tag -a lock-2026-07 -m "Beta lock: 30 July 2026 MPC"
```

### 11b. Stamp the build — do this now, before you push

**A content commit pushed on its own will fail CI.** `data/build_info.json`
records which commit the site was built from, and
`pipeline/tests/test_build_info_fresh.py` fails when it names anything other
than HEAD (or the commit immediately before a stamp-only commit). Every content
commit needs a stamp commit behind it, and the two get pushed together.

**Do this after the tag, never before it.** The tag must point at the lock
commit. If you stamp first, `git tag` lands on the stamp commit and the
timestamp evidence points at the wrong thing.

```bash
.venv/bin/python -m pipeline.build_build_info && git add data/build_info.json index.html methodology.html && git commit -m "Last-updated stamp for the 30 July lock"
```

### 12. Push the commit and the tag together

This pushes both commits — the lock and its stamp — plus the tag:

```bash
git push origin main --follow-tags
```

### 13. Two checks on GitHub, after the push

**Check A — the tag pre-dates the announcement.** Open
<https://github.com/jakefoulkes1/mpc-index/tags>, click `lock-2026-07`, and read
the timestamp. It must be Tuesday 28 July 2026, roughly two days before the
Thursday 30 July 12:00 announcement. This is the public evidence the call was
made in advance. To see the same thing locally:

```bash
git log -1 --format=%cI lock-2026-07
```

**Check B — the site card flipped.** Open
<https://jakefoulkes1.github.io/mpc-index/> and hard-refresh (**Cmd+Shift+R**).
GitHub Pages usually takes a minute or two to redeploy. The call card should now
show:

- a solid gold border, not the hatched dashed one
- the badge reading **LOCKED CALL**, not "DRY RUN · NOT A FORECAST"
- the heading reading `locked <your timestamp>` instead of "beta lock scheduled
  28 July 2026, 12:00"
- your point call and your rationale on the bottom line of the card
- in the Track record table, a **Locked** row for 30 July 2026, and the "First
  pre-registered call: 30 July 2026" note now gone

If the badge still says DRY RUN after a hard refresh, step 6 did not take —
check line 465 of the deployed `index.html`.

---

## Thursday 30 July 2026, just after 12:00 — the outcome

The MPC announces at 12:00. Wait for the actual decision on
<https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes> before
touching anything.

### 1. Get the latest repo state

```bash
git pull
```

### 2. Record the outcome and score the market reference

Replace `hold` with what the MPC actually did — one of `hold`, `hike`, or `cut`,
exactly. This fills in `outcome` and `scores` in the lock file (Brier and log
scores for the m0 market-only reference and for the always-hold baseline) and
changes nothing else:

```bash
.venv/bin/python -m pipeline.predict.score_outcomes data/predictions/lock-2026-07.json hold
```

It prints the scores it wrote. Sanity check: if the outcome was `hold`, m0's
Brier should be small; a large one means you typed the wrong outcome.

### 3. Confirm only `outcome` and `scores` changed

The diff must touch those two fields and nothing else — no probability,
hash, or rationale should appear as changed:

```bash
git diff data/predictions/lock-2026-07.json
```

### 4. Rebuild the track-record table

Picks up the outcome and Brier score for the site's Track record row:

```bash
.venv/bin/python -m pipeline.build_track_record
```

### 5. Syntax-check and re-run the tests

```bash
.venv/bin/python -m json.tool data/predictions/lock-2026-07.json > /dev/null && .venv/bin/python -m pytest -q
```

### 6. Commit, stamp, then push

**A content commit pushed on its own will fail CI.** `data/build_info.json`
records which commit the site was built from, and
`pipeline/tests/test_build_info_fresh.py` fails when it names anything other
than HEAD (or the commit immediately before a stamp-only commit). So: commit
the outcome, run the stamp, commit that, and push both together. Skipping the
stamp is also what made the site look stale for five days in early August —
the footer kept naming an old commit while Pages was serving the tip correctly.

```bash
git add -A && git commit -m "Outcome: 30 July 2026 MPC"
```

```bash
.venv/bin/python -m pipeline.build_build_info && git add data/build_info.json index.html methodology.html && git commit -m "Last-updated stamp for the 30 July outcome"
```

```bash
git push origin main
```

No new tag on Thursday. `lock-2026-07` must keep pointing at Tuesday's commit —
that is the whole point of it.

### 6b. If the site has not updated after ~5 minutes — the empty-commit fallback

Why this step exists: the 28 July lock commit pushed fine but **GitHub Pages
never built it** — no `pages build and deployment` run was created for that push
— so the locked call was not visible on the deployed site for about an hour,
while the live page still showed DRY RUN. The push itself was not at fault.

Check whether Pages actually built your push:

```bash
gh run list --limit 5
```

If there is a `tests` run for "Outcome: 30 July 2026 MPC" but **no**
`pages build and deployment` run alongside it, push an empty commit to
re-trigger the build. It changes no files:

```bash
git commit --allow-empty -m "Trigger Pages rebuild" && git push origin main
```

Then re-check `gh run list --limit 5` for a `pages build and deployment` entry,
and give it a minute or two before hard-refreshing the site.

### 7. What to verify on the live site

Hard-refresh <https://jakefoulkes1.github.io/mpc-index/> (**Cmd+Shift+R**) and
check the **Track record** table's 30 July 2026 row:

- the badge still reads **Locked**
- **Call** is still your point call, unchanged from Tuesday
- **Outcome** now shows the actual decision instead of an em dash
- **Brier (m0)** now shows a number instead of an em dash
- the three probability columns are **identical to Tuesday's** — if any of them
  moved, something rewrote the locked file and that needs investigating before
  anything else

The call card itself does not display the outcome; it keeps showing the locked
call. That is expected.

Separately, and not part of this runbook: the July minutes will be published on
30 July, so the corpus rebuild and a new index reading are a later job.
