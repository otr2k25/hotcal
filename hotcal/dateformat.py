"""Locale-aware numeric date literal parsing and formatting.

Supports exactly the three formats named in CLAUDE.md: DD/MM/YYYY, MM/DD/YYYY,
YYYY-MM-DD. The locale's own order (DD/MM or MM/DD) is preferred both for
display and for resolving genuinely ambiguous input (e.g. "07/04/2026"), but
a literal that's only valid under the *other* order is still accepted — so
all three formats are parseable regardless of locale, not just the locale's
preferred one. A leading 4-digit group is always read as YYYY-MM-DD
regardless of locale, since that form is unambiguous. If the locale can't be
determined at all, formatting and the day/month tiebreak both default to
ISO 8601 (YYYY-MM-DD).
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

    return "ymd", "-"  # locale not detected -> default to ISO 8601


_ORDER, _SEPARATOR = _detect_order_and_separator()

# The locale's own day/month preference, used to resolve genuinely ambiguous
# 2-digit-first input (e.g. "07/04/2026"). "ymd" itself isn't a day/month
# preference — it only applies to the unambiguous 4-digit-year-first case —
# so when that's what we detected (a real ymd locale, or the no-locale
# fallback above), default the tiebreak to day-first, the more common
# convention outside the US.
_DAY_MONTH_ORDER = _ORDER if _ORDER in ("dmy", "mdy") else "dmy"
_ALT_DAY_MONTH_ORDER = "mdy" if _DAY_MONTH_ORDER == "dmy" else "dmy"


def country_code() -> str | None:
    """The system locale's ISO 3166-1 country code (e.g. "DE" for de_DE), or
    None if it can't be determined."""
    try:
        locale.setlocale(locale.LC_ALL, "")
        name, _ = locale.getlocale()
    except (locale.Error, AttributeError, ValueError):
        return None
    if not name or "_" not in name:
        return None
    return name.split("_", 1)[1].split(".", 1)[0].upper() or None


def ordinal_suffix(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def is_valid_date(year: int, month: int, day: int) -> bool:
    if not 1 <= month <= 12:
        return False
    return 1 <= day <= engine.days_in_month(year, month)


def invalid_date_error(token: str, year: int, month: int, day: int) -> ValueError:
    if not 1 <= month <= 12:
        return ValueError(f'invalid date "{token}" — month {month} does not exist')
    days = engine.days_in_month(year, month)
    return ValueError(
        f'invalid date "{token}" — {MONTH_NAMES[month - 1]} {year} '
        f"has no {day}{ordinal_suffix(day)} day"
    )


def parse_numeric_date(token: str):
    """Parse a numeric date literal.

    Returns None if `token` isn't shaped like a numeric date at all (so the
    caller can try a different grammar). Raises ValueError with a
    human-readable reason if it looks like a date but the value is invalid.

    A leading 4-digit group is always YYYY-MM-DD (unambiguous). Otherwise the
    locale's preferred day/month order is tried first; if that's invalid but
    the *other* order is a valid date, that's used instead — so e.g. a
    DD/MM/YYYY-only date still parses correctly even under an MM/DD/YYYY
    locale, and vice versa.
    """
    match = _NUMERIC_DATE.fullmatch(token)
    if match is None:
        return None

    a, b, c = match.groups()
    if len(a) == 4:
        year, month, day = int(a), int(b), int(c)
        if not is_valid_date(year, month, day):
            raise invalid_date_error(token, year, month, day)
        return year, month, day

    parts = (int(a), int(b), int(c))

    def build(order: str) -> tuple[int, int, int]:
        values = dict(zip(order, parts))
        return values["y"], values["m"], values["d"]

    preferred = build(_DAY_MONTH_ORDER)
    if is_valid_date(*preferred):
        return preferred

    alternate = build(_ALT_DAY_MONTH_ORDER)
    if is_valid_date(*alternate):
        return alternate

    raise invalid_date_error(token, *preferred)


def format_date(year: int, month: int, day: int) -> str:
    parts = {"d": f"{day:02d}", "m": f"{month:02d}", "y": f"{year:04d}"}
    return _SEPARATOR.join(parts[code] for code in _ORDER)
