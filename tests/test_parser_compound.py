import pytest

from hotcal.parser import ParseError, RelativeExpr, parse_relative


@pytest.mark.parametrize(
    "text, expected",
    [
        (
            "in two days and 4 weeks",
            RelativeExpr("compound_offset", terms=((2, "days"), (4, "weeks"))),
        ),
        (
            "two days and one week ago",
            RelativeExpr("compound_offset", terms=((-2, "days"), (-1, "weeks"))),
        ),
        (
            "3 weeks and 2 days from now",
            RelativeExpr("compound_offset", terms=((3, "weeks"), (2, "days"))),
        ),
    ],
)
def test_compound_offset_parsing(text, expected):
    assert parse_relative(text) == expected


def test_single_term_still_uses_simple_offset_kind():
    # No "and" present -> stays the plain "offset" kind (backward compatible).
    assert parse_relative("in three weeks") == RelativeExpr("offset", amount=3, unit="weeks")


def test_compound_offset_with_malformed_segment_errors():
    with pytest.raises(ParseError):
        parse_relative("in two days and banana weeks")
