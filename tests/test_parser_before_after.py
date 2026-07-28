import pytest

from hotcal.parser import ParseError, RelativeExpr, parse_relative


@pytest.mark.parametrize(
    "text, expected",
    [
        (
            "3 days before christmas",
            RelativeExpr("anchored_offset", terms=((-3, "days"),), anchor_text="christmas"),
        ),
        (
            "2 weeks after easter",
            RelativeExpr("anchored_offset", terms=((2, "weeks"),), anchor_text="easter"),
        ),
        (
            "10 days before 25.12.2026",
            RelativeExpr("anchored_offset", terms=((-10, "days"),), anchor_text="25.12.2026"),
        ),
        (
            "one month and ten days after next monday",
            RelativeExpr(
                "anchored_offset",
                terms=((1, "months"), (10, "days")),
                anchor_text="next monday",
            ),
        ),
        (
            "5 days before fourth thursday in may 2036",
            RelativeExpr("anchored_offset", terms=((-5, "days"),), anchor_text="fourth thursday in may 2036"),
        ),
        (
            "3 days before today",
            RelativeExpr("anchored_offset", terms=((-3, "days"),), anchor_text="today"),
        ),
        (
            # Bare "before"/"after" (no amount) defaults to 1 day — matches how a
            # human reads "what comes after next thursday" (the very next day).
            "after next thursday",
            RelativeExpr("anchored_offset", terms=((1, "days"),), anchor_text="next thursday"),
        ),
        (
            "before christmas",
            RelativeExpr("anchored_offset", terms=((-1, "days"),), anchor_text="christmas"),
        ),
    ],
)
def test_before_after_parsing(text, expected):
    assert parse_relative(text) == expected


def test_before_without_anchor_errors():
    with pytest.raises(ParseError):
        parse_relative("3 days before")


def test_before_with_malformed_amount_errors():
    with pytest.raises(ParseError):
        parse_relative("banana days before christmas")
