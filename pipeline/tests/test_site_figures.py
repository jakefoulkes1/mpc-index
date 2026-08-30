"""Contract test: no number on either page may disagree with its source file.

index.html and methodology.html carry figures in running prose - sample
sizes, coefficients, p-values, corpus counts. Prose is the author's; the
numbers inside it are the data's, and the two drift apart silently. On
2026-08-10 the July ingest updated index.html and left methodology.html a
meeting behind: 94 documents, 62 evaluated, 60 scheduled, Spec 3 n=91,
fragility n=23, p=0.1422 - every one of them stale, every one of them
plausible, and nothing failed.

This test closes that gap in two directions.

  1. Every `<!-- fig:NAME -->...<!-- /fig:NAME -->` region on either page
     must hold exactly what pipeline/site_figures.py computes for NAME from
     the data. Regenerate with `python -m pipeline.build_fallbacks`; never
     retype a figure into the markup.

  2. Every remaining number in the reader-visible text of either page - that
     is, outside the generated fig and fallback regions - must be accounted
     for by name below, as either an identifier that merely contains a digit
     (L3, Spec 2, SHA-256) or a literal that is not a figure from a data file
     (a citation year, a scale endpoint, a historical date). Anything else
     fails, because an unexplained number in prose is exactly what went stale
     last time.

Adding a figure to a page therefore means adding it to
pipeline/site_figures.py, not typing it - which is the point.

See DECISIONS.md, 2026-08-30.
"""
import html as H
import re
from pathlib import Path

import pytest

from pipeline.site_figures import figures

ROOT = Path(__file__).resolve().parents[2]
PAGES = ("index.html", "methodology.html")

FIG_RE = re.compile(
    r"<!--\s*fig:(?P<name>[a-z0-9_]+)\s*-->(?P<body>.*?)<!--\s*/fig:(?P=name)\s*-->",
    re.S,
)

# Names that contain a digit but are not figures: model and specification
# labels, file names, schema tags, standards, dated log references.
IDENTIFIERS = [
    (r"\bL[0-4]\b", "benchmark ladder model names"),
    (r"\bm0\b", "the market-only reference's name"),
    (r"\bSpec ?[23]\b", "specification names"),
    (r"\bQ[13]\b", "quartile names"),
    (r"\bladder-v1\b", "the ladder schema tag"),
    (r"\bSHA-256\b", "the hash algorithm's name"),
    (r"\babg_2012\.json\b", "the lexicon file's name"),
    (r"\b(?:ladder_v1|inference_v1|validation_v1|member_behaviour_v1)\.json\b", "data file names"),
    (r"\bmarket_history\.csv\b", "a data file name"),
    (r"\bindex\.json\b", "a data file name"),
    (r"\b\d{4}-\d{2}-\d{2}\b", "dated DECISIONS.md entry references"),
    (r"\bLOCK_OFFSET_DAYS=3\b", "a code constant quoted by name in a citation"),
    (r"\bp\.1[03]\b", "page references into Apel & Blix Grimaldi (2012)"),
    (r"\bNo\. 261\b", "the working paper's number"),
    (r"\bCovid-19\b", "the name of the 2020 emergency"),
]

