"""English language pack."""

from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Any

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


_UNITS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9}
_TEENS = {
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
}
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
_NUMBER_WORDS = {"article": {"a": 1, "an": 1}, "units": _UNITS, "teens": _TEENS, "tens": _TENS}
_HUNDRED = "hundred"

# 1 to 99: "forty five", "forty-five", "seventeen", "six".
_SMALL = r"(?:%(num_tens)s)(?:(?:\s+|-)(?:%(num_units)s))?|%(num_teens)s|%(num_units)s"
# "seven thirty", "seven oh five", "six forty-five"
_MINUTE_WORDS = r"(?:oh|o)\s+(?:%(num_units)s)|(?:%(num_tens)s)(?:(?:\s+|-)(?:%(num_units)s))?|%(num_teens)s"
# A 24-hour clock hour said with "hundred": "eighteen hundred", "oh six hundred", "zero hundred".
_HOUR_24_WORDS = r"(?:oh|o|zero)\s+(?:%(num_units)s)|zero|%(num_teens)s|twenty(?:(?:\s+|-)(?:one|two|three))?"
_HOURS = "hours"
# Up to 999: "a hundred", "one hundred and twenty", "two hundred five".
_NUMBER = rf"(?:(?:%(num_units)s|a)\s+)?(?:%(scale)s)(?:\s+(?:and\s+)?(?:{_SMALL}))?|{_SMALL}|%(num_article)s"


def _spell_small(n: int) -> str:
    names = {value: word for words in (_UNITS, _TEENS, _TENS) for word, value in words.items()}
    tens, units = divmod(n, 10)
    return names[n] if n in names else f"{names[tens * 10]} {names[units]}"


def _spellings(n: int) -> list[str]:
    """Every way the number pattern writes ``n`` (1 to 999), hyphens aside, for the sentence lists."""
    if n < 100:
        return [_spell_small(n)]
    hundreds, rest = divmod(n, 100)
    heads = [f"{_spell_small(hundreds)} {_HUNDRED}"] + ([f"a {_HUNDRED}"] if hundreds == 1 else [])
    if not rest:
        return heads
    return [f"{head}{joiner}{_spell_small(rest)}" for head in heads for joiner in (" ", " and ")]


def _spelled(numbers: Iterable[int]) -> dict[str, list[dict[str, Any]]]:
    return {"values": [{"in": words, "out": n} for n in numbers for words in _spellings(n)]}


