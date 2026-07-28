import datetime

from hotcal import cli, render


def _freeze(monkeypatch, y, m, d):
    fixed = datetime.date(y, m, d)

    class FakeDate(datetime.date):
        @classmethod
        def today(cls):
            return fixed

    monkeypatch.setattr(datetime, "date", FakeDate)


def test_no_args_shows_current_month_with_today_highlighted(monkeypatch, capsys):
    _freeze(monkeypatch, 2026, 7, 27)
    assert cli.main([]) == 0
    out = capsys.readouterr().out
    assert out.rstrip("\n") == render.render_month(2026, 7, highlight_day=27, color=False)


def test_relative_expression_highlights_resolved_date(monkeypatch, capsys):
    _freeze(monkeypatch, 2026, 7, 27)
    assert cli.main(["next", "monday"]) == 0
    out = capsys.readouterr().out
    assert out.rstrip("\n") == render.render_month(2026, 8, highlight_day=3, color=False)


def test_n_flag_prints_date_string_instead_of_month_view(monkeypatch, capsys):
    _freeze(monkeypatch, 2026, 7, 27)
    assert cli.main(["-n", "tomorrow"]) == 0
    out = capsys.readouterr().out
    assert out.strip() == "28.07.2026"


def test_n_flag_bundled_into_one_argv_string_is_still_recognized(monkeypatch, capsys):
    # Regression: "-n" must be recognized even when the whole expression arrives
    # as a single argv element (e.g. a caller passing one quoted string),
    # rather than only when "-n" is its own separate argv entry.
    _freeze(monkeypatch, 2026, 7, 27)
    assert cli.main(["-n tomorrow"]) == 0
    out = capsys.readouterr().out
    assert out.strip() == "28.07.2026"


def test_without_n_flag_still_shows_month_view(monkeypatch, capsys):
    _freeze(monkeypatch, 2026, 7, 27)
    assert cli.main(["tomorrow"]) == 0
    out = capsys.readouterr().out
    assert out.rstrip("\n") == render.render_month(2026, 7, highlight_day=28, color=False)


def test_expression_bundled_into_one_argv_string_still_parses(monkeypatch, capsys):
    _freeze(monkeypatch, 2026, 7, 27)
    assert cli.main(["next monday"]) == 0
    out = capsys.readouterr().out
    assert out.rstrip("\n") == render.render_month(2026, 8, highlight_day=3, color=False)


def test_compound_offset_via_cli(monkeypatch, capsys):
    _freeze(monkeypatch, 2026, 7, 27)
    assert cli.main(["in", "two", "days", "and", "4", "weeks"]) == 0
    out = capsys.readouterr().out
    assert out.rstrip("\n") == render.render_month(2026, 8, highlight_day=26, color=False)


def test_invalid_expression_errors_to_stderr(capsys):
    assert cli.main(["cats"]) == 1
    err = capsys.readouterr().err
    assert err.strip() == 'Error: unrecognized word "cats" — not part of the supported vocabulary'


def test_date_is_no_longer_a_special_verb(monkeypatch, capsys):
    # "date" has no grammar meaning now; a bare "date" is just an unrecognized word.
    _freeze(monkeypatch, 2026, 7, 27)
    assert cli.main(["date", "today"]) == 1
    err = capsys.readouterr().err
    assert 'unrecognized word "date"' in err


def test_holiday_expressions_via_cli(monkeypatch, capsys):
    _freeze(monkeypatch, 2026, 7, 27)
    assert cli.main(["-n", "christmas"]) == 0
    assert capsys.readouterr().out.strip() == "25.12.2026"

    assert cli.main(["-n", "easter"]) == 0
    assert capsys.readouterr().out.strip() == "28.03.2027"

    assert cli.main(["-n", "new", "year"]) == 0
    assert capsys.readouterr().out.strip() == "01.01.2027"

    assert cli.main(["-n", "christmas", "2030"]) == 0
    assert capsys.readouterr().out.strip() == "25.12.2030"


def test_before_after_expressions_via_cli(monkeypatch, capsys):
    _freeze(monkeypatch, 2026, 7, 28)
    assert cli.main(["-n", "3", "days", "before", "christmas"]) == 0
    assert capsys.readouterr().out.strip() == "22.12.2026"

    assert cli.main(["-n", "2", "weeks", "after", "easter"]) == 0
    assert capsys.readouterr().out.strip() == "11.04.2027"

    assert cli.main(["-n", "10", "days", "before", "25.12.2026"]) == 0
    assert capsys.readouterr().out.strip() == "15.12.2026"

    assert cli.main(["-n", "5", "days", "before", "fourth", "thursday", "in", "may", "2036"]) == 0
    assert capsys.readouterr().out.strip() == "17.05.2036"


def test_before_after_month_view_highlights_resolved_date(monkeypatch, capsys):
    _freeze(monkeypatch, 2026, 7, 28)
    assert cli.main(["3", "days", "before", "christmas"]) == 0
    out = capsys.readouterr().out
    assert out.rstrip("\n") == render.render_month(2026, 12, highlight_day=22, color=False)
