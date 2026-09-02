"""Regenerates every static fallback block and every inline figure on every
published surface - index.html, methodology.html and README.md - from the
data files.

Site layer, additive: reads the data files the front-end fetches and rewrites
two kinds of marked region.

  <!-- fallback:NAME -->...<!-- /fallback:NAME -->   a whole block of markup
  <!-- fig:NAME -->...<!-- /fig:NAME -->             one figure inside prose

The block regions are what a reader sees if the fetch fails or JavaScript
never runs; the JS overwrites them on success. The figure regions are prose
that JavaScript never touches - the sentence is the author's, the number in
it is the data's. methodology.html runs no JavaScript at all, and README.md
is Markdown (which tolerates HTML comments), so on those two surfaces every
number is a region or it is not a figure.

Nothing here is retyped. Block regions are built from the data file the
front-end would have fetched, using the same formatting rules index.html's
own JS uses; figure regions come from pipeline/site_figures.py, which is also
what the tests read. pipeline/tests/test_static_fallback.py and
pipeline/tests/test_site_figures.py fail until this has been re-run.

Run it after any rebuild of index.json, ladder_v1.json, inference_v1.json,
site_context.json, annotations.json, track_record.json or a prediction file,
and after a new lock-* file is written: the prediction file on display is
the newest lock-*, derived here rather than edited into the page.

Run:  python -m pipeline.build_fallbacks
"""
import json
import re
from pathlib import Path

from pipeline.build_build_info import stamp_html, stamp_short
from pipeline.site_figures import (
    AUTHOR,
    figures,
    gb_date,
    gb_stamp_utc,
    index_value,
    lock_date_for,
    neutral,
    next_meeting_after,
    pct,
    plain,
    prediction_file,
    score,
)

ROOT = Path(__file__).resolve().parents[1]
REPO_URL = AUTHOR["repo"]
PREDICTION_FILE = prediction_file()

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

# The README's longer descriptions of the same five models. Author's labels.
MODEL_DESCRIPTION = {
    "L0": "always hold",
    "L1": "market-only (OIS-implied, two-state ±{move_bp}bp)",
    "L2": "ordered logit on the market-implied change",
    "L3": "L2 + lagged tone index + lagged vote skew",
    "L4": "member-level transition simulation, blended with market",
}

# The context panel's standing label. A sentence in the template rather than
# the JSON's own disclaimer string printed verbatim, so its punctuation is
# the site's (DECISIONS.md 2026-09-02, dash policy). Mirrored in
# renderContext().
CONTEXT_NOTE = (
    "Context, not model inputs. These series are shown for orientation only; "
    "none of them feed the A&amp;BG communication index, the market benchmark, "
    "or any locked call."
)


# Related work, rendered on index.html (Related work) and methodology.html
# (References) from this one list. Author-year-title-venue as supplied in the
# September 2026 brief; "verify" marks an entry whose details have not been
# checked against the source from this repository - nothing has been added
# from memory, and no volume, page or DOI is stated. The maintainer supplies
# the verified set. (DECISIONS.md 2026-09-02, Stage 2.)
RELATED_WORK = [
    {
        # Verbatim from pipeline/score/lexicon/abg_2012.json's `citation` field.
        "cite": 'Apel, Mikael and Marianna Blix Grimaldi (2012), "The Information Content of '
                'Central Bank Minutes", Sveriges Riksbank Working Paper Series No. 261, April 2012.',
        "note": "the dictionary this index implements verbatim, from a retrieved copy of the paper",
        "verify": False,
    },
    {
        "cite": "Gerlach-Kristen, P. (2004). On whether the MPC's voting record is informative "
                "about future UK monetary policy. Scandinavian Journal of Economics.",
        "note": "source of the vote-skew construction, cited by Apel and Blix Grimaldi (2012, p.13)",
        "verify": True,
    },
    {
        "cite": "Hansen, S. and McMahon, M. (2016). Shocking language. Journal of International "
                "Economics.",
        "note": "central bank communication treated as text and measured for its effects",
        "verify": True,
    },
    {
        "cite": "Bholat, D., Hansen, S., Santos, P. and Schonhardt-Bailey, C. (2015). Text Mining "
                "for Central Banks. Bank of England, CCBS Handbook No. 33.",
        "note": "the Bank's own handbook on text methods",
        "verify": True,
    },
    {
        "cite": "Lloyd, S. P. (2018). OIS-based measures of monetary policy expectations. Bank of "
                "England Staff Working Paper No. 709.",
        "note": "why OIS forwards carry premia as well as expectations, the risk-premia limitation",
        "verify": True,
    },
    {
        "cite": "Gneiting, T. and Raftery, A. E. (2007). Strictly proper scoring rules, prediction, "
                "and estimation. Journal of the American Statistical Association.",
        "note": "the Brier and log scores used to score every call are strictly proper",
        "verify": True,
    },
    {
        "cite": "Diebold, F. X. and Mariano, R. S. (1995). Comparing predictive accuracy. Journal of "
                "Business & Economic Statistics.",
        "note": "the test on the loss differential scheduled for the September cycle",
        "verify": True,
    },
]