# Sentence triggers. Time pieces are range or value lists (below) so free text can't reach the
# time part; the command is the {command} wildcard. Every list is drawn from the parser's own
# tables, so whatever a template matches the time parser understands.
# A bare hour after 12 still matches, so the parser refuses it instead of Assist running the command now.
_CLOCK = (
    "at ({hour}[:{minute}] [{meridiem}|hours] [o'clock]|{hour_word} [{minute_word}] [{meridiem}|hours] [o'clock]"
    "|{hhmm} [hours]|({hour_24}|{hour_word_24}) hundred [hours]|{named})"
)
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
_JOB_DAY = "[({day}|on {weekday})]"


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
        "number": _NUMBER,
        "clock": (
            r"at\s+(?:(?P<named>%(named)s)"
            rf"|(?P<hhmm>\d{{4}})\s+{_HOURS}"
            rf"|(?:(?P<hour24>\d{{2}})|(?P<hour24_words>{_HOUR_24_WORDS}))\s+{_HUNDRED}(?:\s+{_HOURS})?"
            r"|(?:(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?"
            rf"|(?P<hour_words>{_SMALL})(?:\s+(?P<minute_words>{_MINUTE_WORDS}))?)"
            rf"(?:\s*(?P<ampm>%(meridiem)s)|\s+(?P<hours>{_HOURS}))?(?:\s+o'?clock)?)"
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
    number_scales={_HUNDRED: 100},
    number_fillers=frozenset({"and", "oh", "o", "zero"}),
    run_pattern=r"(?:run|trigger|fire)\s+(?:the\s+)?(?P<name>.+?)(?:\s+automation)?",
    sentences={
        "run": ["(run|trigger|fire) [the] {name}"],
        "announce_area": [
            "(announce|broadcast) (in|to) [the] {area} [that[s]] {message}",
            "tell [(everyone|everybody) in] the {area} [that[s]] {message}",
            "let [(everyone|everybody) in] the {area} know [that[s]] {message}",
            "(announce|broadcast) [that[s]] {message} (in|to) [the] {area}",
            "tell (everyone|everybody) [that[s]] {message} (in|on) [the] {area}",
        ],
        "announce_floor": [
            "(announce|broadcast) [(on|to) [the]] {floor} [that[s]] {message}",
            "tell [(everyone|everybody) [on]] the {floor} [that[s]] {message}",
            "tell (everyone|everybody) {floor} [that[s]] {message}",
            "let [(everyone|everybody) [on]] the {floor} know [that[s]] {message}",
            "let (everyone|everybody) {floor} know [that[s]] {message}",
            "(announce|broadcast) [that[s]] {message} (on|to) [the] {floor}",
            "tell (everyone|everybody) [that[s]] {message} (on|in) [the] {floor}",
        ],
        "announce_everyone": [
            "tell (everyone|everybody) [that[s]] {message}",
            "let (everyone|everybody) know [that[s]] {message}",
            "(announce|broadcast) to (everyone|everybody|the [whole] house) [that[s]] {message}",
        ],
        "announce_area_no_message": [
            "(announce|broadcast) [everywhere] [that[s]] [(in|to|on)] [the] {area}",
            "tell [(everyone|everybody)] [(in|on)] [the] {area}",
            "let [(everyone|everybody)] [(in|on)] [the] {area} know",
        ],
        "announce_floor_no_message": [
            "(announce|broadcast) [everywhere] [that[s]] [(in|to|on)] [the] {floor}",
            "tell [(everyone|everybody)] [(in|on)] [the] {floor}",
            "let [(everyone|everybody)] [(in|on)] [the] {floor} know",
        ],
        "schedule_absolute": _either_side(_ABSOLUTE),
        "schedule_relative": _either_side(_RELATIVE),
        "list": [_WHAT, f"{_WHAT} for {{scope}}", f"{_WHAT} for [the] {{name}}"],
        "cancel": [
            "cancel {all}",
            f"cancel [the] {_JOB_CLOCK} job {_JOB_DAY}",
            f"cancel [the] job at {_JOB_CLOCK} {_JOB_DAY}",
            "cancel [the] {name} {thing}",
        ],
    },
    sentence_lists={
        "hour": {"range": {"from": 0, "to": 23, "words": False}},
        "hour_24": {"values": [{"in": f"{h:02d}", "out": h} for h in range(24)]},
        "hhmm": {"values": [{"in": f"{h:02d}{m:02d}", "out": h * 100 + m} for h in range(24) for m in range(60)]},
        "minute": {"range": {"from": 0, "to": 59, "words": False}},
        "number": {"range": {"from": 1, "to": 180, "words": False}},
        "number_word": {
            "values": [{"in": word, "out": 1} for word in _NUMBER_WORDS["article"]] + _spelled(range(1, 181))["values"]
        },
        "hour_word": _spelled(range(1, 24)),
        "hour_word_24": {
            "values": [{"in": "zero", "out": 0}]
            + [{"in": f"{zero} {word}", "out": n} for zero in ("oh", "o", "zero") for word, n in _UNITS.items()]
            + _spelled(range(10, 24))["values"]
        },
        "minute_word": {
            "values": [{"in": f"{zero} {word}", "out": n} for zero in ("oh", "o") for word, n in _UNITS.items()]
            + _spelled(range(10, 60))["values"]
        },
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
    sentence_weekday="on {weekday}",
    summary_verbs={
        "turn_on": "Turn on {name}",
        "turn_off": "Turn off {name}",
        "toggle": "Toggle {name}",
        "script.turn_on": "Run {name}",
        "automation.trigger": "Trigger {name}",
        # Intent types, for voice jobs
        "AutomationRun": "Trigger {name}",
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
        "HassBroadcast": 'Broadcast "{message}"',
        "PlaceAnnounce": 'Announce "{message}" in {area}',
        "PlaceAnnounce:floor": 'Announce "{message}" on {floor}',
        "HassMediaSearchAndPlay": "Play {search_query} on {name}",
        "HassVacuumCleanArea": "Clean {area}",
        "HassListAddItem": "Add {item} to {name}",
        "HassListCompleteItem": "Check off {item} on {name}",
        "HassListRemoveItem": "Remove {item} from {name}",
        "HassShoppingListAddItem": "Add {item} to the shopping list",
        "HassShoppingListCompleteItem": "Check off {item} on the shopping list",
    },
    # Where "turn on" or "turn off" is the wrong verb for the device: run a script, open a cover, lock a lock
    domain_summary_verbs={
        "HassTurnOn:script": "Run {name}",
        "HassTurnOn:scene": "Activate {name}",
        "HassTurnOn:cover": "Open {name}",
        "HassTurnOff:cover": "Close {name}",
        "HassTurnOn:valve": "Open {name}",
        "HassTurnOff:valve": "Close {name}",
        "HassTurnOn:lock": "Lock {name}",
        "HassTurnOff:lock": "Unlock {name}",
    },
    generic_action_summary="Run action",
    named_action_summary="{action}: {name}",
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
        "no_message_area": "What should I announce in the {area}?",
        "no_message_floor": "What should I announce on {floor}?",
    },
    responses={
        "absolute": "OK, at {time}{day} I'll {summary}.",
        "relative": "OK, in {duration}, at {time}, I'll {summary}.",
        "today": " today",
        "yesterday": " yesterday",
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
        "cancel_ambiguous": "There are {count} jobs for {name}, at {times}. Say 'cancel the {first}'.",
        "cancel_ambiguous_by_summary": "There are {count} jobs for {name}: {items}. Say 'cancel the {first} job'.",
        "cancel_job": "{time} job{day}",
        "cancel_all": "Cancelled {count} jobs.",
        "cancel_all_one": "Cancelled {count} job.",
        "cancel_all_left": " {count} jobs created by automations were left alone.",
        "cancel_all_left_one": " {count} job created by automations was left alone.",
        "bad_time": "Sorry, I didn't understand when.",
        "announced": "Done",
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
    messages={
        # Why a job failed (core/executor.py, ha_internal/intents.py)
        "nothing_to_run": "the job has nothing to run",
        "user_gone": "The user who scheduled this job no longer exists",
        "entity_unavailable": "{entity_id} is unavailable",
        "entity_gone": "{entity_id} no longer exists",
        "action_invalid": "{action}: the stored action is invalid: {error}",
        "action_failed": "{summary}: {error}",
        "intent_not_exposed": "{intent}: {target} is not exposed to voice assistants",
        "intent_not_found": "{intent}: {target} not found ({reason})",
        "intent_no_match": "no match",
        "automation_triggered": "Triggered {name}",
        "intent_gone": "{intent}: the intent no longer exists",
        "intent_failed": "{intent} for {target} failed: {error}",
        # Why a picked action was refused (core/actions.py)
        "action_one_step": "an action must have exactly one step",
        "action_step_mapping": "the step must be a mapping",
        "action_step_service": "the step must call a service",
        "action_extra_keys": "{name} does not allow {keys}",
        "target_missing": "{name} needs a target",
        "target_extra_keys": "{name} target does not allow {keys}",
        "target_ids_strings": "{name} target ids must be strings",
        "target_specific": "{name} target must name specific ids",
        "templates_admin_only": "Templates are only available to administrators",
        "data_mapping": "{name} data must be a mapping",
        # Voice intents
        "not_set_up": "Sorry, scheduling isn't set up.",
    },
    todo={
        "done": "Done",
        "failed": "Failed: {error}",
        "failed_no_error": "Failed",
        "missed": "Missed",
        "cancelled": "Cancelled",
    },
)
