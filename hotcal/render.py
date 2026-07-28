"""Compact cal/ncal-style month view. No calendar arithmetic lives here."""

import math
import sys

from . import engine
from .names import MONTH_NAMES

WEEKDAY_HEADER = "Mo Tu We Th Fr Sa Su"

_REVERSE_VIDEO = "\x1b[7m"
_RESET = "\x1b[0m"


def render_month(year: int, month: int, highlight_day: int | None = None, *, color: bool | None = None) -> str:
    if color is None:
        color = sys.stdout.isatty()

    width = len(WEEKDAY_HEADER)
    title = f"{MONTH_NAMES[month - 1]} {year}"
    leading = math.ceil((width - len(title)) / 2)
    lines = [" " * leading + title, "", WEEKDAY_HEADER, ""]

    start = engine.first_weekday_of_month(year, month)
    total_days = engine.days_in_month(year, month)

    cells: list[int | None] = [None] * start + list(range(1, total_days + 1))
    while len(cells) % 7:
        cells.append(None)

    for week_start in range(0, len(cells), 7):
        rendered = []
        for day in cells[week_start:week_start + 7]:
            if day is None:
                rendered.append("  ")
            else:
                text = f"{day:2d}"
                if day == highlight_day and color:
                    text = f"{_REVERSE_VIDEO}{text}{_RESET}"
                rendered.append(text)
        lines.append(" ".join(rendered).rstrip())

    return "\n".join(lines)