# Literals that really are numbers, but are not figures computed from a data
# file: historical facts, citation years, definitional endpoints, and
# specification constants stated inside a citation rather than as a claim.
# A removed fig region collapses to a single space, so an allowlisted phrase
# that straddles one is written here with that gap in it.
NOT_A_FIGURE = [
    ("Apel & Blix Grimaldi, 2012", "the lexicon paper's publication year"),
    ("Apel & Blix Grimaldi (2012", "the lexicon paper's publication year"),
    ("after Gerlach-Kristen 2004", "a citation year"),
    ("a published 2012 dictionary", "the lexicon's vintage"),
    ("the paper's 2012 vintage", "the lexicon's vintage"),
    ("Aug 2015-present", "the chart's own axis label, abbreviated"),
    ("the two emergency meetings of March 2020", "a historical fact, not a count from a file"),
    ("the March 2020 emergency meetings", "a historical fact, not a count from a file"),
    ("the 10 March and 19 March 2020 Covid-19 decisions", "the two emergency meeting dates"),
    ("19 March 2020 special meeting added", "a DECISIONS.md entry title"),
    ("A&BG (2012) baseline lexicon", "a DECISIONS.md entry title"),
    ("for 2016 and for 2017", "the two calendar years whose counts are figures either side"),
    ("a 2012 word list", "the lexicon's vintage"),
    ("all before the sample's first cut in March 2020",
     "when the ordered-logit fallbacks stopped, a historical fact about the sample"),
    ("clip(|implied change| / , 0, 1)", "the clip's bounds, which are definitional"),
    ("-log(0) for a confidently wrong call", "the value the probability floor exists to avoid"),
    ("it fades after 2023", "the plain-English gloss on the fragility window"),
    ("the August 2015 regime change", "the Bank's own change of publication regime"),
    ("Meetings were monthly from 2015 until the autumn of 2016 , not 2017",
     "a documented fact about the Bank's meeting schedule"),
    ("on 9 May 2016, once the Bank of England and Financial Services Act 2016 had received Royal Assent",
     "the Act and the Bank's announcement date"),
    ("the meeting scheduled for 13 October 2016", "the first meeting dropped under the new schedule"),
    ("2017 is therefore the first full calendar year with eight",
     "a documented fact about the Bank's meeting schedule"),
    ("9 May 2016, and MPC publication dates for 2016 and provisional dates for 2017",
     "the titles and dates of two Bank of England news pages"),
    ("24 September 2015", "the publication date of a cited Bank of England page"),
    ("Until August 2021 the Bank published the full minutes as a separate PDF",
     "the date the Bank changed how it published minutes"),
    ("meeting_end + 1 day", "the published-date rule, a convention rather than a measurement"),
    ("the 2019 window", "shorthand for the evaluation window, whose start is a figure elsewhere"),
    ("2009-2015 / 2016-2024 / 2025-present", "the era files' own coverage, as the Bank names them"),
    ("a 2-week-average alternative was rejected",
     "a rejected alternative convention, recorded as history"),
    ("on the 2026 curve", "the curve vintage the bias was quantified on"),
    ("the 30 July 2026 lock rationale", "the locked call this limitation was raised in"),
    ("post-September-2023", "the fragility window, whose start date is a figure elsewhere"),
    ("a 0-2 scale where 1.0 is neutral", "the index's definitional range and midpoint"),
    ("Range [0, 2]", "the index's definitional range"),
    ("1.0 is neutral", "the index's definitional midpoint"),
    ("(#dove / (#hawk + #dove)) ] + 1", "the paper's formula, reproduced"),
    ("range [0, 2]", "the Brier score's definitional range"),
    ("0 is a perfect call", "a glossary definition"),
    ("0 is a tie with the benchmark", "a glossary definition"),
    ("where zero would be a tie", "prose, not a figure"),
    ("(p hold = 1), the naive baseline", "L0's definition"),
    ("(proportional odds, classes)", "left by the generated class count"),
    ("blended 0.5/0.5 with the market-implied distribution",
     "the L4 blend weight, a specification choice written as a ratio"),
    ("fewer than 2 outcome classes", "an ordered-logit precondition, not a result"),
    ("at lock time (2 business days before an announcement)",
     "the lock protocol's timing, stated as protocol rather than read from a file"),
    ("two-state ±25bp assumption", "a DECISIONS.md entry title"),
    ("±25bp mapping above", "a back-reference to the mapping defined above"),
    ("the two-state ±25bp mapping above", "a back-reference to the mapping defined above"),
]


def page_text(raw: str) -> str:
    """Reader-visible text with every generated region taken out."""
    s = re.sub(r"<script\b.*?</script>", " ", raw, flags=re.S)
    s = re.sub(r"<style\b.*?</style>", " ", s, flags=re.S)
    for kind in ("fallback", "fig"):
        s = re.sub(
            rf"<!--\s*{kind}:([a-z0-9_]+)\b.*?-->.*?<!--\s*/{kind}:\1\s*-->", " ", s, flags=re.S
        )
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    s = H.unescape(s)
    # One dash and one space, so the allowlist can be written in plain text.
    for ch in ("−", "–", "—"):
        s = s.replace(ch, "-")
    s = s.replace(" ", " ").replace("‑", "-")
    return re.sub(r"\s+", " ", s).strip()


