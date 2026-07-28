import pytest

from hotcal import engine


@pytest.mark.parametrize(
    "year, expected",
    [
        (2000, True),   # divisible by 400
        (1900, False),  # divisible by 100, not 400
        (2024, True),   # divisible by 4
        (2023, False),
        (2400, True),
        (1600, True),
        (100, False),
        (4, True),
    ],
)
def test_is_leap_year(year, expected):
    assert engine.is_leap_year(year) is expected


def test_days_in_month_february():
    assert engine.days_in_month(2024, 2) == 29
    assert engine.days_in_month(2023, 2) == 28
    assert engine.days_in_month(1900, 2) == 28
    assert engine.days_in_month(2000, 2) == 29


def test_days_in_month_regular():
    assert engine.days_in_month(2026, 7) == 31
    assert engine.days_in_month(2026, 4) == 30


@pytest.mark.parametrize(
    "year, month, day, expected_weekday",
    [
        (1, 1, 1, 0),        # 0001-01-01 is a Monday (proleptic Gregorian)
        (2000, 1, 1, 5),     # known reference: Saturday
        (2026, 7, 1, 2),     # matches CLAUDE.md example: Wednesday
        (2026, 7, 27, 0),    # today, per CLAUDE.md currentDate context: Monday
        (1582, 10, 15, 4),   # Gregorian calendar start date (proleptic): Friday
        (2564, 12, 31, 0),   # CLAUDE.md weekday example date: Monday
    ],
)
def test_weekday(year, month, day, expected_weekday):
    assert engine.weekday(year, month, day) == expected_weekday


def test_weekday_matches_datetime_within_supported_range():
    import datetime

    for year, month, day in [(2026, 7, 27), (1999, 12, 31), (2100, 3, 1), (1, 1, 1), (9999, 12, 31)]:
        d = datetime.date(year, month, day)
        assert engine.weekday(year, month, day) == d.weekday()


def test_ordinal_is_monotonic_across_year_boundary():
    assert engine.ordinal(2025, 12, 31) + 1 == engine.ordinal(2026, 1, 1)


def test_days_in_month_rejects_invalid_month():
    with pytest.raises(ValueError):
        engine.days_in_month(2026, 13)


def test_ordinal_rejects_invalid_day():
    with pytest.raises(ValueError):
        engine.ordinal(2026, 2, 30)
