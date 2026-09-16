# LOCKDAY 2026-09 — the September runbook

The author's instructions for the 16 September 2026 lock, saved verbatim from
the session that carried it out, before the lock commit. The decisions taken
during the session (rehearsal file renamed, fresh re-lock on the latest curve,
pre-registration of the vote-split distribution) are in DECISIONS.md
2026-09-16. Nothing below has been edited.

---

I'm locking my pre-registered call for the Bank of England MPC announcement on 17 September 2026 (12:00 BST). Repo: /Users/jakefoulkes/Desktop/CB Project/mpc-index. Read CLAUDE.md, LOCKDAY.md and the latest DECISIONS.md entries first and follow their rules: use .venv/bin/python for everything, stop at any failing check or test, no --force, never modify an existing lock-* file. point_call and rationale are mine: write them exactly as I give them, and don't rephrase anything.

Deadline: the tag must be pushed before 12:00 BST on 17 September. The lock must be timestamped after 07:00 BST on 16 September, because the rationale cites August CPI, published then.

STEP 1: Pre-flight (report, don't fix)
- git status and git pull. Tell me about any uncommitted or unpushed work, especially a September runbook or a pre-registration of the vote-split distribution. The July episode committed to pre-registering these before the September lock. If they exist only locally, they must be committed and pushed in their own commit BEFORE the lock commit. If they don't exist at all, stop and tell me.
- Run the test suite and confirm it is green.

STEP 2: Curve check (report, don't change code)
Run:
.venv/bin/python -c "
import datetime as dt
from pipeline.market.ois import latest_forward_curve, latest_sonia
from pipeline.predict.market_probs import months_between, market_probs_for_meeting
c = latest_forward_curve(); s = latest_sonia()
a = dt.date.fromisoformat(c['as_of_date'])
print('curve', a, '| sonia', s)
for m, r in list(zip(c['maturities_months'], c['forward_rates_pct']))[:4]:
    print(f'{m:>4} months -> {a + dt.timedelta(days=round(m*30.436875))}  {r}')
print('meeting+3 =', round(months_between(a, dt.date(2026,9,20)), 3), 'months')
print(market_probs_for_meeting(c, s, dt.date(2026,9,17)))
"
Report: the curve as-of date, SONIA, the first four maturity nodes with dates, whether meeting+3 falls below the first maturity (and so gets clipped to it), and m0's p_cut / p_hold / p_hike. My draft assumes m0 p_hike = 25.2%. If it differs, tell me.
THEN STOP and wait for me to give the final shaded p(hike) as [X]. Do not choose it yourself.

STEP 3: Records before the lock (one commit, pushed before the lock)
- Add a dated DECISIONS.md entry: the September lock moves from 15 to 16 September 2026 (announcement-minus-one), so the call can use the August CPI release published 07:00 BST on 16 September. This is a deviation from July's announcement-minus-two convention, recorded before the lock.
- Update every site surface that says "next lock 15 September 2026" to 16 September. Regenerate through the pipeline, not by hand-editing generated files.
- If the clipping in step 2 is confirmed, add a DECISIONS.md note that the meeting+3 read clips to the first maturity bucket when the curve is less than a month old, so the read is a forward about one month out, not at meeting+3. Record it as a finding only; don't change code before the lock.
- Build stamp per LOCKDAY rule 4, then commit and push.

STEP 4: The lock
.venv/bin/python -m pipeline.predict.lock 2026-09-17 lock-2026-09
Check that the output's index_current is 0.6667 (minutes-2026-07) and index_trailing_mean is 1.2202 (n = 4). If either differs, stop and tell me; the rationale quotes them.
Set point_call to "hold". Set rationale to the text below, with [M0] replaced by m0's p_hike as a percentage to one decimal and [X] by my number. Show me the complete file and WAIT for my "go" before continuing.

Rationale:
Hold at 3.75%. The communication index is recorded as context and does not enter the call: L3 scores −0.6712 against the market-only benchmark and Spec 2 returns p = 0.4894, so there remains no warrant on this project's own evidence for letting tone override L1. The index reads 0.667 against a trailing 4-document mean of 1.220 (0.553 below), dovish while the hawkish minority grew; this is what the July episode predicted of a lexicon keyed to realised inflation facing forward-risk reasoning. p(hike) is shaded below m0's [M0]%, to [X]%, on the first of July's two reasons only. A read at meeting plus three days falls inside the curve's first one-month bucket and is taken from it, a forward dated mid-October; the fitted spline smooths part of the move priced for 5 November back into that point, and with more now priced for November than was priced for September in July, the effect is larger than it was then. The second reason does not transfer: this repricing is energy-driven rather than a fiscal risk premium. The first remains testable against the November lock. The macro flow since 30 July moved the headline but not the measures the majority said it was waiting for. Headline CPI rose to 3.1% from 2.9% on goods and motor fuels, while core held at 2.6% and services at 3.4%; payrolls fell by an estimated 26,000, and vacancies are the lowest outside the pandemic since 2014. That is first-round energy pass-through of the kind the July majority said it would look through, with no sign yet of the second-round effects the Governor has named as his threshold. The vote split is called at 6–3, with Greene, Mann and Pill again in the minority: the minority has run 8–1, 7–2, 6–3, but 5–4 requires a central-bloc member to act on energy persistence alone. The counter-observation, recorded rather than passed over, is that regular pay growth held at 3.5% and private-sector regular pay was 2.9% rather than continuing to slow, while Brent traded near $108 on 15 September. If 17 September brings a hike or a fourth vote for one, the error is in the reading of the central bloc's threshold, not in the data.

If step 2 shows the clipping does NOT happen (meeting+3 is at or beyond the first maturity), tell me before step 4: the sentence beginning "A read at meeting plus three days" would then be wrong and I'll rewrite it.

STEP 5: After my "go"
.venv/bin/python -m pipeline.build_fallbacks
.venv/bin/python -m pipeline.build_track_record
git add -A && git commit -m "Lock call for 17 September 2026"
git tag lock-2026-09
git push && git push origin lock-2026-09
Then the build stamp commit (build_build_info), committed and pushed AFTER the tag, so the tag stays on the lock commit.

STEP 6: Verify and report
- git log -1 --format=%cI lock-2026-09 (must be after 2026-09-16T07:00+01:00)
- git show lock-2026-09:data/predictions/lock-2026-09.json (must match what I approved)
- Confirm CI passes and the live site shows the September call card as locked and the corrected lock date.
Give me a short summary: the tag timestamp, m0, my probabilities, and anything that deviated from this plan.
