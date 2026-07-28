import datetime
import sys

from . import dateformat, query, render
from .calc import ORDINALS
from .names import MONTH_NAMES, WEEKDAY_NAMES
from .parser import ParseError

_HELP_FLAGS = {"-h", "--help", "help"}


def _usage_text() -> str:
    weekdays = ", ".join(WEEKDAY_NAMES)
    months = ", ".join(MONTH_NAMES)
    ordinals = ", ".join(ORDINALS)
    return f"""hotcal — Human-Oriented Terminal Calendar

Usage:
  hotcal [-n] [<expression>]
  hotcal -h | --help | help

  (no expression)     show the current month, today highlighted
  -n                   print just the resolved date instead of a month view
  -h, --help, help     show this message

Relative expressions:
  today, now, tomorrow, yesterday
  next <weekday>                        last <weekday>
  <n> <unit> ago                        in <n> <unit>
  <n> <unit> from now
  <n> <unit> [and <n> <unit>]... before|after <expression>
  <weekday> in <n> <unit>               (e.g. "monday in three weeks")
  christmas [<year>], easter [<year>], new year [<year>]

Calculation expressions (require an explicit month):
  last day of month [in|of <month> [<year>]]
  <ordinal> <weekday> in|of <month> [<year>]
  last <weekday> in|of <month> [<year>]
  weekday <date>
  day of year <date>

Numeric date literals (order/separator per system locale):
  DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD   (e.g. 31.12.2564, 27/07/2026, 2026-07-27)

Vocabulary:
  Weekdays: {weekdays}
  Months:   {months}
  Ordinals: {ordinals}
  Units:    day(s), week(s), month(s), year(s)
  Numbers:  digits (2, 100) or written words (two, one hundred)

Examples:
  hotcal next monday
  hotcal -n fourth thursday in may 2036
  hotcal 3 days before christmas
  hotcal weekday 31.12.2564
"""


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    # Re-split on whitespace regardless of how the caller's shell tokenized
    # argv, so "-n" is recognized whether it arrives as its own argv element
    # or bundled into one quoted string with the rest of the expression.
    tokens = " ".join(argv).split()

    if any(t.lower() in _HELP_FLAGS for t in tokens):
        print(_usage_text())
        return 0

    as_date_output = "-n" in tokens
    tokens = [t for t in tokens if t != "-n"]

    today_date = datetime.date.today()
    today = (today_date.year, today_date.month, today_date.day)
    year, month, day = today

    if tokens:
        try:
            year, month, day = query.resolve_text(" ".join(tokens), today)
        except ParseError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    if as_date_output:
        print(dateformat.format_date(year, month, day))
    else:
        print(render.render_month(year, month, highlight_day=day))
    return 0
