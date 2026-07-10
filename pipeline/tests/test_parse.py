from pathlib import Path

from pipeline.parse.html_text import html_to_text

FIX = Path(__file__).parent / "fixtures"


def test_strips_nav_and_footer_keeps_body():
    text = html_to_text((FIX / "sample.html").read_text())
    assert "Inflationary pressures" in text
    assert "Main menu" not in text
    assert "Follow us" not in text
