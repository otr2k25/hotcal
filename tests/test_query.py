import pytest

from hotcal import query
from hotcal.parser import parse_relative

TODAY = (2026, 7, 27)  # a Monday, per CLAUDE.md's currentDate context


@pytest.mark.parametrize(
    "text, expected",
    [
        ("today", (2026, 7, 27)),
        ("tomorrow", (2026, 7, 28)),
        ("yesterday", (2026, 7, 26)),
        ("next monday", (2026, 8, 3)),
        ("last friday", (2026, 7, 24)),
        ("two days ago", (2026, 7, 25)),
        ("in three weeks", (2026, 8, 17)),
        ("100 years ago", (1926, 7, 27)),
        ("monday in three weeks", (2026, 8, 17)),
        ("in 8 months", (2027, 3, 27)),
    ],
)
def test_resolve(text, expected):
    expr = parse_relative(text)
    assert query.resolve(expr, TODAY) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("in two days and 4 weeks", (2026, 8, 26)),
        ("two days and one week ago", (2026, 7, 18)),
        ("3 weeks and 2 days from now", (2026, 8, 19)),
    ],
)
def test_resolve_compound_offset(text, expected):
    from hotcal.parser import parse_relative
    assert query.resolve(parse_relative(text), TODAY) == expected
