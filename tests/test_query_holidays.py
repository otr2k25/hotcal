import pytest

from hotcal import query
from hotcal.parser import parse_relative


@pytest.mark.parametrize(
    "today, text, expected",
    [
        # "christmas eve"/"christmas day" are locale-independent, unlike bare
        # "christmas" (tested separately below).
        ((2026, 7, 27), "christmas eve", (2026, 12, 24)),
        ((2026, 12, 25), "christmas eve", (2027, 12, 24)),
        ((2026, 12, 24), "christmas eve", (2026, 12, 24)),
        ((2026, 7, 27), "christmas eve 2030", (2030, 12, 24)),
        ((2026, 7, 27), "christmas day", (2026, 12, 25)),
        ((2026, 12, 26), "christmas day", (2027, 12, 25)),
        ((2026, 12, 25), "christmas day", (2026, 12, 25)),
        ((2026, 7, 27), "christmas day 2030", (2030, 12, 25)),
        # New Year's Day of this year has (almost) always already passed.
        ((2026, 7, 27), "new year", (2027, 1, 1)),
        ((2026, 1, 1), "new year", (2026, 1, 1)),
        ((2025, 12, 31), "new year", (2026, 1, 1)),
        ((2026, 7, 27), "new year 2030", (2030, 1, 1)),
        # Easter 2026 (5 Apr) already passed by July -> Easter 2027.
        ((2026, 7, 27), "easter", (2027, 3, 28)),
        # Before Easter 2026 -> this year's.
        ((2026, 1, 1), "easter", (2026, 4, 5)),
        ((2026, 4, 5), "easter", (2026, 4, 5)),  # exactly on Easter
        ((2026, 7, 27), "easter 2028", (2028, 4, 16)),
    ],
)
def test_resolve_holidays(today, text, expected):
    expr = parse_relative(text)
    assert query.resolve(expr, today) == expected


@pytest.mark.parametrize(
    "country, expected_day",
    [
        ("DE", 24), ("AT", 24), ("CH", 24), ("NO", 24), ("SE", 24), ("FI", 24),
        ("US", 25), ("GB", 25), ("FR", 25), ("ES", 25), ("IT", 25),
        (None, 25),  # locale undetected -> default
        ("ZZ", 25),  # unrecognized country -> default
    ],
)
def test_locale_christmas_day(monkeypatch, country, expected_day):
    monkeypatch.setattr(query.dateformat, "country_code", lambda: country)
    assert query._locale_christmas_day() == expected_day


@pytest.mark.parametrize(
    "country, today, expected",
    [
        ("DE", (2026, 7, 27), (2026, 12, 24)),
        ("US", (2026, 7, 27), (2026, 12, 25)),
        (None, (2026, 7, 27), (2026, 12, 25)),
    ],
)
def test_resolve_bare_christmas_depends_on_locale(monkeypatch, country, today, expected):
    monkeypatch.setattr(query.dateformat, "country_code", lambda: country)
    expr = parse_relative("christmas")
    assert query.resolve(expr, today) == expected
