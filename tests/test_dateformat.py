import locale

import pytest

from hotcal import dateformat


@pytest.mark.parametrize(
    "d_fmt, expected_order, expected_sep",
    [
        ("%d.%m.%Y", "dmy", "."),   # de_DE
        ("%m/%d/%Y", "mdy", "/"),   # en_US
        ("%Y-%m-%d", "ymd", "-"),   # many ISO-preferring locales
        ("%d/%m/%y", "dmy", "/"),
    ],
)
def test_detect_order_and_separator_from_various_locales(monkeypatch, d_fmt, expected_order, expected_sep):
    monkeypatch.setattr(locale, "nl_langinfo", lambda _: d_fmt, raising=False)
    monkeypatch.setattr(locale, "setlocale", lambda *a, **kw: None)
    assert dateformat._detect_order_and_separator() == (expected_order, expected_sep)


def test_detect_order_and_separator_falls_back_to_iso_when_unavailable(monkeypatch):
    def raise_error(*a, **kw):
        raise locale.Error("no locale")

    monkeypatch.setattr(locale, "setlocale", raise_error)
    assert dateformat._detect_order_and_separator() == ("ymd", "-")


def test_this_sandboxs_actual_locale_is_detected_correctly():
    # Smoke test against the real ambient locale (de_DE in this environment).
    order, sep = dateformat._detect_order_and_separator()
    assert (order, sep) == ("dmy", ".")


def test_parse_numeric_date_dmy():
    assert dateformat.parse_numeric_date("31.12.2564") == (2564, 12, 31)


def test_parse_numeric_date_iso_always_year_first():
    assert dateformat.parse_numeric_date("2026-07-27") == (2026, 7, 27)


def test_parse_numeric_date_accepts_slash_separator_too():
    assert dateformat.parse_numeric_date("27/07/2026") == (2026, 7, 27)


def test_parse_numeric_date_returns_none_for_non_date_shapes():
    assert dateformat.parse_numeric_date("hello") is None
    assert dateformat.parse_numeric_date("today") is None


def test_parse_numeric_date_rejects_invalid_month():
    # Invalid under both DD/MM and MM/DD readings, unlike "01.13.2026" (which
    # is only invalid as DD/MM but fine as MM/DD -> Jan 13).
    with pytest.raises(ValueError, match="month 13 does not exist"):
        dateformat.parse_numeric_date("13.13.2026")


def test_parse_numeric_date_rejects_invalid_day_matches_spec_example():
    with pytest.raises(ValueError, match=r'February 2026 has no 31st day'):
        dateformat.parse_numeric_date("31/02/2026")


def test_parse_numeric_date_prefers_locale_order_when_both_are_valid():
    # This sandbox's locale is dmy (de_DE): 07/04 is genuinely ambiguous
    # (day=7,month=4 and month=7,day=4 are both valid dates), so the
    # locale's own preference must win: day-first -> 4 April.
    assert dateformat.parse_numeric_date("07/04/2026") == (2026, 4, 7)


def test_parse_numeric_date_falls_back_to_other_order_when_preferred_is_invalid(monkeypatch):
    monkeypatch.setattr(dateformat, "_DAY_MONTH_ORDER", "dmy")
    monkeypatch.setattr(dateformat, "_ALT_DAY_MONTH_ORDER", "mdy")
    # 25 can't be a month, so this can only be MM/DD/YYYY -> Dec 25, even
    # though the locale prefers DD/MM/YYYY.
    assert dateformat.parse_numeric_date("12/25/2026") == (2026, 12, 25)


def test_parse_numeric_date_falls_back_the_other_direction_too(monkeypatch):
    monkeypatch.setattr(dateformat, "_DAY_MONTH_ORDER", "mdy")
    monkeypatch.setattr(dateformat, "_ALT_DAY_MONTH_ORDER", "dmy")
    # Under an MM/DD/YYYY-preferring locale, 25/12/2026 can only be DD/MM/YYYY.
    assert dateformat.parse_numeric_date("25/12/2026") == (2026, 12, 25)


def test_format_date_matches_detected_order():
    assert dateformat.format_date(2036, 5, 22) == "22.05.2036"


def test_format_date_defaults_to_iso_when_order_is_ymd(monkeypatch):
    monkeypatch.setattr(dateformat, "_ORDER", "ymd")
    monkeypatch.setattr(dateformat, "_SEPARATOR", "-")
    assert dateformat.format_date(2036, 5, 22) == "2036-05-22"


@pytest.mark.parametrize(
    "locale_name, expected",
    [
        ("de_DE", "DE"),
        ("en_US", "US"),
        ("fr_FR.UTF-8", "FR"),
        ("C", None),  # no country component
        (None, None),  # locale.getlocale() returned nothing
    ],
)
def test_country_code_from_various_locales(monkeypatch, locale_name, expected):
    monkeypatch.setattr(locale, "setlocale", lambda *a, **kw: None)
    monkeypatch.setattr(locale, "getlocale", lambda *a, **kw: (locale_name, "UTF-8") if locale_name else (None, None))
    assert dateformat.country_code() == expected


def test_country_code_falls_back_when_unavailable(monkeypatch):
    def raise_error(*a, **kw):
        raise locale.Error("no locale")

    monkeypatch.setattr(locale, "setlocale", raise_error)
    assert dateformat.country_code() is None


def test_this_sandboxs_actual_country_code_is_detected_correctly():
    assert dateformat.country_code() == "DE"
