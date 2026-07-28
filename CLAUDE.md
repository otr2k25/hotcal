# CLAUDE.md

# hotcal – Human-Oriented Terminal Calendar

## Vision

`` is a terminal calendar that combines the visual simplicity of `cal`/`ncal` with natural-language date reasoning.

The project has two equally important goals:

1. **Absolute correctness** for all Gregorian calendar calculations.
2. **Human-oriented interaction** using natural language commands instead of traditional option-heavy interfaces.

The calendar should feel like a conversation with time while remaining fully scriptable.

---

# Primary Design Goals

## Correctness First

Every feature depends on one invariant:

>  must always compute the correct Gregorian date.

No shortcuts, lookup tables with limited ranges or approximations are allowed.

The implementation must work for arbitrarily large years (subject only to integer limits of the language).

---

## Calendar Model

The calendar uses the **proleptic Gregorian calendar**.

Leap year rules are exactly:

* divisible by 4
* except divisible by 100
* except divisible by 400

No locale-specific calendar systems are supported by the core engine.

Everything builds on this model.

---

# Core Capabilities

The engine must answer every calendar question that can be derived from the Gregorian calendar.

Internal results such as weekday names, week numbers, or day-of-year counts are computed by the engine but are not output directly — see Output Formats. They surface only as a highlighted date in month view or as a date in one of the three supported formats.

Examples include:

Determine the weekday of any date.

```
31.12.2564

→ month view of December 2564, with 31.12.2564 highlighted
```

Determine the date from a weekday expression.

```
Fourth Thursday of May 2036

→ 22/05/2036
```

Relative dates.

```
two days ago

next monday

three weeks from now

last friday

100 years ago

in 10 years
```

Month calculations.

```
Last day of month

First weekday of month

Nth weekday of month

Remaining days
```

Year calculations.

```
Leap year

Number of weeks

Day of year

Remaining days
```

---

# Calendar Rendering

Rendering should closely resemble `cal` and `ncal`.

The display must remain compact and optimized for terminals.

Example:

```
      July 2026

Mo Tu We Th Fr Sa Su

       1  2  3  4  5
 6  7  8  9 10 11 12
13 14 15 16 17 18 19
20 21 22 23 24 25 26
27 28 29 30 31
```

Current day should be highlighted.

Selected dates should receive a second highlight.

Navigation never changes the calendar layout.

---

# Output Formats

The only accepted output formats are:

1. **Month view** — a calendar month with the relevant day(s) highlighted, in the compact `cal`/`ncal`-like layout described above. This is the default output for any resolved expression.
2. **Date** — a single date rendered in one of the three supported formats (DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD), per system locale.

No other output format is produced (no weekday names, no bare numbers, no free text).

The `-n` switch selects Date output explicitly — it prints just the resolved date, with no calendar.

---

# Natural Language Interface

The CLI should avoid long option lists whenever possible.

Instead it uses natural language.

The parser should understand common English date expressions.

Examples:

```
 today

 tomorrow

 yesterday

 next monday

 last friday

 two days ago

 in three weeks

 monday in three weeks

 first monday in april

 fourth thursday in may

 last sunday in october

 christmas

 easter

 new year

 now
```

The parser should accept both numeric and written numbers.

```
2 days ago

two days ago
```

Both forms are equivalent.

---

# Examples

Highlight next Monday.

```
 next monday
```

Highlight two days ago.

```
 two days ago
```

Jump three weeks ahead and highlight Monday.

```
 monday in 3 weeks
```

Show month view three weeks from now.

```
 hotcal in three weeks

→ month view of the month three weeks from today, with that date highlighted
```

Show just the date, three weeks from now.

```
 hotcal -n in three weeks

→ single date three weeks from today, in one of the three supported date formats
```

Show next month.

```
 next month
```

Display next year.

```
 next year
```

Show calendar containing Christmas.

```
 christmas
```

Determine weekday (shown as highlighted date in month view).

```
 weekday 31.12.2564

→ month view of December 2564, with 31.12.2564 highlighted
```

Determine date.

```
 -n fourth thursday in may 2036

22/05/2036
```

Determine day number (shown as highlighted date in month view).

```
 day-of-year today

→ month view of the current month, with today highlighted
```

---

# Parser

Natural language parsing is a first-class feature.

The parser should recognize:

* weekdays
* months
* relative durations
* holidays
* ordinal numbers
* written numbers
* numeric dates

