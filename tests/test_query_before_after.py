import pytest

from hotcal import query
from hotcal.parser import parse_relative

TODAY = (2026, 7, 28)  # a Tuesday


@pytest.mark.parametrize(
    "text, expected",
    [
        ("3 days before christmas", (2026, 12, 21)),
        ("2 weeks after easter", (2027, 4, 11)),
        ("10 days before 25.12.2026", (2026, 12, 15)),
        ("one month and ten days after next monday", (2026, 9, 13)),
        ("5 days before fourth thursday in may 2036", (2036, 5, 17)),
        ("3 days before today", (2026, 7, 25)),
        ("2 days after tomorrow", (2026, 7, 31)),
        # nested anchor: the anchor itself is another anchored_offset expression
        ("1 day after 3 days before christmas", (2026, 12, 22)),
        # bare before/after (no amount) defaults to 1 day
        ("after next thursday", (2026, 7, 31)),  # next thursday (Jul 30) + 1 day = Friday Jul 31
        ("before next thursday", (2026, 7, 29)),
        ("after christmas", (2026, 12, 25)),
        ("before easter", (2027, 3, 27)),
    ],
)
def test_resolve_before_after(text, expected):
    expr = parse_relative(text)
    assert query.resolve(expr, TODAY) == expected


def test_resolve_text_handles_before_after_directly():
    assert query.resolve_text("3 days before christmas", TODAY) == (2026, 12, 21)
