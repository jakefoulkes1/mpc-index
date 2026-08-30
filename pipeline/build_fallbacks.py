"""Regenerates every static fallback block, and every inline figure, in
index.html and methodology.html from the JSON.

Site layer, additive: reads the data files the front-end fetches and rewrites
two kinds of marked region.

  <!-- fallback:NAME -->...<!-- /fallback:NAME -->   a whole block of markup
  <!-- fig:NAME -->...<!-- /fig:NAME -->             one figure inside prose

The block regions are what a reader sees if the fetch fails or JavaScript
never runs; the JS overwrites them on success. The figure regions are prose
that JavaScript never touches - the sentence is the author's, the number in
it is the data's. Both pages are covered; methodology.html runs no JavaScript
at all, so every number on it is a figure region or nothing.

Nothing here is retyped. Block regions are built from the data file the
front-end would have fetched, using the same formatting rules index.html's
own JS uses; figure regions come from pipeline/site_figures.py, which is also
what the tests read. pipeline/tests/test_static_fallback.py and
pipeline/tests/test_site_figures.py fail until this has been re-run.

Run it after any rebuild of index.json, ladder_v1.json, inference_v1.json,
site_context.json, annotations.json, track_record.json or a prediction file.

Run:  python -m pipeline.build_fallbacks
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from pipeline.site_figures import figures, gb_date

ROOT = Path(__file__).resolve().parents[1]
REPO_URL = "https://github.com/jakefoulkes1/mpc-index"
PREDICTION_FILE = "data/predictions/lock-2026-07.json"

BADGE_LABEL = {"locked": "Locked", "dryrun": "Dry run", "rehearsal": "Rehearsal", "other": "Other"}

# One-line glosses for the ladder's five forecasters and for the call card's
# market-only reference. Labels, not data: they name what each model is
# allowed to see. Mirrored in index.html's renderLadder()/renderCallCard().
MODEL_GLOSS = {
    "L0": "always-hold",
    "L1": "market pricing",
    "L2": "market modelled",
    "L3": "market + tone + skew",
    "L4": "member simulation",
}
M0_GLOSS = "market pricing only"


def load(rel: str):
    return json.loads((ROOT / rel).read_text())


def pct(v: float) -> str:
    return f"{v * 100:.0f}%"


def replace_region(html: str, name: str, body: str, kind: str = "fallback", where: str = "index.html") -> str:
    pattern = re.compile(
        rf"(<!--\s*{kind}:{name}\b.*?-->)(.*?)(<!--\s*/{kind}:{name}\s*-->)",
        re.S,
    )
    new, n = pattern.subn(lambda m: m.group(1) + body + m.group(3), html)
    if n != 1:
        raise SystemExit(f"{kind}:{name} matched {n} times in {where}, expected 1")
    return new


# ------------------------------------------------------------- figures


def write_figures(html: str, where: str) -> str:
    """Fill every <!-- fig:NAME --> region on the page from the catalogue."""
    catalogue = figures()
    used: set[str] = set()

    def repl(m: re.Match) -> str:
        name = m.group("name")
        if name not in catalogue:
            raise SystemExit(
                f"{where} references fig:{name}, which pipeline/site_figures.py does not "
                f"define - add it there rather than typing a number into the page"
            )
        used.add(name)
        return m.group("open") + catalogue[name] + m.group("close")

    pattern = re.compile(
        r"(?P<open><!--\s*fig:(?P<name>[a-z0-9_]+)\s*-->)"
        r"(?P<body>.*?)"
        r"(?P<close><!--\s*/fig:(?P=name)\s*-->)",
        re.S,
    )
    html = pattern.sub(repl, html)
    if used:
        print(f"  {where}: {len(used)} distinct figures written")
    return html


# -------------------------------------------------------------- ladder


def build_ladder(html: str) -> str:
    d = load("data/ladder_v1.json")
    scores = d["headline_scores_scheduled_only"]
    rows = []
    for model in ("L0", "L1", "L2", "L3", "L4"):
        s = scores[model]
        skill = "&mdash;" if s.get("skill_vs_l1") is None else f"{s['skill_vs_l1']:.4f}"
        cls = ' class="model-l1"' if model == "L1" else ""
        rows.append(
            f"            <tr{cls}><td><strong>{model}</strong>"
            f'<span class="model-gloss">{MODEL_GLOSS[model]}</span></td>'
            f"<td>{s['mean_brier']}</td>"
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


# -------------------------------------------------------------- spec 3


def build_spec3(html: str) -> str:
    """Rounded for reading, with the full precision one link away.

    Six decimal places on a coefficient whose p-value is 0.03 asserts a
    precision the estimate does not have; the JSON keeps every digit and the
    sentence names the file.
    """
    f = figures()
    line = (
        f"Regressing each meeting's market surprise on the <em>previous</em> meeting's index "
        f"(OLS, Newey&ndash;West standard errors, {f['nw_lags']} lags, n={f['spec3_n']} "
        f"scheduled meetings): coefficient <strong>{f['spec3_coef']}</strong> "
        f"(t = {f['spec3_t']}, <strong>p = {f['spec3_p']}</strong>). On the post-hiking-cycle "
        f"subsample (from {f['frag_start']}, n={f['frag_n']}) the result does not "
        f"replicate: coefficient {f['frag_coef']} (t = {f['frag_t']}, p = {f['frag_p']}). "
        f"Spec 2, an ordered-logit likelihood-ratio test on the discrete decision, finds "
        f"nothing: LR = {f['spec2_lr']}, p = {f['spec2_p']}. "
        f"Coefficients and t-statistics are rounded to 2 decimal places and p-values to 4; "
        f"full precision is in <code>data/inference_v1.json</code>."
    )
    return replace_region(
        html, "spec3",
        f'\n          <p id="spec3-line" class="prose" style="margin:0">{line}</p>\n        ',
    )


# -------------------------------------------------------- track record


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


# ---------------------------------------------------- verification box


def build_verify(html: str) -> str:
    """The tag, the git command and the repository, in one place.

    These three used to be spread across the call card and the footer nav.
    Generated from the prediction file actually on display, so it can never
    invite a reader to check a tag that does not exist.
    """
    tag = Path(PREDICTION_FILE).stem
    tag_url = f"{REPO_URL}/releases/tag/{tag}"
    body = f'''
  <section class="card" id="how-to-check">
    <h2>How to check this</h2>
    <p class="plain-summary">Nothing here has to be taken on trust. The call below was tagged
    and pushed to GitHub before the announcement it is about, and everything behind it is in
    the open.</p>
    <ol class="verify-list">
      <li><strong>The timestamp.</strong> Open the
      <a href="{tag_url}" rel="noopener">tag <code>{tag}</code></a>, which GitHub dates
      independently of anything in this repository.</li>
      <li><strong>The call itself.</strong> Clone the repository and run
      <code>git show {tag}:{PREDICTION_FILE}</code> to read the call exactly as it stood
      when it was locked.</li>
      <li><strong>Everything else.</strong> The code, the data, and the dated log of every
      methodological choice are in
      <a href="{REPO_URL}" rel="noopener">the repository</a>.</li>
    </ol>
  </section>
  '''
    return replace_region(html, "verify", body)


# ----------------------------------------------------------- call card


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
    lock_day = gb_date(stamp_iso)

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
    <!-- Every number in this card is the locked file's own, and the locked
         file is never edited. Where a figure elsewhere on the site has since
         been recomputed on a larger corpus, the two will differ; this line
         says which one a reader is looking at. -->
    <p class="call-asat" id="call-asat">Figures as at the lock date ({lock_day}).</p>

    <!-- 10. The same "In plain English" device the Results section uses. -->
    <!-- DRAFT: JF to revise -->
    <p class="plain-summary" id="call-plain"><em>In plain English: this is the call itself
    &mdash; written down and timestamped before the announcement, so it cannot be quietly
    revised afterwards. The percentages beneath are the market's, not mine; the point call
    and the reasoning are mine.</em></p>

    <div class="call-probs" id="call-probs">{prob_divs}</div>
    <div class="call-probbar" id="call-probbar" aria-hidden="true">{bar_segs}</div>
    <p class="call-probsrc" id="call-probsrc"><strong>m0</strong> <span class="prob-gloss">{M0_GLOSS}</span> &mdash; OIS forward curve vs SONIA, {m0["assumed_move_bp"]:g}bp two-state assumption. Not the point call.</p>
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


# ------------------------------------------------- latest reading / chart


def build_latest(html: str) -> str:
    """renderLatest()'s output, generated - the reading, not "Loading..."."""
    data = load("data/index.json")
    doc = data["documents"][-1]
    neutral = data["neutral_value"]
    net = doc["abg_net_index"] - neutral
    cls = "sign-hawk" if net > 0 else ("sign-dove" if net < 0 else "")
    word = "net hawkish" if net > 0 else ("net dovish" if net < 0 else "neutral")
    body = f'''
    <div class="reading" id="content">
      <p class="docline" id="docline">MPC minutes, meeting ending <strong>{gb_date(doc["meeting_end"])}</strong> &middot; published {gb_date(doc["published"])} &middot; decision: {doc["decision"]} &middot; vote {doc["vote"]}</p>
      <p class="score" id="score"><span class="{cls}">{doc["abg_net_index"]:.3f}</span> <span class="score-word">{word} (A&amp;BG Net Index, 0&ndash;2 scale, {neutral} = neutral)</span></p>
      <div class="scale"><div class="marker" id="marker" style="left:{50 + net * 50:.4f}%"></div></div>
      <div class="scale-labels"><span>&larr; dovish</span><span>neutral</span><span>hawkish &rarr;</span></div>
      <p class="fine" id="detail">{doc["abg_hawk"]} hawkish vs {doc["abg_dove"]} dovish noun+adjective hits &middot; lexicon: {data["lexicon"]} &middot; sha256 <code>{doc["sha256"][:16]}&hellip;</code> &middot; <a href="{doc["source_url"]}">source document</a></p>
    </div>
    '''
    return replace_region(html, "latest", body)


