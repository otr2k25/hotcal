import pytest

from hotcal.parser import ParseError, RelativeExpr, parse_relative


@pytest.mark.parametrize(
    "text, expected",
    [
        ("today", RelativeExpr("today")),
        ("now", RelativeExpr("today")),
        ("Today", RelativeExpr("today")),
        ("tomorrow", RelativeExpr("tomorrow")),
        ("yesterday", RelativeExpr("yesterday")),
        ("next monday", RelativeExpr("next_weekday", weekday=0)),
        ("last friday", RelativeExpr("last_weekday", weekday=4)),
        ("two days ago", RelativeExpr("offset", amount=-2, unit="days")),
        ("2 days ago", RelativeExpr("offset", amount=-2, unit="days")),
        ("100 years ago", RelativeExpr("offset", amount=-100, unit="years")),
        ("in three weeks", RelativeExpr("offset", amount=3, unit="weeks")),
        ("in 10 years", RelativeExpr("offset", amount=10, unit="years")),
        ("three weeks from now", RelativeExpr("offset", amount=3, unit="weeks")),
        ("monday in three weeks", RelativeExpr("weekday_in_offset", weekday=0, amount=3, unit="weeks")),
        ("twenty three days ago", RelativeExpr("offset", amount=-23, unit="days")),
        ("one hundred years ago", RelativeExpr("offset", amount=-100, unit="years")),
    ],
)
def test_valid_expressions(text, expected):
    assert parse_relative(text) == expected


def test_numeric_and_written_numbers_are_equivalent():
    assert parse_relative("2 days ago") == parse_relative("two days ago")
    assert parse_relative("in 3 weeks") == parse_relative("in three weeks")


def test_unrecognized_word_error_names_the_word():
    with pytest.raises(ParseError, match=r'unrecognized word "cats"'):
        parse_relative("cats")


def test_empty_expression_errors():
    with pytest.raises(ParseError):
        parse_relative("   ")


def test_malformed_but_all_known_words_errors():
    with pytest.raises(ParseError):
        parse_relative("ago two days")


def test_next_requires_a_weekday():
    with pytest.raises(ParseError):
        parse_relative("next today")
