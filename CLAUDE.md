# Standing rules for this project

These apply to every session. Read them before starting work.

## Orientation
- **Read `DECISIONS.md` at the start of every session** before touching anything.
  It is the dated record of every methodological choice made so far.

## Methodology discipline
- **Every methodological choice gets a dated entry in `DECISIONS.md`**, written
  before (or alongside) the change. Changes apply **forward only** — nothing is
  retrofitted, and existing results are not silently altered.
- **Never fabricate or approximate data.** If a source won't parse, a value is
  missing, or something is ambiguous, **HARD STOP and ask** — do not guess, fill
  in, or estimate. A deliberate `null` with an explanation beats a made-up number.

## What must not change
- **Files under `data/predictions/lock-*` are never modified once written.** A
  locked call is permanent, including its misses.
- **The science layer is off-limits unless a prompt explicitly says to touch it.**
  That means `pipeline/score`, `pipeline/market`, `pipeline/predict`, and the
  lexicon (`pipeline/score/lexicon/`). Site and context work may *import* these
  modules read-only, but must not modify them or any existing data schema.

## Working style
- **The maintainer is a beginner.** Give **one plain-English line before each
  command** explaining what it does and why.
