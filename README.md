# hotcal — Human-Oriented Terminal Calendar

A terminal calendar that combines the visual simplicity of `cal`/`ncal` with
natural-language date reasoning. Instead of flags, you ask it about time in
plain English:

```
$ hotcal next monday
     August 2026

Mo Tu We Th Fr Sa Su

                1  2
 3  4  5  6  7  8  9
10 11 12 13 14 15 16
17 18 19 20 21 22 23
24 25 26 27 28 29 30
31
```

*(The `3` is highlighted in reverse video in an actual terminal — see the
note below the "Output" section on why these plain-text snippets can't show
that.)*

Two design goals drive everything: **absolute correctness** for Gregorian
calendar math (arbitrary years, exact leap-year rules, no shortcuts), and
**natural-language input** in place of an option-heavy CLI.

## Status

Early but functional. The Gregorian engine, rendering, and both of the
project's expression categories (Relative and Calculation) are built and
tested (191 tests, plus Hypothesis property tests for the engine). Not yet
built: a Difference category (`days/weeks/months/years between` — its output
shape is still an open design question, since a bare number isn't an allowed
output format). Verb-oriented commands (`show`, `goto`, etc.) were considered
and dropped from the spec entirely, since they'd hit the same output-format
problem.

## Install & run

Requires Python 3.11+. No third-party dependencies for the engine or
rendering; `pytest`/`hypothesis` are only needed to run the test suite.

```
pip install -e .
hotcal                  # or: python -m hotcal
```

(If `pip` isn't available, `uv run python -m hotcal ...` works without any
manual environment setup.)

## How it works

```
CLI → Natural Language Parser → Calendar Query Model → Gregorian Engine → Renderer
```

- The **engine** (`hotcal/engine.py`) does all date math with pure integer
  arithmetic — no `datetime`, so it isn't bound by `datetime`'s year 1–9999
  range. Leap years, weekdays, month/year arithmetic, nth-weekday-of-month,
  and Easter (Meeus/Jones/Butcher algorithm) all live here.
- The **parser** (`hotcal/parser.py`, `hotcal/calc.py`) turns English text
  into a small expression object. It never does date arithmetic itself.
- The **query model** (`hotcal/query.py`) turns that expression into a
  concrete `(year, month, day)` by calling the engine.
- The **renderer** (`hotcal/render.py`) draws the month grid. It never
  computes dates.

## Output

Only two output forms exist — no JSON, no bare numbers, no free text:

1. **Month view** (default) — a compact `cal`/`ncal`-style grid with the
   resolved date highlighted. The highlight is real terminal reverse video
   (`\x1b[7m...\x1b[0m`), applied only when stdout is a TTY — piped or
   captured output (like the code blocks in this README) gets the plain grid
   with no color codes at all, so wherever a grid appears below, a caption
   underneath it says which day would be highlighted.
2. **Date** — just the resolved date, in one of three formats
   (`DD/MM/YYYY`, `MM/DD/YYYY`, `YYYY-MM-DD`) chosen by your system locale.
   Triggered with `-n`.

```
$ hotcal -n next monday
03.08.2026
```

