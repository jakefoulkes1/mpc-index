"""Regenerates every static fallback block in index.html from the JSON.

Site layer, additive: reads the data files the front-end fetches and rewrites
the `<!-- fallback:NAME -->` regions of index.html. Touches no schema and
nothing under data/predictions/ (the locked files are read only).

Nothing here is retyped: each block is built from the data file the front-end
would have fetched, using the same formatting rules index.html's own JS uses,
so the page a reader sees with a failed fetch carries the same figures as the
page a reader sees with a working one.

Run it after any rebuild of ladder_v1.json, inference_v1.json,
track_record.json or a prediction file - pipeline/tests/test_static_fallback.py
fails until you do.

Run:  python -m pipeline.build_fallbacks
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_URL = "https://github.com/jakefoulkes1/mpc-index"
PREDICTION_FILE = "data/predictions/lock-2026-07.json"

BADGE_LABEL = {"locked": "Locked", "dryrun": "Dry run", "rehearsal": "Rehearsal", "other": "Other"}


def load(rel: str):
    return json.loads((ROOT / rel).read_text())


def gb_date(iso: str) -> str:
    """The site's fmtDate: en-GB day, full month, year."""
    d = datetime.fromisoformat(iso[:10])
    return f"{d.day} {d.strftime('%B')} {d.year}"


def pct(v: float) -> str:
    return f"{v * 100:.0f}%"


def replace_region(html: str, name: str, body: str) -> str:
    pattern = re.compile(
        rf"(<!--\s*fallback:{name}\b.*?-->)(.*?)(<!--\s*/fallback:{name}\s*-->)",
        re.S,
    )
    new, n = pattern.subn(lambda m: m.group(1) + body + m.group(3), html)
    if n != 1:
        raise SystemExit(f"fallback:{name} matched {n} times in index.html, expected 1")
    return new


def build_ladder(html: str) -> str:
    d = load("data/ladder_v1.json")
    scores = d["headline_scores_scheduled_only"]
    rows = []
    for model in ("L0", "L1", "L2", "L3", "L4"):
        s = scores[model]
        skill = "&mdash;" if s.get("skill_vs_l1") is None else f"{s['skill_vs_l1']:.4f}"
        cls = ' class="model-l1"' if model == "L1" else ""
        rows.append(
            f"            <tr{cls}><td>{model}</td><td>{s['mean_brier']}</td>"
            f"<td>{s['mean_log_score']}</td><td>{skill}</td><td>{s['n']}</td></tr>"
        )
    body = '\n          <tbody id="ladder-tbody">\n' + "\n".join(rows) + "\n          </tbody>\n        "
    html = replace_region(html, "ladder", body)

    # The n / specials / clip line under the "More detail" expander, which
    # renderLadder() also overwrites and which silently carried n=60 through
    # the July ingest until a test caught it.
    meta = (
        f'\n          <p class="fine" id="ladder-meta" style="margin-top:0">Scheduled meetings '
        f'only, evaluated {gb_date(d["eval_start"])} &rarr; present (<strong>n={d["n_scheduled"]}'
        f'</strong>) &middot; {d["n_specials"]} special meeting(s) reported separately, not '
        f'blended in &middot; log-score probability floor {d["log_score_probability_clip"]}.</p>\n'
        f'          '
    )
    return replace_region(html, "laddermeta", meta)


