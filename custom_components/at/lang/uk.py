"""Ukrainian language pack."""

from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Any

from . import LanguagePack


def format_clock(dt: datetime) -> str:
    """Format a datetime as a 24-hour clock time such as ``18:30``."""
    return f"{dt.hour:02d}:{dt.minute:02d}"


def format_spoken_time(dt: datetime) -> str:
    """Format a datetime as it is said aloud: the same 24-hour clock."""
    return format_clock(dt)


def _plural(count: int, one: str, few: str, many: str) -> str:
    """Pick the Ukrainian plural form for ``count``."""
    tail = abs(count) % 100
    if 11 <= tail <= 14:
        return many
    tail %= 10
    if tail == 1:
        return one
    if 2 <= tail <= 4:
        return few
    return many


def format_duration(delta: timedelta) -> str:
    """Format a duration as spoken: 20 minutes, 1 hour and 30 minutes."""
    total = max(round(delta.total_seconds()), 1)
    parts: list[str] = []
    units = (
        (86400, ("день", "дні", "днів")),
        (3600, ("годину", "години", "годин")),
        (60, ("хвилину", "хвилини", "хвилин")),
        (1, ("секунду", "секунди", "секунд")),
    )
    for size, forms in units:
        count, total = divmod(total, size)
        if count:
            parts.append(f"{count} {_plural(count, *forms)}")
    return " і ".join(parts)


_UNITS = {
    "одна": 1,
    "один": 1,
    "одну": 1,
    "дві": 2,
    "два": 2,
    "три": 3,
    "чотири": 4,
    "п'ять": 5,
    "шість": 6,
    "сім": 7,
    "вісім": 8,
    "дев'ять": 9,
    # Ordinal locative forms, so "двадцять першій" reads as 20 + 1.
    "першій": 1,
    "другій": 2,
    "третій": 3,
    "четвертій": 4,
    "п'ятій": 5,
    "шостій": 6,
    "сьомій": 7,
    "восьмій": 8,
    "дев'ятій": 9,
}
_TEENS = {
    "десять": 10,
    "одинадцять": 11,
    "дванадцять": 12,
    "тринадцять": 13,
    "чотирнадцять": 14,
    "п'ятнадцять": 15,
    "шістнадцять": 16,
    "сімнадцять": 17,
    "вісімнадцять": 18,
    "дев'ятнадцять": 19,
}
_TENS = {
    "двадцять": 20,
    "тридцять": 30,
    "сорок": 40,
    "п'ятдесят": 50,
    "шістдесят": 60,
    "сімдесят": 70,
    "вісімдесят": 80,
    "дев'яносто": 90,
}
# Ordinal locative forms the clock uses: at seven, at twenty-one minutes past.
_ORDINALS = {
    "першій": 1,
    "другій": 2,
    "третій": 3,
    "четвертій": 4,
    "п'ятій": 5,
    "шостій": 6,
    "сьомій": 7,
    "восьмій": 8,
    "дев'ятій": 9,
    "десятій": 10,
    "одинадцятій": 11,
    "дванадцятій": 12,
    "тринадцятій": 13,
    "чотирнадцятій": 14,
    "п'ятнадцятій": 15,
    "шістнадцятій": 16,
    "сімнадцятій": 17,
    "вісімнадцятій": 18,
    "дев'ятнадцятій": 19,
    "двадцятій": 20,
    "двадцять першій": 21,
    "двадцять другій": 22,
    "двадцять третій": 23,
}
_ZERO = "нуль"
# "півтори години" is a count; "півтори" and "півтора" are number words.
_HALF_WORDS = {"півтори": 1.5, "півтора": 1.5}
_NUMBER_WORDS = {
    "article": {"одну": 1, "одна": 1},
    "units": {**_UNITS, **_HALF_WORDS},
    "teens": _TEENS,
    "tens": _TENS,
    "ordinals": _ORDINALS,
}
_HUNDRED = "сто"

# 1 to 99: "двадцять п'ять", "сімнадцять", "шість", "сьомій".
_SMALL = r"(?:%(num_tens)s)(?:\s+(?:%(num_units)s))?|%(num_teens)s|%(num_ordinals)s|%(num_units)s"
# "сьома тридцять", "сьома нуль п'ять"
_MINUTE_WORDS = r"(?:нуль\s+)?(?:%(num_tens)s)(?:\s+(?:%(num_units)s))?|(?:нуль\s+)?%(num_teens)s|%(num_units)s"
# Up to 999: "сто", "сто двадцять".
_NUMBER = rf"(?:(?:%(num_units)s)\s+)?(?:%(scale)s)(?:\s+(?:{_SMALL}))?|{_SMALL}|{_ZERO}|%(num_article)s"


