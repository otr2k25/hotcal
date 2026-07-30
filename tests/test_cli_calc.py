import datetime

from hotcal import cli, render


def _freeze(monkeypatch, y, m, d):
    fixed = datetime.date(y, m, d)

    class FakeDate(datetime.date):
        @classmethod
        def today(cls):
            return fixed

    monkeypatch.setattr(datetime, "date", FakeDate)


def test_bare_literal_date_highlights_it(monkeypatch, capsys):
    _freeze(monkeypatch, 2026, 7, 27)
    assert cli.main(["31.12.2564"]) == 0
    out = capsys.readouterr().out
    assert out.rstrip("\n") == render.render_month(2564, 12, highlight_day=31, color=False)


def test_n_flag_prints_bare_literal_date_as_date_string(monkeypatch, capsys):
    _freeze(monkeypatch, 2026, 7, 27)
    assert cli.main(["-n", "31.12.2564"]) == 0
    out = capsys.readouterr().out
    assert out.strip() == "31.12.2564"


def test_n_flag_prints_nth_weekday_result_as_date_string(monkeypatch, capsys):
    _freeze(monkeypatch, 2026, 7, 27)
    assert cli.main(["-n", "fourth", "thursday", "in", "may", "2036"]) == 0
    out = capsys.readouterr().out
    assert out.strip() == "22.05.2036"


def test_nth_weekday_of_month_highlights_resolved_date(monkeypatch, capsys):
    _freeze(monkeypatch, 2026, 7, 27)
    assert cli.main(["last", "sunday", "in", "october", "2026"]) == 0
    out = capsys.readouterr().out
    assert out.rstrip("\n") == render.render_month(2026, 10, highlight_day=25, color=False)


def test_invalid_literal_date_errors(capsys):
    assert cli.main(["31/02/2026"]) == 1
    err = capsys.readouterr().err
    assert err.strip() == 'Error: invalid date "31/02/2026" — February 2026 has no 31st day'


def test_nonexistent_nth_weekday_errors(monkeypatch, capsys):
    _freeze(monkeypatch, 2026, 7, 27)
    assert cli.main(["fifth", "monday", "in", "february", "2026"]) == 1
    err = capsys.readouterr().err
    assert err.strip() == (
        'Error: "fifth monday in february 2026" does not exist — '
        "February 2026 has only 4 Mondays"
    )


def test_n_flag_prints_day_of_month_result_as_date_string(monkeypatch, capsys):
    _freeze(monkeypatch, 2026, 7, 27)
    assert cli.main(["-n", "22nd", "august", "1932"]) == 0
    out = capsys.readouterr().out
    assert out.strip() == "22.08.1932"


def test_day_of_month_without_year_highlights_current_year(monkeypatch, capsys):
    _freeze(monkeypatch, 2026, 7, 27)
    assert cli.main(["third", "of", "march"]) == 0
    out = capsys.readouterr().out
    assert out.rstrip("\n") == render.render_month(2026, 3, highlight_day=3, color=False)


def test_invalid_day_of_month_errors(monkeypatch, capsys):
    _freeze(monkeypatch, 2026, 7, 27)
    assert cli.main(["31st", "of", "february", "2026"]) == 1
    err = capsys.readouterr().err
    assert err.strip() == 'Error: invalid date "31st of february 2026" — February 2026 has no 31st day'