## Date Formats

The following numeric date formats are supported:

* Day-Month-Year (DD/MM/YYYY)
* Month-Day-Year (MM/DD/YYYY)
* Year-Month-Day (YYYY-MM-DD)

The format used for parsing and display is determined by the system locale.

## Command Language

Commands are written in English.

The natural language grammar uses a fixed, closed vocabulary of temporally meaningful words (e.g. in, before, after, next, last, ago, from now). Words without temporal meaning in this context (e.g. "many") are not part of the grammar.

## Expression Categories

To keep the grammar unambiguous, vocabulary is grouped into two categories. An expression belongs to exactly one category — words from different categories cannot be combined within the same expression.

* **Relative** — today, tomorrow, yesterday, next, last, ago, in \<n\> \<unit\>, from now (e.g. `next monday`, `in three weeks`, `two days ago`, `monday in three weeks`)
* **Calculation** — last day of, first weekday of, nth weekday of, remaining days, leap year, number of weeks, day of year (e.g. `fourth thursday in may`, `last day of month`)

Mixing categories (e.g. `next fourth thursday in may`) is invalid and produces a diagnostic.

## Error Handling

Diagnostics are produced for ambiguous or invalid input.

Diagnostics are a single human-readable line written to stderr, in the form:

```
Error: <what went wrong> — <why / what was expected>
```

Examples:

```
Error: unrecognized word "cats" — not part of the supported vocabulary
Error: invalid date "31/02/2026" — February 2026 has no 31st day
Error: "fifth monday in february 2026" does not exist — February 2026 has only 4 Mondays
Error: "next fourth thursday in may" mixes categories — Relative and Calculation cannot be combined
```

No machine-readable output (no JSON, no structured codes) is produced — diagnostics are prose, not data.

Exit code is 0 on success, 1 on error.

---

# Architecture

The project is divided into independent layers.

```
CLI

↓

Natural Language Parser

↓

Calendar Query Model

↓

Gregorian Calendar Engine

↓

Renderer
```

No rendering code should perform calendar calculations.

No parser code should perform date arithmetic.

Everything routes through the calendar engine.

## Technical Requirements

Language: Python, version 3.11 or newer.

Standard library only for the calendar engine (no third-party dependency for date arithmetic).

Dependencies:

* `hypothesis` for property-based testing
* `pytest` for unit and fuzz tests

No dependency for rendering (stdlib string formatting only).

---

# Testing Requirements

Calendar correctness is critical.

The project should include:

* property tests
* fuzz testing
* leap year edge cases
* century boundaries
* Gregorian transition assumptions
* parser tests
* rendering tests

Known dates from multiple centuries should be verified against authoritative references.

---

# Design Philosophy

 should feel like asking another person about time.

Instead of:

```
 --weekday --date 2026-12-31
```

users write

```
 weekday 31.12.2026
```

Instead of:

```
 --offset=-2d
```

users write

```
 two days ago
```

Instead of:

```
 --month 5 --weekday thursday --nth 4
```

users write

```
 fourth thursday in may
```

The interface should prefer readable language over flags whenever this does not reduce precision or scriptability.

---

# Future Features

Not part of the first release. Planned for a later version:

* **Calendar arithmetic** — expressions like `today + 3 weeks`, `today - 8 months`, `next monday + 2 days`.
* **ISO week calculations** — week number, first/last day of an ISO week, ISO week expressions in the parser.

---

# Success Criteria

A successful implementation should satisfy the following:

* Every Gregorian date is computed correctly.
* Every weekday calculation is correct.
* Relative date calculations are exact.
* Calendar rendering matches the simplicity of `cal`/`ncal`.
* Natural language commands feel intuitive.
* The CLI remains predictable and script-friendly.
* Adding new date expressions requires extending the parser rather than changing the calendar engine.

## Python environment

This project's virtual environment lives at `.venv/`. Invoke its
interpreter directly; do not run `source .venv/bin/activate` (it cannot
persist between Claude's tool calls).

Use these commands:

- Run a script: `.venv/bin/python script.py`
- Open a REPL: `.venv/bin/python`
- Install a package: `.venv/bin/pip install <package>`
- Run a tool: `.venv/bin/pytest`, `.venv/bin/ruff check`,
  `.venv/bin/mypy`

Each entry under `.venv/bin/` resolves to the venv's copy of the tool,
so Python sees the project's `site-packages` automatically.
