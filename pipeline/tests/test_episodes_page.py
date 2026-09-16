"""The episode notes moved to their own page on 2026-09-02. This is what
that move promised.

index.html used to carry every note whole - 1,324 words, 37% of the front
page. The notes are now published at episodes.html and the front page keeps
an index to them: title, date, the note's own opening two sentences, and a
link. Three things could quietly break that and did not fail anything:

  1. a note published in data/annotations.json but not rendered on
     episodes.html, so its anchor 404s from the front page;
  2. an episode body creeping back onto index.html;
  3. a standfirst that is not the note's own words - a summary written on
     the front page and never checked against what it stands for.

The link into the essay from the track record moved with it, so the fourth
check is that no in-page #episode- anchor is left on index.html.

See DECISIONS.md, 2026-09-17 (front-page structure pass, landed).
"""
import json
import re
from pathlib import Path

import pytest

from pipeline.build_fallbacks import episode_standfirst, sentences

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "index.html"
EPISODES = ROOT / "episodes.html"


@pytest.fixture(scope="module")
def episodes() -> list[dict]:
    return json.loads((ROOT / "data" / "annotations.json").read_text())["episodes"]


def test_every_published_note_is_rendered_on_its_own_page(episodes):
    html = EPISODES.read_text()
    for ep in episodes:
        anchor = f'id="episode-{ep["date"]}"'
        assert anchor in html, f"episodes.html has no {anchor} for {ep['title']!r}"
        assert ep["title"] in html, f"episodes.html does not carry the title {ep['title']!r}"


def test_the_page_carries_the_note_whole(episodes):
    """Not shortened, not rewritten: every paragraph of the source markdown
    reaches the page."""
    html = EPISODES.read_text()
    for ep in episodes:
        for block in re.split(r"\n{2,}", (ep.get("body") or "").strip()):
            if block.startswith("#") or block.lstrip().startswith("- "):
                continue
            # The renderer joins wrapped lines with a space and escapes.
            text = " ".join(block.split()).replace("&", "&amp;").replace("<", "&lt;")
            assert text in html, (
                f"episodes.html is missing a paragraph of {ep['title']!r}: {text[:80]!r}"
            )


def test_the_contents_list_resolves(episodes):
    html = EPISODES.read_text()
    toc = re.search(r"<!--\s*fallback:toc\s*-->(.*?)<!--\s*/fallback:toc\s*-->", html, re.S)
    assert toc, "episodes.html has no generated contents"
    hrefs = re.findall(r'href="#(episode-[^"]+)"', toc.group(1))
    assert len(hrefs) == len(episodes), "the contents and the notes have drifted apart"
    for frag in hrefs:
        assert f'id="{frag}"' in html, f"the contents link to #{frag}, which is not on the page"


def test_the_front_page_links_out_and_carries_no_body(episodes):
    html = INDEX.read_text()
    for ep in episodes:
        assert f'href="episodes.html#episode-{ep["date"]}"' in html, (
            f"index.html does not link to the note for {ep['date']}"
        )
    assert 'class="ep-body"' not in html, (
        "an episode body is back on the front page - the notes live on episodes.html"
    )
    assert not re.search(r'href="#episode-', html), (
        "index.html still has an in-page episode anchor; the notes are on episodes.html now"
    )


def test_each_standfirst_is_the_notes_own_first_two_sentences(episodes):
    """The front page must not summarise a note in words the note does not
    use. The standfirst is generated from the note's opening block."""
    html = INDEX.read_text()
    for ep in episodes:
        stand = episode_standfirst(ep)
        assert f'<p class="ep-standfirst">{stand}</p>' in html, (
            f"the standfirst for {ep['title']!r} is not the note's own opening two sentences"
        )
        first_block = re.split(r"\n{2,}", (ep.get("body") or "").strip())[0]
        assert first_block.startswith(sentences(first_block, 2, ep["title"])[:40])


def test_the_sentence_rule_stops_rather_than_guessing():
    """A passage with too few sentences must halt the build, not be padded or
    truncated into shape."""
    with pytest.raises(SystemExit) as e:
        sentences("One sentence only, and no break after it.", 2, "a test passage")
    assert "HARD STOP" in str(e.value)