def load(rel: str):
    return json.loads((ROOT / rel).read_text())


def related_work_html() -> str:
    items = []
    for r in RELATED_WORK:
        flag = ' <span class="verify" title="not yet checked against the source">[VERIFY]</span>' if r["verify"] else ""
        cite = r["cite"].replace("&", "&amp;")
        items.append(f'      <dt>{cite}{flag}</dt>\n      <dd>{r["note"]}</dd>')
    return '\n    <dl class="refs">\n' + "\n".join(items) + "\n    </dl>\n    "


def build_related_work(html: str, where: str) -> str:
    name = "relatedwork" if where == "index.html" else "references"
    return replace_region(html, name, related_work_html(), where=where)


def build_status(html: str, where: str) -> str:
    """The masthead status line: counts from the record and the corpus, the
    next lock from the calendar, and the build stamp from build_info.json.
    Replaces the "Beta" badge (DECISIONS.md 2026-09-02, Stage 2)."""
    f = figures()
    n = int(f["lock_count"])
    calls = f"{n} locked call{'' if n == 1 else 's'}"
    body = (
        f'{calls} <span class="sep" aria-hidden="true">&middot;</span> '
        f'next lock {f["next_lock_date"]} <span class="sep" aria-hidden="true">&middot;</span> '
        f'{f["corpus_n"]} documents'
    )
    html = replace_region(html, "status", body, where=where)
    info = load("data/build_info.json")
    html = replace_region(html, "buildstamp", stamp_short(info), where=where)
    return html


def replace_region(text: str, name: str, body: str, kind: str = "fallback", where: str = "index.html") -> str:
    pattern = re.compile(
        rf"(<!--\s*{kind}:{name}\b.*?-->)(.*?)(<!--\s*/{kind}:{name}\s*-->)",
        re.S,
    )
    new, n = pattern.subn(lambda m: m.group(1) + body + m.group(3), text)
    if n != 1:
        raise SystemExit(f"{kind}:{name} matched {n} times in {where}, expected 1")
    return new


# ------------------------------------------------------------- figures


def write_figures(text: str, where: str, catalogue: dict[str, str] | None = None) -> str:
    """Fill every <!-- fig:NAME --> region on the surface from the catalogue."""
    catalogue = catalogue if catalogue is not None else figures()
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
    text = pattern.sub(repl, text)
    if used:
        print(f"  {where}: {len(used)} distinct figures written")
    return text


# -------------------------------------------------- byline and metadata


def build_byline(html: str, where: str) -> str:
    """The footer byline, from the one AUTHOR record."""
    body = (
        f'\n    <p class="byline"><strong>{AUTHOR["name"]}</strong>, {AUTHOR["affiliation"]}<br>'
        f'<a href="mailto:{AUTHOR["email"]}">{AUTHOR["email"]}</a></p>\n    '
    )
    return replace_region(html, "byline", body, where=where)