(Format above is `DD.MM.YYYY` because this system's locale is `de_DE`.)

Run `hotcal --help` (or `-h`, or bare `help`) for a full usage summary,
including every weekday/month name, ordinal, and unit the parser accepts.

## Vocabulary

Every expression belongs to exactly one of two categories. Mixing words from
different categories in one expression is an error.

### Relative category

Bare day references:

| Expression | Meaning |
|---|---|
| `today`, `now` | today |
| `tomorrow` | today + 1 day |
| `yesterday` | today − 1 day |

Weekday references (relative to today, no month involved) — any of the
seven weekday names works with both `next` and `last`:

```
next monday
last friday
```

Offsets — numeric or written numbers are interchangeable:

```
two days ago          in three weeks          3 weeks from now
2 days ago             in 3 weeks               three weeks from now
100 years ago          in 10 years
```

Compound offsets, joined with `and`:

```
in two days and 4 weeks
two days and one week ago
3 weeks and 2 days from now
```

Weekday within a shifted week:

```
monday in three weeks     # shift 3 weeks ahead, then find that week's Monday
friday in 2 weeks
```

Holidays — resolve to the nearest upcoming occurrence unless a year is given:

```
christmas              christmas 2030
christmas eve           christmas eve 2030
christmas day           christmas day 2030
easter                 easter 2028
new year               new year 2030
```

`christmas eve` is always December 24, `christmas day` is always December
25. Bare `christmas` picks between them based on the system locale's
country — Dec 24 for a set of Western/Christian-tradition countries where
Christmas Eve is the main celebration (Germany, Austria, Switzerland,
Poland, the Nordics, the Baltics, ...), Dec 25 everywhere else, including
when the locale can't be determined. This list has no authoritative source
and isn't exhaustive — see `hotcal/query.py`'s `_CHRISTMAS_EVE_COUNTRIES`.

The year for any holiday can also be given as a Relative expression instead
of a literal number — the holiday resolves in whichever year that
expression lands on:

```
christmas eve in ten years
easter in three years
new year 3 years ago
```

Offsets anchored to another expression, with `before`/`after` — the anchor
can be anything else in this vocabulary: today, another holiday, a weekday,
a literal date, or even a Calculation-category expression:

```
3 days before christmas
2 weeks after easter
10 days before 25.12.2026
one month and ten days after next monday
5 days before fourth thursday in may 2036
```

### Calculation category

These require an explicit month (that's what distinguishes them from the
Relative category's bare `next monday`/`last friday`):

```
last day of month
last day of month in february 2028

first monday in april
fourth thursday in may 2036
last sunday in october
last friday in december 2026
```

Weekday / day-of-year of an explicit date:

```
weekday 31.12.2564
weekday 2026-07-27
day of year today
```

### Numeric date literals

Any of the three supported formats, standalone, per your system locale
(day-first here, since this system is `de_DE`):

```
31.12.2564
27/07/2026
2026-07-27
```

## Examples

```
$ hotcal
      July 2026

Mo Tu We Th Fr Sa Su

       1  2  3  4  5
 6  7  8  9 10 11 12
13 14 15 16 17 18 19
20 21 22 23 24 25 26
27 28 29 30 31
```

*(`28` highlighted — today.)*

```
$ hotcal -n fourth thursday in may 2036
22.05.2036

$ hotcal weekday 31.12.2564
    December 2564

Mo Tu We Th Fr Sa Su

                1  2
 3  4  5  6  7  8  9
10 11 12 13 14 15 16
17 18 19 20 21 22 23
24 25 26 27 28 29 30
31
```

*(`31` highlighted, in the `weekday 31.12.2564` grid above.)*

```
$ hotcal -n christmas 2030
24.12.2030

$ hotcal -n easter 2028
16.04.2028

$ hotcal -n last day of month in february 2028
29.02.2028

$ hotcal -n in two days and 4 weeks
27.08.2026

$ hotcal -n 3 days before christmas
21.12.2026
```

Errors are single-line diagnostics on stderr, exit code 1:

```
$ hotcal 31/02/2026
Error: invalid date "31/02/2026" — February 2026 has no 31st day

$ hotcal fifth monday in february 2026
Error: "fifth monday in february 2026" does not exist — February 2026 has only 4 Mondays

$ hotcal cats
Error: unrecognized word "cats" — not part of the supported vocabulary
```

## Testing

```
pytest
# or, without a manual environment: uv run --with pytest --with hypothesis pytest
```

191 tests: engine correctness (leap years, century boundaries, Easter,
weekday arithmetic, all verified against known reference dates), parser and
query-resolution tests for both expression categories, rendering tests
(including a byte-for-byte match against the example grid above), and
Hypothesis property tests for date round-tripping and nth-weekday
consistency.

## Full spec

See [`CLAUDE.md`](CLAUDE.md) for the complete design document.
