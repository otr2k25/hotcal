import pytest

from hotcal import query
from hotcal.parser import parse_relative


@pytest.mark.parametrize(
    "today, text, expected",
    [
        # Christmas hasn't happened yet this year -> this year's Christmas.
        ((2026, 7, 27), "christmas", (2026, 12, 25)),
        # Christmas already passed this year -> next year's.
        ((2026, 12, 26), "christmas", (2027, 12, 25)),
        # Exactly on Christmas -> today.
        ((2026, 12, 25), "christmas", (2026, 12, 25)),
        ((2026, 7, 27), "christmas 2030", (2030, 12, 25)),
        # New Year's Day of this year has (almost) always already passed.
        ((2026, 7, 27), "new year", (2027, 1, 1)),
        ((2026, 1, 1), "new year", (2026, 1, 1)),
        ((2025, 12, 31), "new year", (2026, 1, 1)),
        ((2026, 7, 27), "new year 2030", (2030, 1, 1)),
        # Easter 2026 (5 Apr) already passed by July -> Easter 2027.
        ((2026, 7, 27), "easter", (2027, 3, 28)),
        # Before Easter 2026 -> this year's.
        ((2026, 1, 1), "easter", (2026, 4, 5)),
        ((2026, 4, 5), "easter", (2026, 4, 5)),  # exactly on Easter
        ((2026, 7, 27), "easter 2028", (2028, 4, 16)),
    ],
)
def test_resolve_holidays(today, text, expected):
    expr = parse_relative(text)
    assert query.resolve(expr, today) == expected
