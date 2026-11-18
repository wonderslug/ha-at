"""English language pack."""

from . import LanguagePack

_NUMBERS = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "fifteen": 15,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "forty five": 45,
    "fifty": 50,
    "sixty": 60,
}

EN = LanguagePack(
    code="en",
    time_patterns={
        "relative": [
            r"in\s+(?P<count>%(number)s)(?P<half>\s+and\s+a\s+half)?\s+(?P<unit>%(unit)s)",
            r"in\s+(?P<count>%(number)s)\s+(?P<unit>%(unit)s)(?P<half>\s+and\s+a\s+half)",
            r"in\s+half\s+an?\s+(?P<halfonly>%(unit)s)",
        ],
        "clock": (
            r"at\s+(?:(?P<named>%(named)s)"
            r"|(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?"
            r"(?:\s*(?P<ampm>%(meridiem)s))?(?:\s+o'?clock)?)"
        ),
        "dayref": (
            r"(?:(?P<day>%(day)s)|on\s+(?P<weekday>%(weekday)s))"
            r"(?:\s+(?P<period>%(period)s))?"
        ),
        "phrases": [
            r"%(dayref)s\s+%(clock)s",
            r"%(clock)s\s+%(dayref)s",
            r"%(clock)s",
        ],
    },
    day_words={
        "today": ("today", None),
        "tonight": ("today", "night"),
        "tomorrow": ("tomorrow", None),
        "this morning": ("today", "morning"),
        "this afternoon": ("today", "afternoon"),
        "this evening": ("today", "evening"),
    },
    period_words={
        "morning": "morning",
        "afternoon": "afternoon",
        "evening": "evening",
        "night": "night",
    },
    weekday_words={
        "monday": 0,
        "mon": 0,
        "tuesday": 1,
        "tue": 1,
        "tues": 1,
        "wednesday": 2,
        "wed": 2,
        "thursday": 3,
        "thu": 3,
        "thurs": 3,
        "friday": 4,
        "fri": 4,
        "saturday": 5,
        "sat": 5,
        "sunday": 6,
        "sun": 6,
    },
    unit_words={
        "second": 1,
        "seconds": 1,
        "sec": 1,
        "secs": 1,
        "minute": 60,
        "minutes": 60,
        "min": 60,
        "mins": 60,
        "hour": 3600,
        "hours": 3600,
        "hr": 3600,
        "hrs": 3600,
        "day": 86400,
        "days": 86400,
    },
    number_words={k: v for k, v in _NUMBERS.items() if " " not in k},
    meridiem_words={
        "am": "am",
        "a.m.": "am",
        "a.m": "am",
        "pm": "pm",
        "p.m.": "pm",
        "p.m": "pm",
    },
    named_times={"noon": (12, 0), "midnight": (0, 0)},
)
