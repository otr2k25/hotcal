"""Proleptic Gregorian calendar engine.

Pure integer arithmetic — no reliance on datetime's year-range limits,
so calculations remain valid for arbitrarily large years.
"""

_MONTH_LENGTHS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_DAYS_BEFORE_MONTH = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)


def is_leap_year(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def days_in_month(year: int, month: int) -> int:
    if not 1 <= month <= 12:
        raise ValueError(f"invalid month {month!r} — must be between 1 and 12")
    if month == 2 and is_leap_year(year):
        return 29
    return _MONTH_LENGTHS[month - 1]


def _days_before_year(year: int) -> int:
    y = year - 1
    return y * 365 + y // 4 - y // 100 + y // 400


def _days_before_month(year: int, month: int) -> int:
    if month > 2 and is_leap_year(year):
        return _DAYS_BEFORE_MONTH[month - 1] + 1
    return _DAYS_BEFORE_MONTH[month - 1]


def ordinal(year: int, month: int, day: int) -> int:
    """Days since 0001-01-01, counting 0001-01-01 itself as day 1."""
    if not 1 <= day <= days_in_month(year, month):
        raise ValueError(f"invalid date {year:04d}-{month:02d}-{day:02d}")
    return _days_before_year(year) + _days_before_month(year, month) + day


def weekday(year: int, month: int, day: int) -> int:
    """ISO weekday: 0=Monday ... 6=Sunday. 0001-01-01 is a Monday."""
    return (ordinal(year, month, day) - 1) % 7


def first_weekday_of_month(year: int, month: int) -> int:
    return weekday(year, month, 1)


def from_ordinal(n: int) -> tuple[int, int, int]:
    """Inverse of ordinal(): map days-since-epoch back to (year, month, day).

    Adapted from Howard Hinnant's civil_from_days algorithm, re-anchored to
    our own epoch via _days_before_year so it stays independent of datetime
    and its year-range limits.
    """
    z = (n - 1) - _days_before_year(1970) + 719468
    # Python's // already floors (unlike C's truncating division), so era
    # needs no extra adjustment for negative z here.
    era = z // 146097
    doe = z - era * 146097
    yoe = (doe - doe // 1460 + doe // 36524 - doe // 146096) // 365
    y = yoe + era * 400
    doy = doe - (365 * yoe + yoe // 4 - yoe // 100)
    mp = (5 * doy + 2) // 153
    d = doy - (153 * mp + 2) // 5 + 1
    m = mp + 3 if mp < 10 else mp - 9
    y += 1 if m <= 2 else 0
    return (y, m, d)


def add_days(year: int, month: int, day: int, delta: int) -> tuple[int, int, int]:
    return from_ordinal(ordinal(year, month, day) + delta)


def add_months(year: int, month: int, day: int, delta: int) -> tuple[int, int, int]:
    total = year * 12 + (month - 1) + delta
    new_year, new_month = total // 12, total % 12 + 1
    new_day = min(day, days_in_month(new_year, new_month))
    return (new_year, new_month, new_day)


def add_years(year: int, month: int, day: int, delta: int) -> tuple[int, int, int]:
    new_year = year + delta
    new_day = min(day, days_in_month(new_year, month))
    return (new_year, month, new_day)


def add_offset(year: int, month: int, day: int, amount: int, unit: str) -> tuple[int, int, int]:
    if unit == "days":
        return add_days(year, month, day, amount)
    if unit == "weeks":
        return add_days(year, month, day, amount * 7)
    if unit == "months":
        return add_months(year, month, day, amount)
    if unit == "years":
        return add_years(year, month, day, amount)
    raise ValueError(f"unknown unit {unit!r}")


def next_weekday(year: int, month: int, day: int, target: int) -> tuple[int, int, int]:
    """The next occurrence of weekday `target`, strictly after this date."""
    delta = (target - weekday(year, month, day)) % 7 or 7
    return add_days(year, month, day, delta)


def last_weekday(year: int, month: int, day: int, target: int) -> tuple[int, int, int]:
    """The most recent occurrence of weekday `target`, strictly before this date."""
    delta = (weekday(year, month, day) - target) % 7 or 7
    return add_days(year, month, day, -delta)


def weekday_of_week(year: int, month: int, day: int, target: int) -> tuple[int, int, int]:
    """The date of weekday `target` within the week containing this date."""
    return add_days(year, month, day, target - weekday(year, month, day))


def last_day_of_month(year: int, month: int) -> tuple[int, int, int]:
    return (year, month, days_in_month(year, month))


def weekday_count_in_month(year: int, month: int, target: int) -> int:
    """How many times weekday `target` occurs in this month."""
    first_occurrence = 1 + (target - weekday(year, month, 1)) % 7
    return (days_in_month(year, month) - first_occurrence) // 7 + 1


def nth_weekday_of_month(year: int, month: int, target: int, n: int) -> tuple[int, int, int]:
    """The nth occurrence of weekday `target` in this month (n=1..5), or n=-1 for the last."""
    if n == -1:
        last_day = days_in_month(year, month)
        delta = (weekday(year, month, last_day) - target) % 7
        return (year, month, last_day - delta)
    if n < 1:
        raise ValueError(f"invalid occurrence {n!r} — must be 1-5, or -1 for 'last'")
    first_occurrence = 1 + (target - weekday(year, month, 1)) % 7
    day = first_occurrence + (n - 1) * 7
    if day > days_in_month(year, month):
        raise ValueError(
            f"occurrence {n} of weekday {target} does not exist in {year:04d}-{month:02d}"
        )
    return (year, month, day)


def easter(year: int) -> tuple[int, int, int]:
    """Easter Sunday in the Gregorian calendar (Meeus/Jones/Butcher algorithm)."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = (h + l - 7 * m + 114) % 31 + 1
    return (year, month, day)
