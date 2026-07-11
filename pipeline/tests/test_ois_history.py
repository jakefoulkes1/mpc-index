import datetime as dt

import pytest

from pipeline.market.ois_history import find_nearest_available_date


def test_find_nearest_available_date_exact_match():
    dates = {dt.date(2026, 1, 6), dt.date(2026, 1, 7)}
    found, walked = find_nearest_available_date(dates, dt.date(2026, 1, 7))
    assert found == dt.date(2026, 1, 7)
    assert walked == 0


def test_find_nearest_available_date_walks_back_over_weekend():
    # Friday 2 Jan 2026 is available; Sat/Sun 3-4 Jan are not (weekend gap).
    dates = {dt.date(2026, 1, 2), dt.date(2025, 12, 31)}
    found, walked = find_nearest_available_date(dates, dt.date(2026, 1, 4))
    assert found == dt.date(2026, 1, 2)
    assert walked == 2


def test_find_nearest_available_date_hard_stops_beyond_max_walk():
    with pytest.raises(ValueError, match="HARD STOP"):
        find_nearest_available_date(set(), dt.date(2026, 1, 4), max_walk=3)
