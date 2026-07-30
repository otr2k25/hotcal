import pytest

from hotcal.calc import CalcExpr, LiteralDate, parse_calculation
from hotcal.parser import ParseError, RelativeExpr


def test_last_day_of_month_bare():
    assert parse_calculation("last day of month") == CalcExpr("last_day_of_month")


def test_last_day_of_month_with_month_and_year():
    expr = parse_calculation("last day of month in february 2028")
    assert expr == CalcExpr("last_day_of_month", month=2, year=2028)


def test_nth_weekday_of_month():
    expr = parse_calculation("fourth thursday in may 2036")
    assert expr == CalcExpr("nth_weekday_of_month", weekday=3, month=5, year=2036, n=4)


def test_first_weekday_of_month_no_year():
    expr = parse_calculation("first monday in april")
    assert expr == CalcExpr("nth_weekday_of_month", weekday=0, month=4, year=None, n=1)


def test_last_weekday_of_month():
    expr = parse_calculation("last sunday in october")
    assert expr == CalcExpr("nth_weekday_of_month", weekday=6, month=10, year=None, n=-1)


def test_weekday_verb_with_literal_date():
    expr = parse_calculation("weekday 31.12.2564")
    assert expr == CalcExpr("passthrough", target=LiteralDate(2564, 12, 31))


def test_weekday_verb_with_relative_expr():
    expr = parse_calculation("weekday tomorrow")
    assert expr == CalcExpr("passthrough", target=RelativeExpr("tomorrow"))


def test_day_of_year_verb():
    expr = parse_calculation("day of year today")
    assert expr == CalcExpr("passthrough", target=RelativeExpr("today"))


def test_bare_relative_expression_is_not_a_calculation():
    assert parse_calculation("next monday") is None
    assert parse_calculation("two days ago") is None
    assert parse_calculation("today") is None


def test_unrecognized_month_raises():
    with pytest.raises(ParseError, match="unrecognized month"):
        parse_calculation("fourth thursday in mayo 2036")


def test_missing_in_or_of_raises():
    with pytest.raises(ParseError):
        parse_calculation("fourth thursday may 2036")


def test_bare_last_weekday_defers_to_relative_category():
    # "last friday" (no month) must NOT be claimed by the Calculation grammar.
    assert parse_calculation("last friday") is None
    assert parse_calculation("last monday") is None


def test_day_of_month_word_ordinal_with_of():
    expr = parse_calculation("third of march")
    assert expr == CalcExpr("day_of_month", month=3, day=3, year=None)


def test_day_of_month_word_ordinal_first():
    expr = parse_calculation("first of may")
    assert expr == CalcExpr("day_of_month", month=5, day=1, year=None)


def test_day_of_month_beyond_fifth_word_ordinal():
    expr = parse_calculation("twenty-second of march")
    assert expr == CalcExpr("day_of_month", month=3, day=22, year=None)


def test_day_of_month_numeral_suffix_with_year():
    expr = parse_calculation("22nd august 1932")
    assert expr == CalcExpr("day_of_month", month=8, day=22, year=1932)


def test_day_of_month_bare_cardinal_with_year():
    expr = parse_calculation("15 january 2067")
    assert expr == CalcExpr("day_of_month", month=1, day=15, year=2067)


def test_day_of_month_bare_cardinal_written_word():
    expr = parse_calculation("fifteen january 2067")
    assert expr == CalcExpr("day_of_month", month=1, day=15, year=2067)


def test_day_of_month_accepts_in_connector_too():
    expr = parse_calculation("third in march")
    assert expr == CalcExpr("day_of_month", month=3, day=3, year=None)


def test_day_of_month_defers_when_no_month_follows():
    # These are malformed Relative expressions, not day-of-month ones — must
    # not be claimed here, so the caller falls back to the Relative parser.
    assert parse_calculation("5 days ago") is None
    assert parse_calculation("twenty weeks ago") is None
    assert parse_calculation("in three weeks") is None


def test_day_of_month_rejects_mismatched_ordinal_suffix():
    # "22nd" is correct, "22th" isn't a recognized token at all.
    assert parse_calculation("22th august 1932") is None


def test_day_of_month_rejects_out_of_range_day():
    assert parse_calculation("35th of march") is None
