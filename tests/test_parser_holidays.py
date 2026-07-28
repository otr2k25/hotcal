import pytest

from hotcal.parser import ParseError, RelativeExpr, parse_relative


@pytest.mark.parametrize(
    "text, expected",
    [
        ("christmas", RelativeExpr("christmas")),
        ("Christmas", RelativeExpr("christmas")),
        ("christmas 2030", RelativeExpr("christmas", year=2030)),
        ("easter", RelativeExpr("easter")),
        ("easter 2028", RelativeExpr("easter", year=2028)),
        ("new year", RelativeExpr("new_year")),
        ("new year 2030", RelativeExpr("new_year", year=2030)),
    ],
)
def test_holiday_parsing(text, expected):
    assert parse_relative(text) == expected


def test_christmas_with_garbage_trailing_word_errors():
    with pytest.raises(ParseError):
        parse_relative("christmas soon")


def test_new_without_year_errors():
    with pytest.raises(ParseError):
        parse_relative("new")


def test_new_year_with_garbage_trailing_word_errors():
    with pytest.raises(ParseError):
        parse_relative("new year soonish")
