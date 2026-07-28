"""Shared calendar name vocabulary — used by both the parser and the renderer."""

MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)

WEEKDAY_NAMES = (
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
)

MONTH_NUMBERS = {name.lower(): i + 1 for i, name in enumerate(MONTH_NAMES)}
WEEKDAY_NUMBERS = {name.lower(): i for i, name in enumerate(WEEKDAY_NAMES)}
