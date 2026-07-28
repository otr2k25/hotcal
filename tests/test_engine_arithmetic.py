import datetime
import random

import pytest

from hotcal import engine


def test_from_ordinal_round_trips_against_ordinal():
    random.seed(0)
    for _ in range(2000):
        year = random.randint(1, 9999)
        month = random.randint(1, 12)
        day = random.randint(1, engine.days_in_month(year, month))
        n = engine.ordinal(year, month, day)
        assert engine.from_ordinal(n) == (year, month, day)


def test_from_ordinal_matches_datetime():
    for year, month, day in [(2026, 7, 27), (1, 1, 1), (9999, 12, 31), (1600, 2, 29), (1900, 2, 28)]:
        expected = datetime.date(year, month, day)
        got = engine.from_ordinal(engine.ordinal(year, month, day))
        assert got == (expected.year, expected.month, expected.day)


def test_from_ordinal_handles_years_outside_datetime_range():
    for year in (-500, 0, 10000, 100000, -100000):
        n = engine.ordinal(year, 1, 15)
        assert engine.from_ordinal(n) == (year, 1, 15)


def test_add_days_crosses_month_and_year_boundaries():
    assert engine.add_days(2026, 12, 31, 1) == (2027, 1, 1)
    assert engine.add_days(2027, 1, 1, -1) == (2026, 12, 31)
    assert engine.add_days(2024, 2, 28, 1) == (2024, 2, 29)  # leap year


def test_add_months_clamps_to_shorter_month():
    assert engine.add_months(2026, 3, 31, -1) == (2026, 2, 28)
    assert engine.add_months(2026, 1, 31, 1) == (2026, 2, 28)
    assert engine.add_months(2026, 1, 31, -1) == (2025, 12, 31)


def test_add_years_clamps_leap_day():
    assert engine.add_years(2024, 2, 29, 1) == (2025, 2, 28)
    assert engine.add_years(2024, 2, 29, 4) == (2028, 2, 29)


def test_add_offset_units():
    assert engine.add_offset(2026, 7, 27, 2, "days") == (2026, 7, 29)
    assert engine.add_offset(2026, 7, 27, 3, "weeks") == (2026, 8, 17)
    assert engine.add_offset(2026, 7, 27, -1, "months") == (2026, 6, 27)
    assert engine.add_offset(2026, 7, 27, -100, "years") == (1926, 7, 27)


def test_next_weekday_skips_today_even_if_matching():
    # 2026-07-27 is a Monday; "next monday" must not be today.
    assert engine.next_weekday(2026, 7, 27, 0) == (2026, 8, 3)


def test_last_weekday_skips_today_even_if_matching():
    assert engine.last_weekday(2026, 7, 27, 0) == (2026, 7, 20)


def test_next_and_last_weekday_general_case():
    assert engine.next_weekday(2026, 7, 27, 4) == (2026, 7, 31)  # next Friday
    assert engine.last_weekday(2026, 7, 27, 4) == (2026, 7, 24)  # last Friday


def test_weekday_of_week_finds_monday_of_same_week():
    assert engine.weekday_of_week(2026, 8, 17, 0) == (2026, 8, 17)
    assert engine.weekday_of_week(2026, 7, 27, 6) == (2026, 8, 2)  # Sunday of that week


def test_add_offset_rejects_unknown_unit():
    with pytest.raises(ValueError):
        engine.add_offset(2026, 7, 27, 1, "fortnights")


def test_last_day_of_month():
    assert engine.last_day_of_month(2026, 7) == (2026, 7, 31)
    assert engine.last_day_of_month(2024, 2) == (2024, 2, 29)
    assert engine.last_day_of_month(2023, 2) == (2023, 2, 28)


def test_weekday_count_in_month():
    assert engine.weekday_count_in_month(2026, 2, 0) == 4  # Mondays in Feb 2026
    assert engine.weekday_count_in_month(2036, 5, 3) == 5  # Thursdays in May 2036


def test_nth_weekday_of_month_matches_spec_example():
    assert engine.nth_weekday_of_month(2036, 5, 3, 4) == (2036, 5, 22)


def test_nth_weekday_of_month_last():
    assert engine.nth_weekday_of_month(2026, 10, 6, -1) == (2026, 10, 25)


def test_nth_weekday_of_month_out_of_range_raises():
    with pytest.raises(ValueError):
        engine.nth_weekday_of_month(2026, 2, 0, 5)  # only 4 Mondays in Feb 2026


@pytest.mark.parametrize(
    "year, expected",
    [
        (2024, (2024, 3, 31)),
        (2025, (2025, 4, 20)),
        (2026, (2026, 4, 5)),
        (2027, (2027, 3, 28)),
        (2028, (2028, 4, 16)),
        (2000, (2000, 4, 23)),
        (2100, (2100, 3, 28)),
        (2038, (2038, 4, 25)),
        (1583, (1583, 4, 10)),
        (1961, (1961, 4, 2)),
    ],
)
def test_easter_matches_known_reference_dates(year, expected):
    assert engine.easter(year) == expected


def test_easter_is_always_a_sunday():
    for year in range(1583, 2200, 7):
        y, m, d = engine.easter(year)
        assert engine.weekday(y, m, d) == 6
