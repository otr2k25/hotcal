"""Locale-aware numeric date literal parsing and formatting.

Supports exactly the three formats named in CLAUDE.md: DD/MM/YYYY, MM/DD/YYYY,
YYYY-MM-DD. Which of DD/MM vs MM/DD applies (and the display separator) is
picked up from the system locale; a leading 4-digit group is always read as
YYYY-MM-DD regardless of locale, since that form is unambiguous.
"""

import locale
import re

from . import engine
from .names import MONTH_NAMES

_NUMERIC_DATE = re.compile(r"(\d{1,4})[./-](\d{1,4})[./-](\d{1,4})$")


def _detect_order_and_separator() -> tuple[str, str]:
    fmt = ""
    try:
        locale.setlocale(locale.LC_ALL, "")
        fmt = locale.nl_langinfo(locale.D_FMT)
    except (locale.Error, AttributeError):
        pass

    positions = []
    for token, code in (("%d", "d"), ("%m", "m")):
        idx = fmt.find(token)
        if idx != -1:
            positions.append((idx, code))
    y_idx = fmt.find("%Y")
    if y_idx == -1:
        y_idx = fmt.find("%y")
    if y_idx != -1:
        positions.append((y_idx, "y"))

    if len(positions) == 3:
        positions.sort()
        order = "".join(code for _, code in positions)
        separator = next((ch for ch in fmt if ch in "/.-"), "/")
        return order, separator

    return "dmy", "."


_ORDER, _SEPARATOR = _detect_order_and_separator()


def _ordinal_suffix(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def parse_numeric_date(token: str):
    """Parse a numeric date literal.

    Returns None if `token` isn't shaped like a numeric date at all (so the
    caller can try a different grammar). Raises ValueError with a
    human-readable reason if it looks like a date but the value is invalid.
    """
    match = _NUMERIC_DATE.fullmatch(token)
    if match is None:
        return None

    a, b, c = match.groups()
    if len(a) == 4:
        year, month, day = int(a), int(b), int(c)
    else:
        values = dict(zip(_ORDER, (int(a), int(b), int(c))))
        year, month, day = values["y"], values["m"], values["d"]

    if not 1 <= month <= 12:
        raise ValueError(f'invalid date "{token}" — month {month} does not exist')

    days = engine.days_in_month(year, month)
    if not 1 <= day <= days:
        raise ValueError(
            f'invalid date "{token}" — {MONTH_NAMES[month - 1]} {year} '
            f"has no {day}{_ordinal_suffix(day)} day"
        )

    return year, month, day


def format_date(year: int, month: int, day: int) -> str:
    parts = {"d": f"{day:02d}", "m": f"{month:02d}", "y": f"{year:04d}"}
    return _SEPARATOR.join(parts[code] for code in _ORDER)