def build_meta(html: str, where: str) -> str:
    """<meta> tags that carry a figure or the byline: generated whole, because
    a fig region cannot sit inside an attribute."""
    f = figures()
    html = replace_region(
        html, "metaauthor",
        f'\n<meta name="author" content="{AUTHOR["name"]}">\n',
        where=where,
    )
    alt = (
        f"The A&amp;BG communication index for Bank of England MPC minutes, "
        f"{f['corpus_start_month']} to {f['corpus_end_month']}, plotted against its neutral value."
    )
    return replace_region(
        html, "ogalt",
        f'\n<meta property="og:image:alt" content="{alt}">\n',
        where=where,
    )


def build_gen_note(html: str) -> str:
    """The footer's "index data generated" note - shipped filled in, so the
    separator before it never dangles. renderLatest() refreshes it."""
    f = figures()
    return replace_region(
        html, "gennote",
        f'<span id="gen-note">Index data generated {f["index_generated"]}.</span>',
    )


# -------------------------------------------------------------- ladder


def build_ladder(html: str) -> str:
    d = load("data/ladder_v1.json")
    f = figures()
    scores = d["headline_scores_scheduled_only"]
    rows = []
    for model in ("L0", "L1", "L2", "L3", "L4"):
        s = scores[model]
        skill = "&mdash;" if s.get("skill_vs_l1") is None else score(s["skill_vs_l1"])
        cls = ' class="model-l1"' if model == "L1" else ""
        rows.append(
            f"            <tr{cls}><td><strong>{model}</strong>"
            f'<span class="model-gloss">{MODEL_GLOSS[model]}</span></td>'
            f"<td>{score(s['mean_brier'])}</td>"
            f"<td>{score(s['mean_log_score'])}</td><td>{skill}</td><td>{s['n']}</td></tr>"
        )
    body = '\n          <tbody id="ladder-tbody">\n' + "\n".join(rows) + "\n          </tbody>\n        "
    html = replace_region(html, "ladder", body)

    # The n / specials / clip line under the "More detail" expander, which
    # renderLadder() also overwrites and which silently carried n=60 through
    # the July ingest until a test caught it.
    meta = (
        f'\n          <p class="fine" id="ladder-meta" style="margin-top:0">Scheduled meetings '
        f'only, evaluated from {f["eval_start"]} onwards (n&nbsp;=&nbsp;{f["n_scheduled"]}); '
        f'{f["n_specials"]} special meetings reported separately, not blended in; '
        f'log-score probability floor {f["log_clip"]}.</p>\n'
        f'          '
    )
    return replace_region(html, "laddermeta", meta)


# -------------------------------------------------------------- spec 3


def spec3_sentence(f: dict[str, str], code_open: str = "<code>", code_close: str = "</code>",
                   strong_open: str = "<strong>", strong_close: str = "</strong>",
                   em_open: str = "<em>", em_close: str = "</em>", ndash: str = "&ndash;") -> str:
    """The one Spec 3 / Spec 2 sentence, rounded for reading, with the full
    precision one link away. Shared by index.html and README.md."""
    return (
        f"Regressing each meeting's market surprise on the {em_open}previous{em_close} meeting's index "
        f"(OLS, Newey{ndash}West standard errors, {f['nw_lags']} lags, n={f['spec3_n']} "
        f"scheduled meetings): coefficient {strong_open}{f['spec3_coef']}{strong_close} "
        f"(t = {f['spec3_t']}, {strong_open}p = {f['spec3_p']}{strong_close}). On the post-hiking-cycle "
        f"subsample (from {f['frag_start']}, n={f['frag_n']}) the result does not "
        f"replicate: coefficient {f['frag_coef']} (t = {f['frag_t']}, p = {f['frag_p']}). "
        f"Spec 2, an ordered-logit likelihood-ratio test on the discrete decision, finds "
        f"nothing: LR = {f['spec2_lr']}, p = {f['spec2_p']}. "
        f"Coefficients and t-statistics are rounded to 2 decimal places and p-values to 4; "
        f"full precision is in {code_open}data/inference_v1.json{code_close}."
    )