def _spell_small(n: int) -> str:
    names = {value: word for words in (_UNITS, _TEENS, _TENS) for word, value in words.items()}
    # Prefer the feminine form the clock and durations use: одна, дві.
    names[1] = "одна"
    names[2] = "дві"
    if n in names:
        return names[n]
    tens, units = divmod(n, 10)
    return f"{names[tens * 10]} {names[units]}"


def _spellings(n: int) -> list[str]:
    """Every way the number pattern writes ``n`` (0 to 999), for the sentence lists."""
    if n == 0:
        return [_ZERO]
    if n < 100:
        return [_spell_small(n)]
    hundreds, rest = divmod(n, 100)
    heads = [f"{_spell_small(hundreds)} {_HUNDRED}"] if hundreds > 1 else [_HUNDRED]
    if not rest:
        return heads
    return [f"{head} {_spell_small(rest)}" for head in heads]


def _spelled(numbers: Iterable[int]) -> dict[str, list[dict[str, Any]]]:
    return {"values": [{"in": words, "out": n} for n in numbers for words in _spellings(n)]}


# Sentence triggers. Time pieces are range or value lists (below) so free text can't reach the
# time part; the command is the {command} wildcard. Every list is drawn from the parser's own
# tables, so whatever a template matches the time parser understands.
_CLOCK = (
    r"(?:(?:о|в|на)\s+(?:"
    r"(?P<hour24>\d{2})\s+годин[аиі]?"
    r"|(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?"
    rf"|(?P<hour_words>{_SMALL})(?:\s+(?P<minute_words>{_MINUTE_WORDS}))?(?:\s+годин[іа]?)?"
    r")|(?P<named>%(named)s))"
    r"(?:\s+(?P<period>%(period)s))?"
)
_DAYREF = r"(?:(?P<day>%(day)s)|(?:у|в|на)\s+(?P<weekday>%(weekday)s))"
_WHAT = "(що заплановано|що в черзі|які плани)"
_JOB_CLOCK = "(о|в) {hour}[:{minute}]"
_JOB_DAY = "[{day}|(у|в|на) {weekday}]"

# Sentence templates for hassil. {area} and {floor} are the registries' names.
_CLOCK_SENTENCE = "(о|в|на) ({hour}[:{minute}]|{hour_word} [{minute_word}]|{named}) [годині|годин] [{period}]"
_DAYREF_SENTENCE = "({day}|(у|в|на) {weekday})"
_ABSOLUTE_SENTENCES = [
    f"{_DAYREF_SENTENCE} {_CLOCK_SENTENCE}",
    f"{_CLOCK_SENTENCE} {_DAYREF_SENTENCE}",
    _CLOCK_SENTENCE,
]
_RELATIVE_SENTENCES = [
    "через {number} {unit}",
    "через {number_word} {unit}",
    "через {number} з половиною {unit}",
    "через {number_word} з половиною {unit}",
    "через {number} {unit} і пів",
    "через пів {unit}",
    "через півтори {unit}",
    "через півтора {unit}",
]


def _either_side(phrases: list[str]) -> list[str]:
    return [f"{phrase} {{command}}" for phrase in phrases] + [f"{{command}} {phrase}" for phrase in phrases]


def _values(words: Iterable[str]) -> dict[str, list[str]]:
    return {"values": list(words)}


