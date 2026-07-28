"""Calendar Query Model — turns a parsed RelativeExpr into a concrete date.

Dispatches to the engine for every calculation; holds no arithmetic itself.
"""

from . import calc, dateformat, engine
from .calc import CalcExpr, LiteralDate
from .names import MONTH_NAMES, WEEKDAY_NAMES
from .parser import ParseError, RelativeExpr, parse_relative


def resolve_text(text: str, today: tuple[int, int, int]) -> tuple[int, int, int]:
    """Resolve any supported expression string to a date: a numeric date
    literal, a Calculation-category expression, or a Relative one. This is
    the single place that combines all three grammars, so anything that
    accepts "a date expression" as an argument (holiday years aside, that's
    `weekday <date>`, `day of year <date>`, and `before`/`after` anchors) goes
    through here rather than re-implementing the dispatch order.
    """
    tokens = text.split()
    if len(tokens) == 1:
        try:
            literal = dateformat.parse_numeric_date(tokens[0])
        except ValueError as e:
            raise ParseError(str(e)) from e
        if literal is not None:
            return literal

    calc_expr = calc.parse_calculation(text)
    if calc_expr is not None:
        return resolve_calc(calc_expr, today, text)
    relative_expr = parse_relative(text)
    return resolve(relative_expr, today)


def resolve_date_arg(arg, today: tuple[int, int, int]) -> tuple[int, int, int]:
    if isinstance(arg, LiteralDate):
        return (arg.year, arg.month, arg.day)
    return resolve(arg, today)


def resolve_calc(expr: CalcExpr, today: tuple[int, int, int], original_text: str) -> tuple[int, int, int]:
    year = expr.year if expr.year is not None else today[0]

    if expr.kind == "passthrough":
        return resolve_date_arg(expr.target, today)

    if expr.kind == "last_day_of_month":
        month = expr.month if expr.month is not None else today[1]
        return engine.last_day_of_month(year, month)

    if expr.kind == "nth_weekday_of_month":
        try:
            return engine.nth_weekday_of_month(year, expr.month, expr.weekday, expr.n)
        except ValueError:
            count = engine.weekday_count_in_month(year, expr.month, expr.weekday)
            weekday_name = WEEKDAY_NAMES[expr.weekday]
            month_name = MONTH_NAMES[expr.month - 1]
            raise ParseError(
                f'"{original_text}" does not exist — {month_name} {year} '
                f"has only {count} {weekday_name}s"
            ) from None

    raise AssertionError(f"unhandled calc expression kind {expr.kind!r}")


def resolve(expr: RelativeExpr, today: tuple[int, int, int]) -> tuple[int, int, int]:
    year, month, day = today

    if expr.kind == "today":
        return today
    if expr.kind == "tomorrow":
        return engine.add_days(year, month, day, 1)
    if expr.kind == "yesterday":
        return engine.add_days(year, month, day, -1)
    if expr.kind == "next_weekday":
        return engine.next_weekday(year, month, day, expr.weekday)
    if expr.kind == "last_weekday":
        return engine.last_weekday(year, month, day, expr.weekday)
    if expr.kind == "offset":
        return engine.add_offset(year, month, day, expr.amount, expr.unit)
    if expr.kind == "compound_offset":
        for amount, unit in expr.terms:
            year, month, day = engine.add_offset(year, month, day, amount, unit)
        return (year, month, day)
    if expr.kind == "weekday_in_offset":
        shifted = engine.add_offset(year, month, day, expr.amount, expr.unit)
        return engine.weekday_of_week(*shifted, expr.weekday)
    if expr.kind == "christmas":
        return _resolve_fixed_holiday(
            today, expr.year, expr.year_offset_text, month=12, day=_locale_christmas_day()
        )
    if expr.kind == "christmas_eve":
        return _resolve_fixed_holiday(today, expr.year, expr.year_offset_text, month=12, day=24)
    if expr.kind == "christmas_day":
        return _resolve_fixed_holiday(today, expr.year, expr.year_offset_text, month=12, day=25)
    if expr.kind == "new_year":
        return _resolve_fixed_holiday(today, expr.year, expr.year_offset_text, month=1, day=1)
    if expr.kind == "easter":
        return _resolve_easter(today, expr.year, expr.year_offset_text)
    if expr.kind == "anchored_offset":
        y, m, d = resolve_text(expr.anchor_text, today)
        for amount, unit in expr.terms:
            y, m, d = engine.add_offset(y, m, d, amount, unit)
        return (y, m, d)

    raise AssertionError(f"unhandled expression kind {expr.kind!r}")


# Countries where the main Christmas celebration is Dec 24 (Christmas Eve),
# not Dec 25. Unlike the rest of this engine, this list has no authoritative
# source — it's an approximation, scoped for now to Western/Christian-
# tradition countries (Europe + the Americas) with a well-established single
# convention. Genuinely mixed cases (e.g. much of Latin America) are left out
# rather than guessed at; they fall through to the Dec 25 default below.
_CHRISTMAS_EVE_COUNTRIES = frozenset({
    "DE", "AT", "CH", "LI",  # German-speaking
    "PL", "CZ", "SK", "HU", "SI",  # Central Europe
    "NO", "SE", "DK", "FI", "IS",  # Nordics
    "EE", "LV", "LT",  # Baltics
})


def _locale_christmas_day() -> int:
    """24 or 25, based on the system locale's country. Defaults to 25 if the
    locale is undetected or not in the table above."""
    country = dateformat.country_code()
    if country in _CHRISTMAS_EVE_COUNTRIES:
        return 24
    return 25


def _resolve_fixed_holiday(
    today: tuple[int, int, int],
    explicit_year: int | None,
    year_offset_text: str | None,
    month: int,
    day: int,
) -> tuple[int, int, int]:
    if explicit_year is not None:
        return (explicit_year, month, day)
    if year_offset_text is not None:
        shifted_year, _, _ = resolve_text(year_offset_text, today)
        return (shifted_year, month, day)
    candidate = (today[0], month, day)
    if candidate < today:
        candidate = (today[0] + 1, month, day)
    return candidate


def _resolve_easter(
    today: tuple[int, int, int], explicit_year: int | None, year_offset_text: str | None
) -> tuple[int, int, int]:
    if explicit_year is not None:
        return engine.easter(explicit_year)
    if year_offset_text is not None:
        shifted_year, _, _ = resolve_text(year_offset_text, today)
        return engine.easter(shifted_year)
    candidate = engine.easter(today[0])
    if candidate < today:
        candidate = engine.easter(today[0] + 1)
    return candidate
