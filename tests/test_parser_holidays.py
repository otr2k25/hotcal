import pytest

from hotcal.parser import ParseError, RelativeExpr, parse_relative


@pytest.mark.parametrize(
    "text, expected",
    [
        ("christmas", RelativeExpr("christmas")),
        ("Christmas", RelativeExpr("christmas")),
        ("christmas 2030", RelativeExpr("christmas", year=2030)),
        ("christmas eve", RelativeExpr("christmas_eve")),
        ("christmas eve 2030", RelativeExpr("christmas_eve", year=2030)),
        ("christmas day", RelativeExpr("christmas_day")),
        ("christmas day 2030", RelativeExpr("christmas_day", year=2030)),
        ("easter", RelativeExpr("easter")),
        ("easter 2028", RelativeExpr("easter", year=2028)),
        ("new year", RelativeExpr("new_year")),
        ("new year 2030", RelativeExpr("new_year", year=2030)),
        ("christmas in ten years", RelativeExpr("christmas", year_offset_text="in ten years")),
        ("christmas eve in ten years", RelativeExpr("christmas_eve", year_offset_text="in ten years")),
        ("christmas day in ten years", RelativeExpr("christmas_day", year_offset_text="in ten years")),
        ("easter in three years", RelativeExpr("easter", year_offset_text="in three years")),
        ("new year in five years", RelativeExpr("new_year", year_offset_text="in five years")),
        ("christmas eve 3 years ago", RelativeExpr("christmas_eve", year_offset_text="3 years ago")),
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


def test_christmas_eve_with_garbage_year_errors():
    with pytest.raises(ParseError):
        parse_relative("christmas eve soon")


def test_christmas_day_with_garbage_year_errors():
    with pytest.raises(ParseError):
        parse_relative("christmas day soon")