def build_spec3(html: str) -> str:
    d = load("data/inference_v1.json")
    full = d["full_sample"]["spec3_surprise_on_lagged_index"]
    li = full["coefficients"]["lagged_index"]
    frag = d["fragility_check_subsample"]
    frag_li = frag["results"]["spec3_surprise_on_lagged_index"]["coefficients"]["lagged_index"]
    lr = d["full_sample"]["spec2_ordered_logit_lr_test"]
    line = (
        f"Regressing each meeting's market surprise on the <em>previous</em> meeting's index "
        f"(OLS, Newey&ndash;West standard errors, {full['newey_west_maxlags']} lags, n={full['n']} "
        f"scheduled meetings): coefficient <strong>{li['coef']}</strong>, t = {li['t']}, "
        f"<strong>p = {li['p']}</strong>. On the post-hiking-cycle subsample "
        f"(from {gb_date(frag['start_date'])}, n={frag['results']['n']}) the result does not "
        f"replicate: coefficient {frag_li['coef']}, p = {frag_li['p']}. Spec 2, an ordered-logit "
        f"likelihood-ratio test on the discrete decision, finds nothing: "
        f"LR = {lr['lr_statistic']}, p = {lr['p_value']}. "
        f"Full output: <code>data/inference_v1.json</code>."
    )
    return replace_region(
        html, "spec3",
        f'\n          <p id="spec3-line" class="prose" style="margin:0">{line}</p>\n        ',
    )


def build_track(html: str) -> str:
    """Locked rows only.

    The show-rehearsals toggle is JavaScript; with scripting off it cannot
    hide anything, so shipping rehearsal rows statically would contradict the
    default-off promise the toggle makes.
    """
    d = load("data/track_record.json")
    rows = []
    for r in d["records"]:
        if r["kind"] != "locked":
            continue
        m0 = r["m0_market_only"]
        brier = "&mdash;" if r["brier_m0"] is None else f"{r['brier_m0']:.4f}"
        rows.append(
            f'            <tr class="kind-{r["kind"]}">'
            f'<td>{gb_date(r["meeting_announcement"])}</td>'
            f'<td><span class="track-badge {r["kind"]}">{BADGE_LABEL[r["kind"]]}</span></td>'
            f'<td>{r["point_call"] or "&mdash;"}</td>'
            f'<td>{pct(m0["p_cut"])}</td><td>{pct(m0["p_hold"])}</td><td>{pct(m0["p_hike"])}</td>'
            f'<td>{r["outcome"] or "&mdash;"}</td><td>{brier}</td></tr>'
        )
    body = '\n          <tbody id="track-tbody">\n' + "\n".join(rows) + "\n          </tbody>\n        "
    return replace_region(html, "track", body)


