"""Natural-language parser for the Relative expression category.

Turns English text into a RelativeExpr describing what to compute. No date
arithmetic happens here — that's the Calendar Query Model's job (query.py),
which turns a RelativeExpr into an actual (year, month, day) via the engine.
"""

from dataclasses import dataclass

from .names import WEEKDAY_NUMBERS as WEEKDAYS

_UNIT_ALIASES = {
    "day": "days", "days": "days",
    "week": "weeks", "weeks": "weeks",
    "month": "months", "months": "months",
    "year": "years", "years": "years",
}

_ONES = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19,
}

_TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}

_SCALES = {"hundred": 100}

_KEYWORDS = {
    "today", "now", "tomorrow", "yesterday", "next", "last", "ago", "in", "from", "and",
    "christmas", "easter", "new", "before", "after", "eve",
}

_HOLIDAY_KINDS = {"christmas": "christmas", "easter": "easter"}


class ParseError(Exception):
    """Carries a diagnostic message in the "<what> — <why>" form."""


@dataclass(frozen=True)
class RelativeExpr:
    kind: str  # today | tomorrow | yesterday | next_weekday | last_weekday | offset | compound_offset | weekday_in_offset | christmas | christmas_eve | christmas_day | easter | new_year | anchored_offset
    weekday: int | None = None
    amount: int | None = None
    unit: str | None = None
    terms: tuple[tuple[int, str], ...] | None = None  # for compound_offset/anchored_offset: [(signed_amount, unit), ...]
    year: int | None = None  # explicit year for holiday expressions, e.g. "christmas 2030"
    anchor_text: str | None = None  # for anchored_offset: the un-parsed anchor expression, e.g. "christmas"
    year_offset_text: str | None = None  # for holidays: which year, e.g. "in ten years" in "christmas in ten years"


def _is_known_word(word: str) -> bool:
    return (
        word.isdigit()
        or word in _ONES
        or word in _TENS
        or word in _SCALES
        or word in _UNIT_ALIASES
        or word in WEEKDAYS
        or word in _KEYWORDS
    )


def parse_number(tokens: list[str], start: int) -> tuple[int, int] | None:
    """Parse a run of number words/digits starting at `start`.

    Returns (value, next_index) or None if tokens[start] isn't a number.
    """
    if start >= len(tokens):
        return None
    if tokens[start].isdigit():
        return int(tokens[start]), start + 1
    if tokens[start] not in _ONES and tokens[start] not in _TENS:
        return None

    idx = start
    total = 0
    current = 0
    while idx < len(tokens):
        word = tokens[idx]
        if word in _ONES:
            current += _ONES[word]
            idx += 1
        elif word in _TENS:
            current += _TENS[word]
            idx += 1
        elif word in _SCALES:
            current = (current or 1) * _SCALES[word]
            total += current
            current = 0
            idx += 1
        else:
            break
    total += current
    return total, idx


def _parse_amount_unit(tokens: list[str]) -> tuple[int, str] | None:
    """Parse a full "<number> <unit>" phrase spanning all of `tokens`."""
    parsed = parse_number(tokens, 0)
    if parsed is None:
        return None
    amount, idx = parsed
    if idx != len(tokens) - 1:
        return None
    unit = _UNIT_ALIASES.get(tokens[idx])
    if unit is None:
        return None
    return amount, unit


def _parse_compound_amount_units(tokens: list[str]) -> list[tuple[int, str]] | None:
    """Parse "<n> <unit> [and <n> <unit>]*" spanning all of `tokens`."""
    segments: list[list[str]] = [[]]
    for tok in tokens:
        if tok == "and":
            segments.append([])
        else:
            segments[-1].append(tok)

    terms = []
    for segment in segments:
        parsed = _parse_amount_unit(segment)
        if parsed is None:
            return None
        terms.append(parsed)
    return terms


def _make_offset_expr(terms: list[tuple[int, str]], sign: int) -> RelativeExpr:
    signed = [(sign * amount, unit) for amount, unit in terms]
    if len(signed) == 1:
        amount, unit = signed[0]
        return RelativeExpr("offset", amount=amount, unit=unit)
    return RelativeExpr("compound_offset", terms=tuple(signed))