def build_chart(html: str) -> str:
    """The chart in words.

    An SVG line chart cannot be drawn without JavaScript, so the honest
    static state is not an empty box: it is the same series described.
    """
    data = load("data/index.json")
    series = data["series"]
    values = [p["abg_net_index"] for p in series]
    lo = min(series, key=lambda p: p["abg_net_index"])
    hi = max(series, key=lambda p: p["abg_net_index"])
    body = f'''
    <p class="fine" id="chart-fallback">The chart is drawn by JavaScript. In words:
    <strong>{len(series)}</strong> readings from {gb_date(series[0]["date"])} to
    {gb_date(series[-1]["date"])} on the A&amp;BG 0&ndash;2 scale, where {data["neutral_value"]}
    is neutral. Latest <strong>{values[-1]:.3f}</strong> ({series[-1]["doc_id"]}); series low
    {lo["abg_net_index"]:.3f} ({lo["doc_id"]}), high {hi["abg_net_index"]:.3f} ({hi["doc_id"]}).
    Every point is in <code>data/index.json</code>.</p>
    '''
    return replace_region(html, "chart", body)


# ------------------------------------------------------- context panel


def build_context(html: str) -> str:
    """renderContext()'s output, generated.

    The two sparklines are drawn by JavaScript and stay empty without it;
    the figures they illustrate are all here as text.
    """
    ctx = load("data/site_context.json")
    op = ctx["ois_path"]
    n = len(op["meetings"])
    rows = []
    for m in op["meetings"]:
        segs = ""
        for cls in ("cut", "hold", "hike"):
            v = m[f"p_{cls}"]
            label = f"{round(v * 100)}%" if round(v * 100) >= 12 else ""
            segs += f'<div class="ois-seg {cls}" style="width:{v * 100:.1f}%">{label}</div>'
        chg = f'{"+" if m["implied_change_bp"] >= 0 else ""}{m["implied_change_bp"]:.1f}bp'
        rows.append(
            f'<div class="ois-row"><div class="ois-date">{gb_date(m["meeting_date"])}</div>'
            f'<div class="ois-bar">{segs}</div><div class="ois-chg">{chg}</div></div>'
        )
    rate = ctx["bank_rate_history"]["points"][-1]
    g = ctx["gilt_2y"]
    body = f'''
      <div class="ctx-block">
        <h3 class="ctx-h" id="ois-h">OIS-implied path &middot; next {n} scheduled meeting{"" if n == 1 else "s"}</h3>
        <p class="ctx-sub" id="ois-sub">Curve as of <b style="color:var(--text)">{gb_date(op["curve_as_of"])}</b> vs SONIA {op["sonia_pct"]:.3f}% ({gb_date(op["sonia_as_of"])}) &middot; two-state &plusmn;{op["assumed_move_bp"]:g}bp assumption.</p>
        <div class="ois-legend">
          <span class="key"><span class="box cut"></span> cut</span>
          <span class="key"><span class="box hold"></span> hold</span>
          <span class="key"><span class="box hike"></span> hike</span>
          <span class="key" style="color:var(--faint)">bars = market-implied probability &middot; right = implied move</span>
        </div>
        <div id="ois-rows">{"".join(rows)}</div>
        <p class="ctx-footnote">Forward-implied probabilities reflect risk premia as well as
        expectations &mdash; <a href="methodology.html#limitations">see Limitations</a>.</p>
      </div>

      <div class="ctx-grid">
        <div class="ctx-block ctx-figure">
          <h3 class="ctx-h">Bank Rate</h3>
          <p class="big" id="rate-latest">{rate["rate_pct"]:.2f}<span class="unit">%</span></p>
          <p class="asof" id="rate-asof">latest, {gb_date(rate["date"])}</p>
          <svg id="rate-chart" viewBox="0 0 320 110" role="img"
               aria-label="Bank Rate history as a step chart"></svg>
        </div>
        <div class="ctx-block ctx-figure">
          <h3 class="ctx-h" id="gilt-h">{g["label"]}</h3>
          <p class="big" id="gilt-latest">{g["latest_pct"]:.2f}<span class="unit">%</span></p>
          <p class="asof" id="gilt-asof">latest, {gb_date(g["as_of"])} &middot; {g["window_months"]}-month history</p>
          <svg id="gilt-chart" viewBox="0 0 320 110" role="img"
               aria-label="Twelve-month history of the 2-year nominal gilt yield"></svg>
        </div>
      </div>

      <p class="ctx-note" id="context-note">{ctx["disclaimer"]} Sources: Bank of England OIS forward curve &amp; SONIA; GLC nominal gilt curve; Bank Rate from the voting record.</p>
'''
    return replace_region(html, "context", body)


