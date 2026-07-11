import datetime as dt

import openpyxl

from pipeline.build_votes import load_member_columns, parse_meetings


def _sample_ws():
    wb = openpyxl.Workbook()
    ws = wb.active
    # Mimic the real sheet's layout: header names on row 4 (1-indexed),
    # meeting rows from row 5 (date in col B, decided rate in col C).
    ws.append([None] * 6)
    ws.append([None, None, None, "Monetary Policy Committee voting history - Bank Rate"])
    ws.append([None] * 6)
    ws.append([None, None, "Current members", "Ada Lovelace", "Grace Hopper", "Past members", "Alan Turing"])
    ws.append([None, dt.datetime(2026, 6, 18), 0.0375, 0.0375, 0.04, None, None])
    ws.append([None, dt.datetime(2026, 4, 30), 0.0375, 0.0375, None, None, 0.035])
    ws.append([None, dt.datetime(1998, 1, 8), 0.07, "Increase", None, None, None])  # pre-era, qualitative
    return ws


def test_load_member_columns_skips_labels():
    ws = _sample_ws()
    columns = load_member_columns(ws)
    assert columns == {3: "Ada Lovelace", 4: "Grace Hopper", 6: "Alan Turing"}


def test_parse_meetings_skew_and_dissents():
    ws = _sample_ws()
    columns = load_member_columns(ws)
    meetings = parse_meetings(ws, columns)
    assert len(meetings) == 2  # the 1998 row is outside the era filter

    m = next(m for m in meetings if m["meeting_date"] == "2026-06-18")
    assert m["decided_rate"] == 0.0375
    assert m["votes"] == {"Ada Lovelace": 0.0375, "Grace Hopper": 0.04}
    assert m["hawkish_dissents"] == 1
    assert m["dovish_dissents"] == 0
    assert m["skew"] > 0

    m2 = next(m for m in meetings if m["meeting_date"] == "2026-04-30")
    assert m2["votes"] == {"Ada Lovelace": 0.0375, "Alan Turing": 0.035}
    assert m2["dovish_dissents"] == 1