_DAY_WORDS = {
    "сьогодні": ("today", None),
    "сьогодні вранці": ("today", "morning"),
    "сьогодні вдень": ("today", "afternoon"),
    "сьогодні ввечері": ("today", "evening"),
    "сьогодні вночі": ("today", "night"),
    "вранці": ("today", "morning"),
    "вдень": ("today", "afternoon"),
    "ввечері": ("today", "evening"),
    "вночі": ("today", "night"),
    "завтра": ("tomorrow", None),
    "завтра вранці": ("tomorrow", "morning"),
    "завтра вдень": ("tomorrow", "afternoon"),
    "завтра ввечері": ("tomorrow", "evening"),
    "завтра вночі": ("tomorrow", "night"),
}
_PERIOD_WORDS = {
    "вранці": "morning",
    "ранку": "morning",
    "вдень": "afternoon",
    "дня": "afternoon",
    "ввечері": "evening",
    "вечора": "evening",
    "вночі": "night",
    "ночі": "night",
}
_WEEKDAY_WORDS = {
    "понеділок": 0,
    "вівторок": 1,
    "середу": 2,
    "середа": 2,
    "четвер": 3,
    "п'ятницю": 4,
    "п'ятниця": 4,
    "суботу": 5,
    "субота": 5,
    "неділю": 6,
    "неділя": 6,
}
_UNIT_WORDS = {
    "секунду": 1,
    "секунди": 1,
    "секунд": 1,
    "сек": 1,
    "хвилину": 60,
    "хвилини": 60,
    "хвилин": 60,
    "хв": 60,
    "годину": 3600,
    "години": 3600,
    "годин": 3600,
    "год": 3600,
    "день": 86400,
    "дні": 86400,
    "днів": 86400,
}
# Ukrainian has no AM/PM: the pack keeps an empty table and no ampm branch in the clock.
_MERIDIEM_WORDS: dict[str, str] = {}
_NAMED_TIMES = {"опівдні": (12, 0), "опівночі": (0, 0)}