def build_spec3(html: str) -> str:
    line = spec3_sentence(figures())
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
        brier = "&mdash;" if r["brier_m0"] is None else score(r["brier_m0"])
        rows.append(
            f'            <tr class="kind-{r["kind"]}">'
            f'<td>{gb_date(r["meeting_announcement"])}</td>'
            f'<td><span class="track-badge {r["kind"]}">{BADGE_LABEL[r["kind"]]}</span></td>'
            f'<td>{r["point_call"] or "&mdash;"}</td>'
            f'<td>{pct(m0["p_cut"])}</td><td>{pct(m0["p_hold"])}</td><td>{pct(m0["p_hike"])}</td>'
            f'<td>{r["outcome"] or "&mdash;"}</td><td>{brier}</td></tr>'
        )
    # The next meeting in the Bank's calendar after the newest locked call,
    # as a pending row: lock date, no call, no probabilities, no score. It
    # shows the mechanism's cadence, and it moves on by itself once a
    # lock-* file for that meeting exists (prediction_file() picks the
    # newest). renderTrackRecord() keeps this row when it rebuilds the table.
    f = figures()
    rows.append(
        f'            <tr class="kind-pending"><td>{f["next_meeting"]}</td>'
        f'<td><span class="track-badge pending">Pending</span> '
        f'<span class="track-lockdate">locks {f["next_lock_date"]}</span></td>'
        f'<td>&mdash;</td><td>&mdash;</td><td>&mdash;</td><td>&mdash;</td>'
        f'<td>&mdash;</td><td>&mdash;</td></tr>'
    )
    body = '\n          <tbody id="track-tbody">\n' + "\n".join(rows) + "\n          </tbody>\n        "
    return replace_region(html, "track", body)


# ---------------------------------------------------- verification box