def _parse_holiday_year_suffix(text: str, tokens: list[str], rest: list[str]) -> tuple[int | None, str | None]:
    """What follows a holiday keyword: nothing, a literal year ("christmas
    2030"), or a Relative expression describing which year to shift to
    ("christmas in ten years"). Returns (literal_year, year_offset_text) —
    at most one of the two is set.
    """
    if not rest:
        return None, None
    if len(rest) == 1 and rest[0].isdigit():
        return int(rest[0]), None
    try:
        parse_relative(" ".join(rest))
    except ParseError:
        raise _unrecognized_error(text, tokens) from None
    return None, " ".join(rest)


def _unrecognized_error(text: str, tokens: list[str]) -> ParseError:
    for word in tokens:
        if not _is_known_word(word):
            return ParseError(f'unrecognized word "{word}" — not part of the supported vocabulary')
    return ParseError(f'"{text}" is not a recognized relative expression — check word order and units')


def parse_relative(text: str) -> RelativeExpr:
    tokens = text.strip().lower().split()
    if not tokens:
        raise ParseError("empty expression — expected a relative date expression")

    if tokens in (["today"], ["now"]):
        return RelativeExpr("today")
    if tokens == ["tomorrow"]:
        return RelativeExpr("tomorrow")
    if tokens == ["yesterday"]:
        return RelativeExpr("yesterday")

    if tokens[0] == "christmas" and len(tokens) >= 2 and tokens[1] in ("eve", "day"):
        kind = "christmas_eve" if tokens[1] == "eve" else "christmas_day"
        year, year_offset_text = _parse_holiday_year_suffix(text, tokens, tokens[2:])
        return RelativeExpr(kind, year=year, year_offset_text=year_offset_text)

    if tokens[0] in _HOLIDAY_KINDS:
        year, year_offset_text = _parse_holiday_year_suffix(text, tokens, tokens[1:])
        return RelativeExpr(_HOLIDAY_KINDS[tokens[0]], year=year, year_offset_text=year_offset_text)

    if tokens[0] == "new" and len(tokens) >= 2 and tokens[1] == "year":
        year, year_offset_text = _parse_holiday_year_suffix(text, tokens, tokens[2:])
        return RelativeExpr("new_year", year=year, year_offset_text=year_offset_text)

    if len(tokens) == 2 and tokens[0] == "next" and tokens[1] in WEEKDAYS:
        return RelativeExpr("next_weekday", weekday=WEEKDAYS[tokens[1]])
    if len(tokens) == 2 and tokens[0] == "last" and tokens[1] in WEEKDAYS:
        return RelativeExpr("last_weekday", weekday=WEEKDAYS[tokens[1]])

    keyword_idx = next((i for i, t in enumerate(tokens) if t in ("before", "after")), None)
    if keyword_idx is not None:
        anchor_tokens = tokens[keyword_idx + 1:]
        if not anchor_tokens:
            raise _unrecognized_error(text, tokens)
        amount_tokens = tokens[:keyword_idx]
        if amount_tokens:
            terms = _parse_compound_amount_units(amount_tokens)
            if terms is None:
                raise _unrecognized_error(text, tokens)
        else:
            # Bare "before X" / "after X" — a human means the very next/previous day.
            terms = [(1, "days")]
        sign = -1 if tokens[keyword_idx] == "before" else 1
        signed = tuple((sign * amount, unit) for amount, unit in terms)
        return RelativeExpr("anchored_offset", terms=signed, anchor_text=" ".join(anchor_tokens))

    if tokens[-1] == "ago":
        terms = _parse_compound_amount_units(tokens[:-1])
        if terms is not None:
            return _make_offset_expr(terms, sign=-1)
        raise _unrecognized_error(text, tokens)

    if tokens[0] == "in":
        terms = _parse_compound_amount_units(tokens[1:])
        if terms is not None:
            return _make_offset_expr(terms, sign=1)
        raise _unrecognized_error(text, tokens)

    if tokens[-2:] == ["from", "now"]:
        terms = _parse_compound_amount_units(tokens[:-2])
        if terms is not None:
            return _make_offset_expr(terms, sign=1)
        raise _unrecognized_error(text, tokens)

    if tokens[0] in WEEKDAYS and len(tokens) >= 2 and tokens[1] == "in":
        parsed = _parse_amount_unit(tokens[2:])
        if parsed is not None:
            amount, unit = parsed
            return RelativeExpr("weekday_in_offset", weekday=WEEKDAYS[tokens[0]], amount=amount, unit=unit)
        raise _unrecognized_error(text, tokens)

    raise _unrecognized_error(text, tokens)