UK = LanguagePack(
    code="uk",
    time_patterns={
        "relative": [
            r"через\s+(?P<count>%(number)s)(?P<half>\s+(?:з\s+)?половиною)?\s+(?P<unit>%(unit)s)",
            r"через\s+(?P<count>%(number)s)\s+(?P<unit>%(unit)s)(?P<half>\s+і\s+пів)",
            r"через\s+пів\s+(?P<halfonly>%(unit)s)",
        ],
        "number": _NUMBER,
        "clock": _CLOCK,
        "dayref": _DAYREF,
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
    number_fillers=frozenset({"і", "та", "нуль"}),
    run_pattern=r"(?:запусти|виконай|активуй)\s+(?:автоматизацію\s+)?(?P<name>.+?)(?:\s+автоматизацію)?",
    sentences={
        "run": ["(запусти|виконай|активуй) [автоматизацію] {name}"],
        "announce_area": [
            "(оголоси|повідом|скажи) (в|у|на) {area} [що] {message}",
            "скажи (всім|усім) (в|у) {area} [що] {message}",
            "повідом (всім|усім) (в|у) {area} [що] {message}",
            "(оголоси|повідом) [що] {message} (в|у|на) {area}",
        ],
        "announce_floor": [
            "(оголоси|повідом) [на] {floor} [що] {message}",
            "скажи (всім|усім) на {floor} [що] {message}",
            "(оголоси|повідом) [що] {message} на {floor}",
        ],
        "announce_everyone": [
            "скажи (всім|усім) [що] {message}",
            "оголоси (всім|усім|на весь дім) [що] {message}",
            "повідом (всім|усім) [що] {message}",
        ],
        "announce_area_no_message": [
            "(оголоси|повідом|скажи) (в|у|на) {area}",
            "скажи (всім|усім) (в|у) {area}",
        ],
        "announce_floor_no_message": [
            "(оголоси|повідом|скажи) на {floor}",
            "скажи (всім|усім) на {floor}",
        ],
        "schedule_absolute": _either_side(_ABSOLUTE_SENTENCES),
        "schedule_relative": _either_side(_RELATIVE_SENTENCES),
        "list": [
            _WHAT,
            f"{_WHAT} на {{scope}}",
            f"{_WHAT} для {{name}}",
            "що заплановано на {scope}",
        ],
        "cancel": [
            "скасуй {all}",
            f"скасуй завдання {_JOB_CLOCK} {_JOB_DAY}",
            f"скасуй завдання на {_JOB_CLOCK} {_JOB_DAY}",
            "скасуй {name} {thing}",
        ],
    },
    sentence_lists={
        "hour": {"range": {"from": 0, "to": 23, "words": False}},
        "minute": {"range": {"from": 0, "to": 59, "words": False}},
        "number": {"range": {"from": 1, "to": 180, "words": False}},
        "number_word": {
            "values": [{"in": word, "out": 1} for word in _NUMBER_WORDS["article"]] + _spelled(range(1, 181))["values"]
        },
        "hour_word": {"values": [{"in": word, "out": value} for word, value in _ORDINALS.items()]},
        "minute_word": _spelled(range(60)),
        "unit": _values(_UNIT_WORDS),
        "named": _values(_NAMED_TIMES),
        "day": _values(_DAY_WORDS),
        "period": _values(_PERIOD_WORDS),
        "weekday": _values(_WEEKDAY_WORDS),
        "scope": {
            "values": [
                {"in": "сьогодні", "out": "today"},
                {"in": "вечір", "out": "tonight"},
                {"in": "ввечері", "out": "tonight"},
                {"in": "завтра", "out": "tomorrow"},
            ]
        },
        "all": _values(["все", "усе", "всі завдання", "усі завдання", "все заплановане", "всі заплановані завдання"]),
        # The noun after a name in "скасуй сцену Вечір"; "скасуй {name}" alone would catch "скасуй таймер".
        "thing": _values(
            [
                "завдання",
                "завданням",
                "світло",
                "лампу",
                "розетку",
                "вентилятор",
                "штору",
                "термостат",
                "медіаплеєр",
                "пилосос",
                "газонокосарку",
                "клапан",
                "замок",
                "сцену",
                "скрипт",
            ]
        ),
    },
    sentence_clock="о {hour}:{minute:02d} {meridiem}",
    sentence_weekday="у {weekday}",
    summary_verbs={
        "turn_on": "увімкнути {name}",
        "turn_off": "вимкнути {name}",
        "toggle": "перемкнути {name}",
        "script.turn_on": "запустити {name}",
        "automation.trigger": "активувати {name}",
        # Intent types, for voice jobs
        "AutomationRun": "активувати {name}",
        "HassTurnOn": "увімкнути {name}",
        "HassTurnOff": "вимкнути {name}",
        "HassToggle": "перемкнути {name}",
        "HassLightSet": "змінити {name}",
        "HassSetPosition": "змінити положення {name}",
        "HassClimateSetTemperature": "змінити температуру {name}",
        "HassClimateSetFanMode": "змінити режим вентилятора {name}",
        "HassFanSetSpeed": "змінити швидкість {name}",
        "HassSetVolume": "змінити гучність {name}",
        "HassSetVolumeRelative": "змінити гучність {name}",
        "HassMediaPause": "призупинити {name}",
        "HassMediaUnpause": "продовжити {name}",
        "HassMediaNext": "перемкнути на наступний трек у {name}",
        "HassMediaPrevious": "перемкнути на попередній трек у {name}",
        "HassMediaPlayerMute": "вимкнути звук {name}",
        "HassMediaPlayerUnmute": "увімкнути звук {name}",
        "HassVacuumStart": "запустити {name}",
        "HassVacuumReturnToBase": "відправити {name} на базу",
        "HassLawnMowerStartMowing": "запустити {name}",
        "HassLawnMowerDock": "відправити {name} на базу",
        "HassBroadcast": "оголосити «{message}»",
        "PlaceAnnounce": "оголосити «{message}» у {area}",
        "PlaceAnnounce:floor": "оголосити «{message}» на {floor}",
        "HassMediaSearchAndPlay": "відтворити {search_query} на {name}",
        "HassVacuumCleanArea": "прибрати в {area}",
        "HassListAddItem": "додати {item} до {name}",
        "HassListCompleteItem": "позначити {item} у {name}",
        "HassListRemoveItem": "видалити {item} з {name}",
        "HassShoppingListAddItem": "додати {item} до списку покупок",
        "HassShoppingListCompleteItem": "позначити {item} у списку покупок",
    },
    # Where "turn on" or "turn off" is the wrong verb for the device: run a script, open a cover, lock a lock
    domain_summary_verbs={
        "HassTurnOn:script": "запустити {name}",
        "HassTurnOn:scene": "активувати {name}",
        "HassTurnOn:cover": "відкрити {name}",
        "HassTurnOff:cover": "закрити {name}",
        "HassTurnOn:valve": "відкрити {name}",
        "HassTurnOff:valve": "закрити {name}",
        "HassTurnOn:lock": "замкнути {name}",
        "HassTurnOff:lock": "відімкнути {name}",
    },
    generic_action_summary="виконати дію",
    named_action_summary="{action}: {name}",
    joiner=" і ",
    domain_words={
        "light": "світло",
        "switch": "вимикачі",
        "fan": "вентилятори",
        "cover": "штори",
        "climate": "термостати",
        "media_player": "медіаплеєри",
        "vacuum": "пилососи",
        "lawn_mower": "газонокосарки",
        "valve": "клапани",
        "lock": "замки",
        "scene": "сцени",
        "script": "скрипти",
    },
    place_target="{place}: {things}",
    recognize_errors={
        "no_match": (
            "Вибачте, я можу планувати лише команди, які вмію перевірити зараз. "
            "Спробуйте переформулювати або заплануйте скрипт чи сцену."
        ),
        "refused": (
            "Вибачте, я можу планувати лише команди, які вмію перевірити зараз. "
            "Спробуйте переформулювати або заплануйте скрипт чи сцену."
        ),
        "no_target": "Не знайшов нічого з назвою {name}.",
        "no_target_domain": "Не знайшов {domain} з назвою {name}.",
        "no_message_area": "Що оголосити в {area}?",
        "no_message_floor": "Що оголосити на {floor}?",
    },
    responses={
        "absolute": "Гаразд, о {time}{day}: {summary}.",
        "relative": "Гаразд, через {duration} (о {time}): {summary}.",
        "today": " сьогодні",
        "yesterday": " вчора",
        "tomorrow": " завтра",
        "weekday": " у {weekday}",
        "date": " {day} {month}",
        "weekday_names": ["понеділок", "вівторок", "середу", "четвер", "п'ятницю", "суботу", "неділю"],
        "month_names": [
            "січня",
            "лютого",
            "березня",
            "квітня",
            "травня",
            "червня",
            "липня",
            "серпня",
            "вересня",
            "жовтня",
            "листопада",
            "грудня",
        ],
        "list_empty": "Нічого не заплановано.",
        "list": "Заплановано ({count}): {items}{more}.",
        "list_item": "{summary} о {time}{day}",
        "list_more": ", і ще {more}",
        "list_separator": "; ",
        "cancel_one": "Скасовано: {item}.",
        "cancel_none": "Не знайшов відповідного запланованого завдання.",
        "cancel_ambiguous": "Знайдено кілька завдань ({count}) для {name}: {times}. Скажіть «скасуй {first}».",
        "cancel_ambiguous_by_summary": "Знайдено кілька завдань ({count}) для {name}: {items}. Скажіть «скасуй {first}».",
        "cancel_job": "завдання о {time}{day}",
        "cancel_all": "Скасовано завдань: {count}.",
        "cancel_all_one": "Скасовано завдань: {count}.",
        "cancel_all_left": " Залишено без змін завдань, створених автоматизаціями: {count}.",
        "cancel_all_left_one": " Залишено без змін завдань, створених автоматизаціями: {count}.",
        "bad_time": "Вибачте, не зрозумів, коли саме.",
        "announced": "Готово",
        "spoken_time": format_spoken_time,
        "duration": format_duration,
    },
    logbook={
        "scheduled": "заплановано {summary} на {time}",
        "executed": "виконано {summary}",
        "failed": "не виконано {summary}: {error}",
        "failed_no_error": "не виконано {summary}",
        "cancelled": "скасовано {summary}",
        "missed": "пропущено {summary} (Home Assistant був недоступний)",
    },
    messages={
        # Why a job failed (core/executor.py, ha_internal/intents.py)
        "nothing_to_run": "у завдання немає що виконувати",
        "user_gone": "Користувача, який запланував це завдання, більше не існує",
        "entity_unavailable": "{entity_id} недоступний",
        "entity_gone": "{entity_id} більше не існує",
        "action_invalid": "{action}: збережена дія некоректна: {error}",
        "action_failed": "{summary}: {error}",
        "intent_not_exposed": "{intent}: {target} не відкритий для голосових асистентів",
        "intent_not_found": "{intent}: {target} не знайдено ({reason})",
        "intent_no_match": "немає збігу",
        "automation_triggered": "активовано {name}",
        "intent_gone": "{intent}: інтент більше не існує",
        "intent_failed": "{intent} для {target} не вдався: {error}",
        # Why a picked action was refused (core/actions.py)
        "action_one_step": "дія повинна мати рівно один крок",
        "action_step_mapping": "крок повинен бути словником",
        "action_step_service": "крок повинен викликати сервіс",
        "action_extra_keys": "{name} не дозволяє {keys}",
        "target_missing": "{name} потребує цілі",
        "target_extra_keys": "ціль {name} не дозволяє {keys}",
        "target_ids_strings": "ідентифікатори цілі {name} повинні бути рядками",
        "target_specific": "ціль {name} повинна вказувати конкретні ідентифікатори",
        "templates_admin_only": "Шаблони доступні лише адміністраторам",
        "data_mapping": "{name}: дані повинні бути словником",
        # Voice intents
        "not_set_up": "Вибачте, планування не налаштоване.",
    },
    todo={
        "done": "Виконано",
        "failed": "Не виконано: {error}",
        "failed_no_error": "Не виконано",
        "missed": "Пропущено",
        "cancelled": "Скасовано",
    },
)
