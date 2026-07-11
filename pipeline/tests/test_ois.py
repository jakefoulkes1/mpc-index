import datetime as dt

import openpyxl
import pytest

from pipeline.market.ois import _read_forward_curve_sheet, parse_sonia_csv

SONIA_FIXTURE = """SERIES,DESCRIPTION
IUDSOIA,Daily Sterling overnight index average (SONIA) rate

DATE,IUDSOIA
01 Jun 2026,3.7291
02 Jun 2026,3.7308
03 Jun 2026,3.7306
"""


def _sample_forward_curve_workbook(tmp_path, sheet_name="1. fwds, short end"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append([None, "UK instantaneous OIS forward curve"])
    ws.append(["Maturity "])
    ws.append(["months:", 1, 2, 3])
    ws.append(["years:", 1 / 12, 2 / 12, 3 / 12])
    ws.append(["Refresh", "Refresh", "Refresh", "Refresh"])
    ws.append([dt.datetime(2026, 6, 29), 3.72, 3.76, 3.80])
    ws.append([dt.datetime(2026, 6, 30), 3.73, 3.77, 3.81])
    path = tmp_path / "sample.xlsx"
    wb.save(path)
    return path


def test_read_forward_curve_sheet_happy_path(tmp_path):
    path = _sample_forward_curve_workbook(tmp_path)
    sheet_name, maturities, rows = _read_forward_curve_sheet(path)
    assert sheet_name == "1. fwds, short end"
    assert maturities == [1.0, 2.0, 3.0]
    assert rows[-1] == (dt.date(2026, 6, 30), [3.73, 3.77, 3.81])


def test_read_forward_curve_sheet_tries_alternate_sheet_names(tmp_path):
    path = _sample_forward_curve_workbook(tmp_path, sheet_name="1. fwd curve")
    sheet_name, maturities, rows = _read_forward_curve_sheet(
        path, sheet_names=("1. fwds, short end", "1. fwd curve")
    )
    assert sheet_name == "1. fwd curve"
    assert maturities == [1.0, 2.0, 3.0]


def test_read_forward_curve_sheet_returns_none_for_wrong_layout(tmp_path):
    wb = openpyxl.Workbook()
    wb.active.title = "some other sheet"
    path = tmp_path / "wrong.xlsx"
    wb.save(path)
    assert _read_forward_curve_sheet(path) is None


def test_parse_sonia_csv():
    rows = parse_sonia_csv(SONIA_FIXTURE)
    assert rows == [
        (dt.date(2026, 6, 1), 3.7291),
        (dt.date(2026, 6, 2), 3.7308),
        (dt.date(2026, 6, 3), 3.7306),
    ]


def test_parse_sonia_csv_hard_stops_on_missing_header():
    with pytest.raises(ValueError, match="HARD STOP"):
        parse_sonia_csv("not,a,sonia,csv\n1,2,3")