# ------------------------------------------------------------ episodes


def render_markdown(md: str) -> str:
    """The same small Markdown subset renderMarkdown() implements in index.html.

    Kept deliberately literal so the two agree: escape, then bold, italic and
    links; blocks split on blank lines; an all-dash block is a list; a lone
    ##/###/#### line is a heading one level down.
    """
    def inline(s: str) -> str:
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
        s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2" rel="noopener">\1</a>', s)
        return s

    out = []
    for block in re.split(r"\n{2,}", md):
        lines = block.split("\n")
        if lines and all(re.match(r"^\s*-\s+", line) for line in lines):
            items = "".join(f"<li>{inline(re.sub(r'^\s*-\s+', '', line))}</li>" for line in lines)
            out.append(f"<ul>{items}</ul>")
            continue
        h = re.match(r"^(#{2,4})\s+(.*)$", block)
        if h and len(lines) == 1:
            level = len(h.group(1)) + 1
            out.append(f"<h{level}>{inline(h.group(2))}</h{level}>")
            continue
        out.append(f"<p>{inline(block.replace(chr(10), ' '))}</p>")
    return "".join(out)


def build_episodes(html: str) -> str:
    d = load("data/annotations.json")
    articles = []
    for ep in d["episodes"]:
        articles.append(
            f'<article class="episode" id="episode-{ep["date"]}">'
            f'<h3>{ep["title"].replace("<", "&lt;")}</h3>'
            f'<p class="ep-date">{gb_date(ep["date"])}</p>'
            f'<div class="ep-body">{render_markdown(ep.get("body") or "")}</div>'
            f"</article>"
        )
    body = f'''
    <div id="episodes-list">
      {"".join(articles)}
    </div>
    '''
    return replace_region(html, "episodes", body)


def main() -> None:
    index_path = ROOT / "index.html"
    html = index_path.read_text()
    for fn in (
        build_verify, build_call, build_latest, build_chart, build_context,
        build_ladder, build_spec3, build_track, build_episodes,
    ):
        html = fn(html)
    html = write_figures(html, "index.html")
    index_path.write_text(html)

    meth_path = ROOT / "methodology.html"
    meth_path.write_text(write_figures(meth_path.read_text(), "methodology.html"))

    print(
        "regenerated index.html blocks: verify, call, latest, chart, context, "
        "ladder, spec3, track, episodes"
    )


if __name__ == "__main__":
    main()
