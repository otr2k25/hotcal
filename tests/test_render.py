from hotcal import render


def test_render_month_matches_spec_example():
    # Exact layout from CLAUDE.md's "Calendar Rendering" example.
    expected = (
        "      July 2026\n"
        "\n"
        "Mo Tu We Th Fr Sa Su\n"
        "\n"
        "       1  2  3  4  5\n"
        " 6  7  8  9 10 11 12\n"
        "13 14 15 16 17 18 19\n"
        "20 21 22 23 24 25 26\n"
        "27 28 29 30 31"
    )
    assert render.render_month(2026, 7, color=False) == expected


def test_highlight_uses_reverse_video_when_color_enabled():
    out = render.render_month(2026, 7, highlight_day=27, color=True)
    assert "\x1b[7m27\x1b[0m" in out


def test_no_escape_codes_when_color_disabled():
    out = render.render_month(2026, 7, highlight_day=27, color=False)
    assert "\x1b[" not in out
    assert "27" in out


def test_month_starting_on_monday_has_no_leading_blank():
    # August 2026 starts on a Saturday; February 2027 starts on a Monday.
    out = render.render_month(2027, 2, color=False)
    first_row = out.splitlines()[4]
    assert first_row.startswith(" 1")


def test_highlight_day_outside_month_is_ignored():
    out = render.render_month(2026, 7, highlight_day=99, color=True)
    assert "\x1b[" not in out
