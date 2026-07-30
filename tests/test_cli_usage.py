import pytest

from hotcal import cli
from hotcal.names import MONTH_NAMES, WEEKDAY_NAMES


@pytest.mark.parametrize("flag", ["-h", "--help", "help", "HELP", "--Help"])
def test_help_flag_variants_exit_zero_and_print_usage(flag, capsys):
    assert cli.main([flag]) == 0
    out = capsys.readouterr().out
    assert "hotcal" in out
    assert "Usage" in out


def test_usage_lists_every_weekday_and_month(capsys):
    cli.main(["--help"])
    out = capsys.readouterr().out
    for weekday in WEEKDAY_NAMES:
        assert weekday in out
    for month in MONTH_NAMES:
        assert month in out


def test_usage_mentions_key_grammar_pieces(capsys):
    cli.main(["--help"])
    out = capsys.readouterr().out
    for fragment in ["-n", "ago", "before", "after", "christmas", "easter", "new year",
                      "last day of month", "weekday <date>", "day of year",
                      "Day-of-month expressions"]:
        assert fragment in out


def test_help_takes_precedence_over_expression_parsing(capsys):
    # A malformed/unrelated expression alongside --help should still show usage, not an error.
    assert cli.main(["--help", "cats"]) == 0
    out = capsys.readouterr().out
    assert "Usage" in out
