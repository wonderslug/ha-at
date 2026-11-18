"""English language pack."""

from collections.abc import Iterable
from datetime import datetime, timedelta

from . import LanguagePack


def format_clock(dt: datetime) -> str:
    """Format a datetime as a 12-hour clock time such as ``11:00 PM`` or ``6:30 AM``."""
    return f"{dt.hour % 12 or 12}:{dt.minute:02d} {'AM' if dt.hour < 12 else 'PM'}"


UNSUPPORTED_LANGUAGE = "Sorry, scheduling is only available in English for now."


def format_spoken_time(dt: datetime) -> str:
    """Format a datetime as it is said aloud: ``6 AM``, ``6:30 AM``, ``12 PM``, ``10:42 PM``."""
    suffix = "AM" if dt.hour < 12 else "PM"
    hour = dt.hour % 12 or 12
    return f"{hour} {suffix}" if dt.minute == 0 else f"{hour}:{dt.minute:02d} {suffix}"


def format_duration(delta: timedelta) -> str:
    """Format a duration as it is said aloud: ``20 minutes``, ``1 hour and 30 minutes``."""
    total = max(round(delta.total_seconds()), 1)
    parts: list[str] = []
    for unit, size in (("day", 86400), ("hour", 3600), ("minute", 60), ("second", 1)):
        count, total = divmod(total, size)
        if count:
            parts.append(f"{count} {unit}{'' if count == 1 else 's'}")
    return " and ".join(parts)


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

# Sentence triggers. Time pieces are range or value lists (below) so free text can't reach the
# time part; the command is the {command} wildcard. Every list is drawn from the parser's own
# tables, so whatever a template matches the time parser understands.
_CLOCK = "at ({hour}[:{minute}] [{meridiem}] [o'clock]|{named})"
_DAYREF = "({day}|on {weekday}) [{period}]"
_COUNT = "({number}|{number_word})"
_ABSOLUTE = [f"{_DAYREF} {_CLOCK}", f"{_CLOCK} {_DAYREF}", _CLOCK]
_RELATIVE = [
    _COUNT.join(("in ", " [and a half] {unit}")),
    _COUNT.join(("in ", " {unit} and a half")),
    "in half (a|an) {unit}",
]
_WHAT = "(what's|what is) scheduled"
_JOB_CLOCK = "{hour}[:{minute}] [{meridiem}]"


def _either_side(phrases: list[str]) -> list[str]:
    return [f"{phrase} {{command}}" for phrase in phrases] + [f"{{command}} {phrase}" for phrase in phrases]


def _values(words: Iterable[str]) -> dict[str, list[str]]:
    return {"values": list(words)}


