"""Natural-language parser for the Calculation expression category.

Recognizes month-anchored calculations (`last day of month`,
`fourth thursday in may 2036`, `last sunday in october`), day-of-month
literals spelled in natural language (`third of march`, `22nd august 1932`,
`15 january 2067`), and the `weekday <date>` / `day of year <date>` forms.
Presence of an explicit month name is what distinguishes these from the
Relative category's bare `next monday` / `last friday`.
"""

import re
from dataclasses import dataclass

from . import dateformat
from .names import MONTH_NUMBERS, WEEKDAY_NUMBERS
from .parser import ParseError, RelativeExpr, parse_number, parse_relative

ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5}

# Day-of-month words, 1st-31st — used only for the day-of-month grammar
# below, so kept separate from ORDINALS (nth-weekday occurrences, capped at
# 5 per month).
_DAY_ORDINAL_WORDS = {
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
    "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
    "eleventh": 11, "twelfth": 12, "thirteenth": 13, "fourteenth": 14,
    "fifteenth": 15, "sixteenth": 16, "seventeenth": 17, "eighteenth": 18,
    "nineteenth": 19, "twentieth": 20, "twenty-first": 21, "twenty-second": 22,
    "twenty-third": 23, "twenty-fourth": 24, "twenty-fifth": 25,
    "twenty-sixth": 26, "twenty-seventh": 27, "twenty-eighth": 28,
    "twenty-ninth": 29, "thirtieth": 30, "thirty-first": 31,
}

_DAY_ORDINAL_SUFFIX_RE = re.compile(r"(\d{1,2})(st|nd|rd|th)")


@dataclass(frozen=True)
class LiteralDate:
    year: int
    month: int
    day: int


DateArg = LiteralDate | RelativeExpr


@dataclass(frozen=True)
class CalcExpr:
    kind: str  # last_day_of_month | nth_weekday_of_month | day_of_month | passthrough
    year: int | None = None
    month: int | None = None
    weekday: int | None = None
    n: int | None = None
    day: int | None = None
    target: DateArg | None = None


def parse_date_arg(tokens: list[str]) -> DateArg:
    """Parse a single date argument: either a numeric literal or a Relative expression."""
    if len(tokens) == 1:
        try:
            literal = dateformat.parse_numeric_date(tokens[0])
        except ValueError as e:
            raise ParseError(str(e)) from e
        if literal is not None:
            return LiteralDate(*literal)
    return parse_relative(" ".join(tokens))


def _parse_optional_year(tokens: list[str]) -> int | None:
    if not tokens:
        return None
    if len(tokens) == 1 and tokens[0].isdigit():
        return int(tokens[0])
    raise ParseError(f'"{" ".join(tokens)}" is not a valid year — expected a bare number')


def parse_calculation(text: str) -> CalcExpr | None:
    """Returns None if `text` doesn't match any Calculation pattern at all
    (so the caller can fall back to the Relative parser), or a CalcExpr if it
    does. Raises ParseError if it matches a pattern's skeleton but a
    component (month name, weekday count, ...) is invalid.
    """
    tokens = text.strip().lower().split()
    if not tokens:
        return None

    if tokens[0] == "weekday" or tokens[:3] == ["day", "of", "year"]:
        rest = tokens[1:] if tokens[0] == "weekday" else tokens[3:]
        if not rest:
            raise ParseError(f'"{text}" is missing a date — expected e.g. "weekday 31.12.2564"')
        return CalcExpr("passthrough", target=parse_date_arg(rest))

    if tokens[:4] == ["last", "day", "of", "month"]:
        rest = tokens[4:]
        month, year = None, None
        if rest:
            if rest[0] not in ("in", "of"):
                raise ParseError(f'unrecognized word "{rest[0]}" — expected "in" or "of" before a month name')
            if len(rest) < 2 or rest[1] not in MONTH_NUMBERS:
                word = rest[1] if len(rest) > 1 else ""
                raise ParseError(f'unrecognized month "{word}" — not part of the supported vocabulary')
            month = MONTH_NUMBERS[rest[1]]
            year = _parse_optional_year(rest[2:])
        return CalcExpr("last_day_of_month", month=month, year=year)

    # Only claim these as Calculation when a month follows ("last friday in october"). A
    # bare "last friday" (2 tokens) is the Relative category's "last <weekday>" instead —
    # defer to it by returning None rather than hard-erroring here.
    if tokens[0] == "last" and len(tokens) > 2 and tokens[1] in WEEKDAY_NUMBERS:
        return _parse_weekday_in_month(tokens, n=-1)

    if tokens[0] in ORDINALS and len(tokens) > 2 and tokens[1] in WEEKDAY_NUMBERS:
        return _parse_weekday_in_month(tokens, n=ORDINALS[tokens[0]])

    return _parse_day_of_month(tokens)


def _parse_day_number(tokens: list[str], start: int) -> tuple[int, int] | None:
    """Parse an ordinal or cardinal day-of-month number at `tokens[start]`.

    Accepts ordinal words ("third", "twenty-second"), numeral-suffix
    ordinals ("3rd", "22nd"), or cardinal numbers ("15", "fifteen").
    Returns (day, next_index), or None if `tokens[start]` isn't one of these.
    """
    token = tokens[start]
    if token in _DAY_ORDINAL_WORDS:
        return _DAY_ORDINAL_WORDS[token], start + 1

    match = _DAY_ORDINAL_SUFFIX_RE.fullmatch(token)
    if match is not None:
        day = int(match.group(1))
        if 1 <= day <= 31 and dateformat.ordinal_suffix(day) == match.group(2):
            return day, start + 1
        return None

    parsed = parse_number(tokens, start)
    if parsed is not None:
        day, idx = parsed
        if 1 <= day <= 31:
            return day, idx
    return None


def _parse_day_of_month(tokens: list[str]) -> CalcExpr | None:
    """Parse "<day> [in|of] <month> [<year>]", e.g. "third of march",
    "22nd august 1932", "15 january 2067". Returns None if `tokens` doesn't
    start with a day number immediately followed by a recognized month
    (with an optional "in"/"of" connector and optional year) — deferring to
    the Relative parser rather than committing to a diagnostic, since a bare
    number followed by a non-month word is more likely a malformed Relative
    expression (e.g. "5 days ago" with a typo) than a malformed date.
    """
    parsed_day = _parse_day_number(tokens, 0)
    if parsed_day is None:
        return None
    day, idx = parsed_day
    if idx < len(tokens) and tokens[idx] in ("in", "of"):
        idx += 1
    if idx >= len(tokens) or tokens[idx] not in MONTH_NUMBERS:
        return None
    month = MONTH_NUMBERS[tokens[idx]]
    year = _parse_optional_year(tokens[idx + 1:])
    return CalcExpr("day_of_month", month=month, day=day, year=year)


def _parse_weekday_in_month(tokens: list[str], n: int) -> CalcExpr:
    weekday = WEEKDAY_NUMBERS[tokens[1]]
    rest = tokens[2:]
    if not rest or rest[0] not in ("in", "of"):
        word = rest[0] if rest else ""
        raise ParseError(f'"{" ".join(tokens)}" is missing "in"/"of" before a month name near "{word}"')
    if len(rest) < 2 or rest[1] not in MONTH_NUMBERS:
        word = rest[1] if len(rest) > 1 else ""
        raise ParseError(f'unrecognized month "{word}" — not part of the supported vocabulary')
    month = MONTH_NUMBERS[rest[1]]
    year = _parse_optional_year(rest[2:])
    return CalcExpr("nth_weekday_of_month", weekday=weekday, month=month, year=year, n=n)