@pytest.mark.parametrize("page", PAGES)
def test_every_figure_region_matches_its_source(page):
    """A number inside a fig region is the data's, to the character."""
    catalogue = figures()
    raw = (ROOT / page).read_text()
    found = list(FIG_RE.finditer(raw))
    assert found, f"{page} has no fig regions - has the markup lost its markers?"
    for m in found:
        name, body = m.group("name"), m.group("body")
        assert name in catalogue, (
            f"{page} references fig:{name}, which pipeline/site_figures.py does not define"
        )
        assert body == catalogue[name], (
            f"{page}'s fig:{name} reads {body!r} but its source says "
            f"{catalogue[name]!r} - re-run python -m pipeline.build_fallbacks; "
            f"never retype a figure by hand"
        )


def test_the_two_pages_never_disagree_about_a_shared_figure():
    """The same figure on both pages is the same number on both pages.

    This is the specific failure of 2026-08-10: index.html was rebuilt and
    methodology.html was not, so the two pages published different sample
    sizes for the same test.
    """
    seen: dict[str, tuple[str, str]] = {}
    for page in PAGES:
        for m in FIG_RE.finditer((ROOT / page).read_text()):
            name, body = m.group("name"), m.group("body")
            if name in seen and seen[name][1] != body:
                other_page, other_body = seen[name]
                pytest.fail(
                    f"fig:{name} reads {other_body!r} in {other_page} but {body!r} in {page}"
                )
            seen[name] = (page, body)


def test_no_catalogue_figure_is_dead():
    """Every figure the catalogue computes is actually shown somewhere.

    Either in a fig region, or inside a generated fallback block - the Spec 3
    line, for instance, is built whole from the catalogue rather than
    assembled around fig markers.
    """
    catalogue = figures()
    used = set()
    for page in PAGES:
        raw = (ROOT / page).read_text()
        used |= {m.group("name") for m in FIG_RE.finditer(raw)}
        blocks = " ".join(
            m.group(0)
            for m in re.finditer(
                r"<!--\s*fallback:([a-z0-9_]+)\b.*?-->.*?<!--\s*/fallback:\1\s*-->", raw, re.S
            )
        )
        used |= {name for name, value in catalogue.items() if value in blocks}
    unused = set(catalogue) - used
    assert not unused, (
        f"pipeline/site_figures.py computes figures no page shows: {sorted(unused)} - "
        f"either use them or delete them"
    )


@pytest.mark.parametrize("page", PAGES)
def test_no_number_escapes_a_generated_region_unaccounted_for(page):
    """The census: after the generated regions, the identifiers and the
    allowlist are removed, no digit may remain in reader-visible text."""
    text = page_text((ROOT / page).read_text())
    # Phrases first, then identifiers: several allowlisted phrases contain an
    # identifier ("...19 March 2020 Covid-19 decisions") and would not match
    # once it had been taken out from under them.
    for phrase, _reason in NOT_A_FIGURE:
        text = text.replace(phrase, " ")
    for pattern, _reason in IDENTIFIERS:
        text = re.sub(pattern, " ", text)
    leftovers = [
        m.group(0).strip()
        for m in re.finditer(r"[^.;:!?]*\d[^.;:!?]*", text)
    ]
    assert not leftovers, (
        f"{page} states {len(leftovers)} number(s) that are neither generated from a data "
        f"file nor listed in this test's allowlist. Generate them (add the figure to "
        f"pipeline/site_figures.py and wrap it in a fig region) or, if the number is not a "
        f"figure, add it to NOT_A_FIGURE with a reason:\n  "
        + "\n  ".join(repr(x[:160]) for x in leftovers)
    )


def test_the_allowlist_has_no_stale_entries():
    """Every allowlisted phrase and identifier still appears on a page.

    A stale allowlist is how a guard quietly stops guarding: the entry that
    once excused a number goes on excusing whatever replaces it.
    """
    combined = " ".join(page_text((ROOT / page).read_text()) for page in PAGES)
    unused_ids = [p for p, _ in IDENTIFIERS if not re.search(p, combined)]
    assert not unused_ids, f"IDENTIFIERS patterns that match nothing any more: {unused_ids}"
    unused_phrases = [p for p, _ in NOT_A_FIGURE if p not in combined]
    assert not unused_phrases, (
        f"NOT_A_FIGURE entries that appear on neither page any more: {unused_phrases}"
    )