_DAY_WORDS = {
    "today": ("today", None),
    "tonight": ("today", "night"),
    "tomorrow": ("tomorrow", None),
    "this morning": ("today", "morning"),
    "this afternoon": ("today", "afternoon"),
    "this evening": ("today", "evening"),
}
_PERIOD_WORDS = {
    "morning": "morning",
    "afternoon": "afternoon",
    "evening": "evening",
    "night": "night",
}
_WEEKDAY_WORDS = {
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
}
_UNIT_WORDS = {
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
}
_NUMBER_WORDS = {k: v for k, v in _NUMBERS.items() if " " not in k}
_MERIDIEM_WORDS = {
    "am": "am",
    "a.m.": "am",
    "a.m": "am",
    "pm": "pm",
    "p.m.": "pm",
    "p.m": "pm",
}
_NAMED_TIMES = {"noon": (12, 0), "midnight": (0, 0)}

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
    day_words=_DAY_WORDS,
    period_words=_PERIOD_WORDS,
    weekday_words=_WEEKDAY_WORDS,
    unit_words=_UNIT_WORDS,
    number_words=_NUMBER_WORDS,
    meridiem_words=_MERIDIEM_WORDS,
    named_times=_NAMED_TIMES,
    sentences={
        "schedule_absolute": _either_side(_ABSOLUTE),
        "schedule_relative": _either_side(_RELATIVE),
        "list": [_WHAT, f"{_WHAT} for {{scope}}", f"{_WHAT} for [the] {{name}}"],
        "cancel": [
            "cancel {all}",
            f"cancel [the] {_JOB_CLOCK} job",
            f"cancel [the] job at {_JOB_CLOCK}",
            "cancel [the] {name} {thing}",
        ],
    },
    sentence_lists={
        "hour": {"range": {"from": 0, "to": 23, "words": False}},
        "minute": {"range": {"from": 0, "to": 59, "words": False}},
        "number": {"range": {"from": 1, "to": 180, "words": False}},
        "number_word": _values(_NUMBER_WORDS),
        "unit": _values(_UNIT_WORDS),
        "meridiem": {"values": [{"in": word, "out": value} for word, value in _MERIDIEM_WORDS.items()]},
        "named": _values(_NAMED_TIMES),
        "day": _values(_DAY_WORDS),
        "period": _values(_PERIOD_WORDS),
        "weekday": _values(_WEEKDAY_WORDS),
        "scope": {
            "values": [
                {"in": "today", "out": "today"},
                {"in": "tonight", "out": "tonight"},
                {"in": "this evening", "out": "tonight"},
                {"in": "tomorrow", "out": "tomorrow"},
            ]
        },
        "all": _values(
            ["everything", "everything scheduled", "all jobs", "all the jobs", "all scheduled jobs", "all my jobs"]
        ),
        # The noun after a name in "cancel the bedtime script"; "the {name}" alone would also
        # catch "cancel the timer".
        "thing": _values(
            [
                "job",
                "jobs",
                "light",
                "lights",
                "lamp",
                "switch",
                "fan",
                "cover",
                "blinds",
                "thermostat",
                "media player",
                "vacuum",
                "lawn mower",
                "valve",
                "lock",
                "scene",
                "script",
            ]
        ),
    },
    sentence_clock="at {hour}:{minute:02d} {meridiem}",
    summary_verbs={
        "turn_on": "Turn on {name}",
        "turn_off": "Turn off {name}",
        "toggle": "Toggle {name}",
        "script.turn_on": "Run {name}",
        "automation.trigger": "Trigger {name}",
        # Intent types, for voice jobs
        "HassTurnOn": "Turn on {name}",
        "HassTurnOff": "Turn off {name}",
        "HassToggle": "Toggle {name}",
        "HassLightSet": "Set {name}",
        "HassSetPosition": "Set {name} position",
        "HassClimateSetTemperature": "Set {name} temperature",
        "HassClimateSetFanMode": "Set {name} fan mode",
        "HassFanSetSpeed": "Set {name} speed",
        "HassSetVolume": "Set {name} volume",
        "HassSetVolumeRelative": "Change {name} volume",
        "HassMediaPause": "Pause {name}",
        "HassMediaUnpause": "Resume {name}",
        "HassMediaNext": "Skip to the next track on {name}",
        "HassMediaPrevious": "Go back a track on {name}",
        "HassMediaPlayerMute": "Mute {name}",
        "HassMediaPlayerUnmute": "Unmute {name}",
        "HassVacuumStart": "Start {name}",
        "HassVacuumReturnToBase": "Send {name} back to base",
        "HassLawnMowerStartMowing": "Start {name}",
        "HassLawnMowerDock": "Dock {name}",
    },
    # A turn-on of scripts or scenes reads better as running or activating them
    domain_summary_verbs={
        "HassTurnOn:script": "Run {name}",
        "HassTurnOn:scene": "Activate {name}",
    },
    generic_action_summary="Run action",
    joiner=" and ",
    domain_words={
        "light": "lights",
        "switch": "switches",
        "fan": "fans",
        "cover": "covers",
        "climate": "thermostats",
        "media_player": "media players",
        "vacuum": "vacuums",
        "lawn_mower": "lawn mowers",
        "valve": "valves",
        "lock": "locks",
        "scene": "scenes",
        "script": "scripts",
    },
    place_target="{place} {things}",
    recognize_errors={
        "no_match": (
            "Sorry, I can only schedule commands I can check right now. Try rephrasing, or schedule a script or scene."
        ),
        "refused": (
            "Sorry, I can only schedule commands I can check right now. Try rephrasing, or schedule a script or scene."
        ),
        "no_target": "I couldn't find anything called {name}.",
        "no_target_domain": "I couldn't find a {domain} called {name}.",
    },
    responses={
        "absolute": "OK, at {time}{day} I'll {summary}.",
        "relative": "OK, in {duration}, at {time}, I'll {summary}.",
        "tomorrow": " tomorrow",
        "weekday": " on {weekday}",
        "date": " on {month} {day}",
        "weekday_names": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "month_names": [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ],
        "list_empty": "Nothing is scheduled.",
        "list": "{count} scheduled: {items}{more}.",
        "list_item": "{summary} at {time}{day}",
        "list_more": ", and {more} more",
        "list_separator": "; ",
        "cancel_one": "Cancelled: {item}.",
        "cancel_none": "I couldn't find a scheduled job matching that.",
        "cancel_ambiguous": "There are {count} jobs for {name}, at {times}. Say 'cancel the {first} job'.",
        "cancel_all": "Cancelled {count} jobs.",
        "cancel_all_left": " {count} jobs created by automations were left alone.",
        "bad_time": "Sorry, I didn't understand when.",
        "spoken_time": format_spoken_time,
        "duration": format_duration,
    },
    logbook={
        "scheduled": "scheduled {summary} for {time}",
        "executed": "ran {summary}",
        "failed": "failed {summary}: {error}",
        "failed_no_error": "failed {summary}",
        "cancelled": "cancelled {summary}",
        "missed": "missed {summary} (Home Assistant was down)",
    },
)