def build_verify(html: str) -> str:
    """The tag, the git command and the repository, in one place.

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
    m0 = lock["m0_market_only"]
    probs = [("cut", m0["p_cut"]), ("hold", m0["p_hold"]), ("hike", m0["p_hike"])]
    lead = max(probs, key=lambda kv: kv[1])[0]
    tag = Path(PREDICTION_FILE).stem
    tag_url = f"{REPO_URL}/releases/tag/{tag}"

    scored = lock["outcome"] is not None and lock["scores"] is not None
    brier = lock["scores"]["m0_market_only"]["brier_score"]
    hit = lock["point_call"] == lock["outcome"]

    # Next announcement: the first meeting in the Bank's published calendar
    # after this call's own. From the calendar constant, never typed in.
    next_meeting = next_meeting_after(lock["meeting_announcement"])

    stamp_iso = lock["lock_timestamp"]
    stamp_utc = gb_stamp_utc(stamp_iso)
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
        f'<span class="n">{pct(v)}</span><span class="l">{k}</span></div>'
        for k, v in probs
    )
    bar_segs = "".join(
        f'<span class="seg-{k}" style="width:{v * 100:.1f}%"></span>' for k, v in probs
    )
    vs = abs(lock["index_current"] - lock["index_trailing_mean"])
    word = "above" if lock["index_current"] > lock["index_trailing_mean"] else "below"

    body = f'''
  <section class="card call-card locked" id="call-card" aria-labelledby="call-badge"
           data-prediction-file="{PREDICTION_FILE}">
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

    <!-- The same "In plain English" device the Results section uses. -->
    <p class="plain-summary" id="call-plain"><em>In plain English: this is the call, written
    down and tagged before the announcement so it cannot be revised afterwards. The
    percentages are the market's; the point call and the reasoning are mine.</em></p>

    <div class="call-probs" id="call-probs">{prob_divs}</div>
    <div class="call-probbar" id="call-probbar" aria-hidden="true">{bar_segs}</div>
    <p class="call-probsrc" id="call-probsrc"><strong>m0</strong> <span class="prob-gloss">{M0_GLOSS}</span> &mdash; OIS forward curve vs SONIA, {m0["assumed_move_bp"]:g}bp two-state assumption. Not the point call.</p>
    <p class="fine call-index-line" id="call-index-line">A&amp;BG index ({lock["index_current_doc_id"]}): <strong>{index_value(lock["index_current"])}</strong> vs trailing {lock["index_trailing_n"]}-document mean <strong>{index_value(lock["index_trailing_mean"])}</strong> ({index_value(vs)} {word})</p>
    <div class="call-rationale" id="call-rationale">
      <p class="call-rationale-h" id="call-rationale-h">Point call <span class="pt-call">{lock["point_call"]}</span></p>
      <p class="call-rationale-body" id="call-rationale-body">{rationale}</p>
    </div>
    <p class="fine" id="call-fine" style="display:none"></p>

    <!-- Once the announcement has happened and score_outcomes has run, the
         card stops being a forward-looking notice and becomes a result. Both
         figures come from the locked file's own outcome/scores fields. -->
    <div class="call-outcome" id="call-outcome">
      <div class="call-outcome-row"><span class="oc-item"><span class="oc-l">Outcome</span><span class="oc-v">{lock["outcome"]}</span></span><span class="oc-item"><span class="oc-l">Brier (m0)</span><span class="oc-v">{score(brier)}</span></span><span class="oc-item"><span class="oc-l">Point call</span><span class="oc-v{" oc-hit" if hit else ""}">{"matched" if hit else "missed"}</span></span></div>
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


def lexicon_id(index: dict) -> str:
    """The lexicon's short name. data/index.json's `lexicon` field is a
    sentence of provenance ("abg_2012 (Apel & Blix Grimaldi 2012, verbatim -
    see ...)"); the page shows its identifier and links the file. Mirrored in
    renderLatest()."""
    return index["lexicon"].split()[0]


def build_latest(html: str) -> str:
    """renderLatest()'s output, generated - the reading, not "Loading..."."""
    data = load("data/index.json")
    doc = data["documents"][-1]
    mid = data["neutral_value"]
    net = doc["abg_net_index"] - mid
    cls = "sign-hawk" if net > 0 else ("sign-dove" if net < 0 else "")
    word = "net hawkish" if net > 0 else ("net dovish" if net < 0 else "neutral")
    body = f'''
    <div class="reading" id="content">
      <p class="docline" id="docline">MPC minutes, meeting ending <strong>{gb_date(doc["meeting_end"])}</strong> &middot; published {gb_date(doc["published"])} &middot; decision: {doc["decision"]} &middot; vote {doc["vote"]}</p>
      <p class="score" id="score"><span class="{cls}">{index_value(doc["abg_net_index"])}</span> <span class="score-word">{word} (A&amp;BG Net Index, 0&ndash;2 scale, {neutral(mid)} = neutral)</span></p>
      <div class="scale"><div class="marker" id="marker" style="left:{50 + net * 50:.4f}%"></div></div>
      <div class="scale-labels"><span>&larr; dovish</span><span>neutral</span><span>hawkish &rarr;</span></div>
      <p class="fine" id="detail">{doc["abg_hawk"]} hawkish vs {doc["abg_dove"]} dovish noun+adjective hits &middot; lexicon <code>{lexicon_id(data)}</code> &middot; sha256 <code>{doc["sha256"][:16]}&hellip;</code> &middot; <a href="{doc["source_url"]}">source document</a></p>
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
    {gb_date(series[-1]["date"])} on the A&amp;BG 0&ndash;2 scale, where {neutral(data["neutral_value"])}
    is neutral. Latest <strong>{index_value(values[-1])}</strong> ({series[-1]["doc_id"]}); series low
    {index_value(lo["abg_net_index"])} ({lo["doc_id"]}), high {index_value(hi["abg_net_index"])} ({hi["doc_id"]}).
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

      <p class="ctx-note" id="context-note">{CONTEXT_NOTE} Sources: Bank of England OIS forward curve &amp; SONIA; GLC nominal gilt curve; Bank Rate from the voting record.</p>
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


# -------------------------------------------------------------- README


def build_readme(md: str) -> str:
    """README.md's headline table, Spec 3 paragraph, lock line and byline.

    Markdown, so the values are plain characters (a real minus sign, not an
    entity) and the table is a pipe table. Same catalogue, same rounding.
    """
    f = plain()
    d = load("data/ladder_v1.json")
    scores = d["headline_scores_scheduled_only"]
    rows = [
        "| Model | Description | Mean Brier | Mean log score | Skill vs L1 | n |",
        "|---|---|---|---|---|---|",
    ]
    for model in ("L0", "L1", "L2", "L3", "L4"):
        s = scores[model]
        if model == "L1":
            skill = "reference"
        elif s.get("skill_vs_l1") is None:
            skill = "—"
        else:
            skill = plain({"v": score(s["skill_vs_l1"])})["v"]
        desc = MODEL_DESCRIPTION[model].format(move_bp=f["move_bp"])
        rows.append(
            f"| {model} | {desc} | {plain({'v': score(s['mean_brier'])})['v']} | "
            f"{plain({'v': score(s['mean_log_score'])})['v']} | {skill} | {s['n']} |"
        )
    md = replace_region(md, "readme_ladder", "\n" + "\n".join(rows) + "\n", where="README.md")

    spec3 = spec3_sentence(
        f, code_open="`", code_close="`", strong_open="**", strong_close="**",
        em_open="*", em_close="*", ndash="–",
    )
    md = replace_region(md, "readme_spec3", spec3, where="README.md")

    lock_line = (
        f"**First pre-registered lock: {f['lock_stamp_utc']}, for the {f['lock_meeting']} "
        f"announcement** (tag `{f['lock_tag']}`). Locked calls so far: {f['lock_count']}. "
        f"Next lock: {f['next_lock_date']}, for the {f['next_meeting']} announcement."
    )
    md = replace_region(md, "readme_lock", lock_line, where="README.md")

    byline = (
        f"Built and maintained by {AUTHOR['name']}, {AUTHOR['affiliation']}. "
        f"Contact: <{AUTHOR['email']}>."
    )
    return replace_region(md, "byline", byline, where="README.md")


def main() -> None:
    index_path = ROOT / "index.html"
    html = index_path.read_text()
    for fn in (
        build_verify, build_call, build_latest, build_chart, build_context,
        build_ladder, build_spec3, build_track, build_episodes, build_gen_note,
    ):
        html = fn(html)
    html = build_meta(html, "index.html")
    html = build_byline(html, "index.html")
    html = build_status(html, "index.html")
    html = build_related_work(html, "index.html")
    html = write_figures(html, "index.html")
    index_path.write_text(html)

    meth_path = ROOT / "methodology.html"
    meth = meth_path.read_text()
    meth = build_meta(meth, "methodology.html")
    meth = build_byline(meth, "methodology.html")
    meth = build_status(meth, "methodology.html")
    meth = build_related_work(meth, "methodology.html")
    meth_path.write_text(write_figures(meth, "methodology.html"))

    readme_path = ROOT / "README.md"
    readme = build_readme(readme_path.read_text())
    readme_path.write_text(write_figures(readme, "README.md", plain()))

    print(
        "regenerated index.html blocks: verify, call, latest, chart, context, "
        "ladder, spec3, track, episodes, gennote, meta, byline, status, related work; "
        "methodology.html: meta, byline, status, references; "
        "README.md: ladder table, spec3, lock line, byline"
    )


if __name__ == "__main__":
    main()
