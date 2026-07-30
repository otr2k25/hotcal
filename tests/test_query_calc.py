import pytest

from hotcal import query
from hotcal.calc import parse_calculation
from hotcal.parser import ParseError

TODAY = (2026, 7, 27)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("fourth thursday in may 2036", (2036, 5, 22)),
        ("last sunday in october 2026", (2026, 10, 25)),
        ("last day of month in february 2028", (2028, 2, 29)),
        ("last day of month", (2026, 7, 31)),  # defaults to current month/year
        ("weekday 31.12.2564", (2564, 12, 31)),
        ("day of year today", TODAY),
        ("first monday in april", (2026, 4, 6)),  # defaults year to today's year
        ("third of march", (2026, 3, 3)),  # defaults year to today's year
        ("22nd august 1932", (1932, 8, 22)),
        ("15 january 2067", (2067, 1, 15)),
    ],
)
def test_resolve_calc(text, expected):
    expr = parse_calculation(text)
    assert query.resolve_calc(expr, TODAY, text) == expected


def test_invalid_day_of_month_raises_spec_diagnostic():
    text = "31st of february 2026"
    expr = parse_calculation(text)
    with pytest.raises(ParseError) as excinfo:
        query.resolve_calc(expr, TODAY, text)
    assert str(excinfo.value) == (
        f'invalid date "{text}" — February 2026 has no 31st day'
    )


def test_nonexistent_nth_weekday_raises_spec_diagnostic():
    text = "fifth monday in february 2026"
    expr = parse_calculation(text)
    with pytest.raises(ParseError) as excinfo:
        query.resolve_calc(expr, TODAY, text)
    assert str(excinfo.value) == (
        '"fifth monday in february 2026" does not exist — '
        "February 2026 has only 4 Mondays"
    )