def build_call(html: str) -> str:
    lock = load(PREDICTION_FILE)
    ctx = load("data/site_context.json")
    m0 = lock["m0_market_only"]
    probs = [("cut", m0["p_cut"]), ("hold", m0["p_hold"]), ("hike", m0["p_hike"])]
    lead = max(probs, key=lambda kv: kv[1])[0]
    tag = Path(PREDICTION_FILE).stem
    tag_url = f"{REPO_URL}/releases/tag/{tag}"

    scored = lock["outcome"] is not None and lock["scores"] is not None
    brier = lock["scores"]["m0_market_only"]["brier_score"]
    hit = lock["point_call"] == lock["outcome"]

    # Next announcement: the first meeting in the Bank's published calendar
    # after this call's own. Read from site_context.json, never typed in.
    later = sorted(
        m["meeting_date"] for m in ctx["ois_path"]["meetings"]
        if m["meeting_date"] > lock["meeting_announcement"]
    )
    if not later:
        raise SystemExit(
            "no meeting after the locked call in data/site_context.json - "
            "rebuild it (python -m pipeline.site_context) before stating a next announcement"
        )
    next_meeting = later[0]

    stamp_iso = lock["lock_timestamp"]
    utc = datetime.fromisoformat(stamp_iso).astimezone(timezone.utc)
    # Matches fmtUTCStamp() in index.html: site date format, to the second, UTC.
    stamp_utc = f"{utc.day} {utc.strftime('%B')} {utc.year}, {utc.strftime('%H:%M:%S')} UTC"

    rationale = (
        lock["rationale"]
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace("—", "&mdash;")
        .replace("−", "&minus;")
    )
    prob_divs = "".join(
        f'<div class="call-prob{" is-lead" if k == lead else ""}">'
        f'<span class="n">{v * 100:.0f}%</span><span class="l">{k}</span></div>'
        for k, v in probs
    )
    bar_segs = "".join(
        f'<span class="seg-{k}" style="width:{v * 100:.1f}%"></span>' for k, v in probs
    )
    vs = abs(lock["index_current"] - lock["index_trailing_mean"])
    word = "above" if lock["index_current"] > lock["index_trailing_mean"] else "below"

    body = f'''
  <section class="card call-card locked" id="call-card" aria-labelledby="call-badge">
    <div class="call-badge locked" id="call-badge">LOCKED CALL{" &middot; SCORED" if scored else ""}</div>
    <p class="call-heading" id="call-heading">Call for <strong>{gb_date(lock["meeting_announcement"])}</strong></p>
    <p class="call-stamp" id="call-stamp"><span class="stamp-label">Locked</span><time
      datetime="{stamp_iso}">{stamp_utc}</time> <span
      aria-hidden="true">&middot;</span> <a
      href="{tag_url}" rel="noopener">tag {tag}</a></p>

    <p class="call-verify" id="call-verify">
      <span class="vh">How to check this timestamp yourself</span>
      The call above was tagged and pushed to GitHub before the announcement it is about:
      open the <a href="{tag_url}"
      rel="noopener">tag page</a>, which GitHub dates independently of anything in this repository,
      or clone the repository and run
      <code>git show {tag}:{PREDICTION_FILE}</code> to read the call exactly
      as it stood when it was locked.
    </p>

    <div class="call-probs" id="call-probs">{prob_divs}</div>
    <div class="call-probbar" id="call-probbar" aria-hidden="true">{bar_segs}</div>
    <p class="call-probsrc" id="call-probsrc">m0 market-only reference &mdash; OIS forward curve vs SONIA, {m0["assumed_move_bp"]}bp two-state assumption. Not the point call.</p>
    <p class="fine call-index-line" id="call-index-line">A&amp;BG index ({lock["index_current_doc_id"]}): <strong>{lock["index_current"]:.3f}</strong> vs trailing {lock["index_trailing_n"]}-document mean <strong>{lock["index_trailing_mean"]:.3f}</strong> ({vs:.3f} {word})</p>
    <div class="call-rationale" id="call-rationale">
      <p class="call-rationale-h" id="call-rationale-h">Point call <span class="pt-call">{lock["point_call"]}</span></p>
      <p class="call-rationale-body" id="call-rationale-body">{rationale}</p>
      <p class="call-rationale-attrib" id="call-rationale-attrib">Written by hand before the announcement, and never edited afterwards.</p>
    </div>
    <p class="fine" id="call-fine" style="display:none"></p>

    <!-- Once the announcement has happened and score_outcomes has run, the
         card stops being a forward-looking notice and becomes a result. Both
         figures come from the locked file's own outcome/scores fields. -->
    <div class="call-outcome" id="call-outcome">
      <div class="call-outcome-row"><span class="oc-item"><span class="oc-l">Outcome</span><span class="oc-v">{lock["outcome"]}</span></span><span class="oc-item"><span class="oc-l">Brier (m0)</span><span class="oc-v">{brier:.4f}</span></span><span class="oc-item"><span class="oc-l">Point call</span><span class="oc-v{" oc-hit" if hit else ""}">{"matched" if hit else "missed"}</span></span></div>
      <p class="oc-note" id="call-outcome-note">Scored after the announcement by
      <code>pipeline/predict/score_outcomes.py</code>, which fills the outcome and scores fields
      and nothing else.</p>
    </div>

    <p class="call-next" id="call-next">Next announcement:
      <strong>{gb_date(next_meeting)}</strong> &mdash; the next call locks before it.</p>
  </section>
  '''
    return replace_region(html, "call", body)


def main() -> None:
    path = ROOT / "index.html"
    html = path.read_text()
    for fn in (build_ladder, build_spec3, build_track, build_call):
        html = fn(html)
    path.write_text(html)
    print("regenerated index.html fallbacks: ladder, spec3, track, call")


if __name__ == "__main__":
    main()
