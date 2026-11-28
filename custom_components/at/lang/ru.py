"""Russian language pack (draft translation, awaiting native-speaker review).

Notes for the reviewer:
- grammatical person: every ``summary_verbs`` entry is first-person perfective future
  («Включу ...»), because confirmations render as «Хорошо, в 23:00 я включу ...»;
- entity/area names arrive in the nominative, so ``place_target`` wraps the place in
  parentheses instead of guessing a prepositional case («Светильники (Кухня)»);
- «в 21 час» is refused (a bare 24-hour hour), like English "at 21"; say «в 21:00»
  or «в двадцать один ноль-ноль».
"""

from collections.abc import Iterable
from datetime import datetime, timedelta
from typing import Any

from . import LanguagePack

UNSUPPORTED_LANGUAGE = "Извини, планирование пока недоступно на этом языке."


def format_clock(dt: datetime) -> str:
    """Format a datetime as a 24-hour clock time such as ``23:00`` or ``6:30``."""
    return f"{dt.hour}:{dt.minute:02d}"


def format_spoken_time(dt: datetime) -> str:
    """Format a datetime as it is said aloud: «6 утра», «12 ночи», «15:05», «23:00».

    Russian says hour words only for 0-12 («в 6 утра», «в 2 ночи»); later times are just
    the 24-hour clock («в 23:00»), never «23 вечера».
    """
    hour = dt.hour
    if hour < 5:
        suffix, spoken = "ночи", hour or 12
    elif hour < 12:
        suffix, spoken = "утра", hour
    elif hour == 12:
        suffix, spoken = "дня", 12
    else:
        return f"{hour}:{dt.minute:02d}"
    return f"{spoken} {suffix}" if dt.minute == 0 else f"{spoken}:{dt.minute:02d} {suffix}"


_PLURAL_FORMS = {
    "секунда": ("секунда", "секунды", "секунд"),
    "минута": ("минута", "минуты", "минут"),
    "час": ("час", "часа", "часов"),
    "день": ("день", "дня", "дней"),
}


def _plural(count: int, forms: tuple[str, str, str]) -> str:
    """Russian plural forms: 1 секунда, 2 секунды, 5 секунд."""
    if count % 100 in (11, 12, 13, 14) or count % 10 in (0, 5, 6, 7, 8, 9):
        return forms[2]
    if count % 10 == 1:
        return forms[0]
    return forms[1]


def format_duration(delta: timedelta) -> str:
    """Format a duration as it is said aloud: ``20 минут``, ``1 час 30 минут``."""
    total = max(round(delta.total_seconds()), 1)
    parts: list[str] = []
    for unit, size in (("день", 86400), ("час", 3600), ("минута", 60), ("секунда", 1)):
        count, total = divmod(total, size)
        if count:
            parts.append(f"{count} {_plural(count, _PLURAL_FORMS[unit])}")
    return " ".join(parts)


_UNITS = {
    "один": 1,
    "одна": 1,
    "одну": 1,
    "час": 1,
    "минуту": 1,
    "секунду": 1,
    "день": 1,
    "два": 2,
    "две": 2,
    "три": 3,
    "четыре": 4,
    "пять": 5,
    "шесть": 6,
    "семь": 7,
    "восемь": 8,
    "девять": 9,
}
_TEENS = {
    "десять": 10,
    "одиннадцать": 11,
    "двенадцать": 12,
    "тринадцать": 13,
    "четырнадцать": 14,
    "пятнадцать": 15,
    "шестнадцать": 16,
    "семнадцать": 17,
    "восемнадцать": 18,
    "девятнадцать": 19,
}
_TENS = {
    "двадцать": 20,
    "тридцать": 30,
    "сорок": 40,
    "пятьдесят": 50,
    "шестьдесят": 60,
    "семьдесят": 70,
    "восемьдесят": 80,
    "девяносто": 90,
}
_ZERO = {"ноль": 0, "нуль": 0, "ноль-ноль": 0, "ноль ноль": 0}
_ONEHALF = {"полтора": 1, "полторы": 1}
_NUMBER_WORDS = {"units": _UNITS, "teens": _TEENS, "tens": _TENS, "zero": _ZERO, "onehalf": _ONEHALF}

# Russian hundreds are single words («двести» = 200), so every one is a scale word.
_SCALES = {
    "сто": 100,
    "двести": 200,
    "триста": 300,
    "четыреста": 400,
    "пятьсот": 500,
    "шестьсот": 600,
    "семьсот": 700,
    "восемьсот": 800,
    "девятьсот": 900,
}

# 3 to 99: «двадцать пять», «пять» — the tens alternation is wrapped like English's, so the
# optional unit follows any ten, not just the last one.
_SMALL = r"(?:%(num_tens)s)(?:\s+(?:%(num_units)s))?|%(num_teens)s|%(num_units)s"
# «ноль ноль», «ноль-ноль», «ноль пять», «сорок пять», «пятнадцать»
_MINUTE_WORDS = (
    r"(?:%(num_zero)s)(?:\s+(?:%(num_zero)s|%(num_units)s))?"
    r"|(?:%(num_tens)s)(?:\s+(?:%(num_units)s))?|%(num_teens)s"
)
# 1 to 23 as spoken hours: «час», «один», «два», «тринадцать», «двадцать один»
_HOUR_WORDS = r"(?:%(num_tens)s)(?:\s+(?:%(num_units)s))?|%(num_teens)s|%(num_units)s"
# 1 to 999: «двести двадцать пять», «сто», «девяносто девять»
_NUMBER = rf"(?:%(scale)s)(?:\s+(?:{_SMALL}))?|{_SMALL}"


def _unit_forms() -> dict[int, tuple[str, ...]]:
    forms: dict[int, tuple[str, ...]] = {}
    for word, value in _UNITS.items():
        if word in ("час", "минуту", "секунду", "день"):  # bare-unit words, not counting words
            continue
        forms.setdefault(value, ())
        if word not in forms[value]:
            forms[value] = (*forms[value], word)
    return forms


_UNIT_FORMS = _unit_forms()
_TEEN_NAMES = {value: word for word, value in _TEENS.items()}
_TEN_NAMES = {value: word for word, value in _TENS.items()}


def _spell_small(n: int) -> list[str]:
    """Every way the small-number pattern writes ``n`` (1 to 99)."""
    if n < 10:
        return list(_UNIT_FORMS[n])
    if n < 20:
        return [_TEEN_NAMES[n]]
    tens, units = divmod(n, 10)
    if units == 0:
        return [_TEN_NAMES[tens * 10]]
    return [f"{_TEN_NAMES[tens * 10]} {unit}" for unit in _UNIT_FORMS[units]]


def _spellings(n: int) -> list[str]:
    """Every way the number pattern writes ``n`` (1 to 999)."""
    if n < 100:
        return _spell_small(n)
    hundreds = n // 100 * 100
    rest = n - hundreds
    head = next(word for word, value in _SCALES.items() if value == hundreds)
    if rest == 0:
        return [head]
    return [f"{head} {small}" for small in _spell_small(rest)]


def _spelled(numbers: Iterable[int]) -> dict[str, list[dict[str, Any]]]:
    return {"values": [{"in": words, "out": n} for n in numbers for words in _spellings(n)]}


# Sentence triggers. The command is the {command} wildcard; time pieces are range or value
# lists drawn from the parser's own tables, so whatever a template matches the time parser
# understands. A bare hour after 12 still matches, so the parser refuses it instead of
# Assist running the command now.
_CLOCK = "в ({hour}[:{minute}] [{meridiem}]|{hour_word} [{minute_word}] [{meridiem}]|{named})"
_DAYREF = "({day}|в {weekday}) [{period}]"
_COUNT = "({number}|{number_word})"
_ABSOLUTE = [f"{_DAYREF} {_CLOCK}", f"{_CLOCK} {_DAYREF}", _CLOCK]
_RELATIVE = [
    _COUNT.join(("через ", " [с половиной] {unit}")),
    "через {onehalf} {unit}",
    "через (час|минуту|секунду|день)",
    "через (полчаса|пол-часа|пол часа|полминуты|пол-минуты|пол минуты|полдня|пол-дня|пол дня)",
]
_WHAT = "что запланировано"
_JOB_CLOCK = "{hour}[:{minute}] [{meridiem}]"
_JOB_DAY = "[({day}|в {weekday})]"


def _either_side(phrases: list[str]) -> list[str]:
    return [f"{phrase} {{command}}" for phrase in phrases] + [f"{{command}} {phrase}" for phrase in phrases]


def _values(words: Iterable[str]) -> dict[str, list[str]]:
    return {"values": list(words)}


_DAY_WORDS = {
    "сегодня": ("today", None),
    "сегодня утром": ("today", "morning"),
    "сегодня днём": ("today", "afternoon"),
    "сегодня вечером": ("today", "evening"),
    "сегодня ночью": ("today", "night"),
    "завтра": ("tomorrow", None),
    "завтра утром": ("tomorrow", "morning"),
    "завтра днём": ("tomorrow", "afternoon"),
    "завтра вечером": ("tomorrow", "evening"),
    "завтра ночью": ("tomorrow", "night"),
}
_PERIOD_WORDS = {
    "утром": "morning",
    "днём": "afternoon",
    "вечером": "evening",
    "ночью": "night",
}
# Accusative forms, as they stand after «в»: «в пятницу», «во вторник».
_WEEKDAY_WORDS = {
    "понедельник": 0,
    "вторник": 1,
    "среду": 2,
    "четверг": 3,
    "пятницу": 4,
    "субботу": 5,
    "воскресенье": 6,
    "пн": 0,
    "вт": 1,
    "ср": 2,
    "чт": 3,
    "пт": 4,
    "сб": 5,
    "вс": 6,
}
_UNIT_WORDS = {
    "секунда": 1,
    "секунды": 1,
    "секунду": 1,
    "секунд": 1,
    "сек": 1,
    "минута": 60,
    "минуты": 60,
    "минуту": 60,
    "минут": 60,
    "мин": 60,
    "час": 3600,
    "часа": 3600,
    "часу": 3600,
    "часов": 3600,
    "день": 86400,
    "дня": 86400,
    "дню": 86400,
    "дней": 86400,
}
# Genitive forms after «в ...»: «в 6 утра», «в 12 ночи» (which is midnight).
_MERIDIEM_WORDS = {
    "утра": "am",
    "дня": "pm",
    "вечера": "pm",
    "ночи": "am",
}
_NAMED_TIMES = {"полдень": (12, 0), "полночь": (0, 0)}

RU = LanguagePack(
    code="ru",
    time_patterns={
        "relative": [
            r"через\s+(?P<count>%(number)s)(?P<half>\s+с\s+половиной)?\s+(?P<unit>%(unit)s)",
            r"через\s+(?P<count>%(num_onehalf)s)(?P<half>)\s+(?P<unit>%(unit)s)",
            # «через час»: one word is both the count and the unit; the lookbehind is fixed-width.
            r"через\s+(?P<unit>час)(?<=(?P<count>час))(?P<half>\s+с\s+половиной)?",
            r"через\s+(?P<unit>минуту)(?<=(?P<count>минуту))(?P<half>\s+с\s+половиной)?",
            r"через\s+(?P<unit>секунду)(?<=(?P<count>секунду))(?P<half>\s+с\s+половиной)?",
            r"через\s+(?P<unit>день)(?<=(?P<count>день))(?P<half>\s+с\s+половиной)?",
            r"через\s+пол(?:\s+|-)?(?P<halfonly>%(unit)s)",
        ],
        "number": _NUMBER,
        "clock": (
            r"в\s+(?:(?P<named>%(named)s)"
            r"|(?:(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?"
            rf"|(?P<hour_words>{_HOUR_WORDS})(?:\s+(?P<minute_words>{_MINUTE_WORDS}))?)"
            r"(?:\s+(?:часа|часов|час))?(?:\s*(?P<ampm>%(meridiem)s))?)"
        ),
        "dayref": r"(?:(?P<day>%(day)s)|в(?:о)?\s+(?P<weekday>%(weekday)s))(?:\s+(?P<period>%(period)s))?",
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
    number_scales=_SCALES,
    number_fillers=frozenset(),
    run_pattern=r"(?:запусти|выполни|активируй)\s+(?P<name>.+)",
    sentences={
        "run": ["(запусти|выполни|активируй) {name}"],
        "announce_area": [
            "(скажи|объяви|передай) (в|на) {area} [что] {message}",
            "(скажи|объяви|передай) (всем|всех) (в|на) {area} [что] {message}",
            "(скажи|объяви|передай) [что] {message} (в|на) {area}",
            "(скажи|объяви|передай) (всем|всех) [что] {message} (в|на) {area}",
        ],
        "announce_floor": [
            "(скажи|объяви|передай) [(на|в)] {floor} [что] {message}",
            "(скажи|объяви|передай) (всем|всех) [(на|в)] {floor} [что] {message}",
            "(скажи|объяви|передай) [что] {message} [(на|в)] {floor}",
            "(скажи|объяви|передай) (всем|всех) [что] {message} [(на|в)] {floor}",
        ],
        "announce_everyone": [
            "скажи (всем|всех) [что] {message}",
            "передай (всем|всех) [что] {message}",
            "(объяви|объяви всем|объяви на весь дом) [что] {message}",
        ],
        "announce_area_no_message": ["(скажи|объяви|передай) [(всем|всех)] [(в|на)] {area}"],
        "announce_floor_no_message": ["(скажи|объяви|передай) [(всем|всех)] [(на|в)] {floor}"],
        "schedule_absolute": _either_side(_ABSOLUTE),
        "schedule_relative": _either_side(_RELATIVE),
        "list": [_WHAT, f"{_WHAT} {{scope}}", f"{_WHAT} на {{name}}"],
        "cancel": [
            "(отмени|убери) {all}",
            f"(отмени|убери) [задание|задачу|сценарий] (на|в) {_JOB_CLOCK} {_JOB_DAY}",
            f"(отмени|убери) [задание|задачу|сценарий] {_JOB_DAY} (на|в) {_JOB_CLOCK}",
            "(отмени|убери) {name}",
        ],
    },
    sentence_lists={
        "hour": {"range": {"from": 0, "to": 23, "words": False}},
        "minute": {"range": {"from": 0, "to": 59, "words": False}},
        "number": {"range": {"from": 1, "to": 180, "words": False}},
        "number_word": _spelled(range(1, 181)),
        "hour_word": {
            "values": [
                {"in": words, "out": n}
                for n in range(1, 24)
                for words in (["час", "один"] if n == 1 else ["два"] if n == 2 else _spell_small(n))
            ]
        },
        "minute_word": {
            "values": [{"in": word, "out": 0} for word in ("ноль ноль", "ноль-ноль", "нуль нуль")]
            + _spelled(range(10, 60))["values"]
        },
        "unit": _values(_UNIT_WORDS),
        # "out" must be the spoken word itself: _cancel_time rebuilds the cancel time from the
        # slot values, and the Russian parser only knows Russian meridiem words.
        "meridiem": {"values": [{"in": word, "out": word} for word in _MERIDIEM_WORDS]},
        "named": _values(_NAMED_TIMES),
        "day": _values(_DAY_WORDS),
        "period": _values(_PERIOD_WORDS),
        "weekday": _values(_WEEKDAY_WORDS),
        "onehalf": {"values": [{"in": word, "out": 1} for word in _ONEHALF]},
        "scope": {
            "values": [
                {"in": "сегодня", "out": "today"},
                {"in": "сегодня вечером", "out": "tonight"},
                {"in": "вечером", "out": "tonight"},
                {"in": "на вечер", "out": "tonight"},
                {"in": "завтра", "out": "tomorrow"},
                {"in": "на завтра", "out": "tomorrow"},
            ]
        },
        "all": _values(
            ["всё", "все", "все задания", "всё запланированное", "все запланированные задания", "все мои задания"]
        ),
    },
    sentence_clock="в {hour}:{minute:02d} {meridiem}",
    sentence_weekday="в {weekday}",
    summary_verbs={
        "turn_on": "Включу {name}",
        "turn_off": "Выключу {name}",
        "toggle": "Переключу {name}",
        "script.turn_on": "Запущу {name}",
        "automation.trigger": "Запущу {name}",
        # Intent types, for voice jobs
        "AutomationRun": "Запущу {name}",
        "HassTurnOn": "Включу {name}",
        "HassTurnOff": "Выключу {name}",
        "HassToggle": "Переключу {name}",
        "HassLightSet": "Настрою {name}",
        "HassSetPosition": "Настрою {name}",
        "HassClimateSetTemperature": "Настрою {name}",
        "HassClimateSetFanMode": "Настрою {name}",
        "HassFanSetSpeed": "Настрою {name}",
        "HassSetVolume": "Настрою {name}",
        "HassSetVolumeRelative": "Изменю громкость {name}",
        "HassMediaPause": "Поставлю {name} на паузу",
        "HassMediaUnpause": "Возобновлю {name}",
        "HassMediaNext": "Включу следующую дорожку на {name}",
        "HassMediaPrevious": "Верну предыдущую дорожку на {name}",
        "HassMediaPlayerMute": "Уберу звук {name}",
        "HassMediaPlayerUnmute": "Верну звук {name}",
        "HassVacuumStart": "Запущу {name}",
        "HassVacuumReturnToBase": "Отправлю {name} на базу",
        "HassLawnMowerStartMowing": "Запущу {name}",
        "HassLawnMowerDock": "Отправлю {name} на базу",
        "HassBroadcast": "Объявлю всем: «{message}»",
        "PlaceAnnounce": "Объявлю «{message}» ({area})",
        "PlaceAnnounce:floor": "Объявлю «{message}» ({floor})",
        "HassMediaSearchAndPlay": "Включу {search_query} на {name}",
        "HassVacuumCleanArea": "Запущу уборку ({area})",
        "HassListAddItem": "Добавлю {item} в {name}",
        "HassListCompleteItem": "Отмечу {item} в {name}",
        "HassListRemoveItem": "Уберу {item} ({name})",
        "HassShoppingListAddItem": "Добавлю {item} в список покупок",
        "HassShoppingListCompleteItem": "Отмечу {item} в списке покупок",
    },
    # Where «включить» is the wrong verb: run a script, open a cover, lock a lock
    domain_summary_verbs={
        "HassTurnOn:script": "Запущу {name}",
        "HassTurnOn:scene": "Активирую {name}",
        "HassTurnOn:cover": "Открою {name}",
        "HassTurnOff:cover": "Закрою {name}",
        "HassTurnOn:valve": "Открою {name}",
        "HassTurnOff:valve": "Закрою {name}",
        "HassTurnOn:lock": "Заблокирую {name}",
        "HassTurnOff:lock": "Разблокирую {name}",
    },
    generic_action_summary="Выполню действие",
    named_action_summary="{action}: {name}",
    joiner=" и ",
    domain_words={
        "light": "светильники",
        "switch": "выключатели",
        "fan": "вентиляторы",
        "cover": "шторы",
        "climate": "термостаты",
        "media_player": "медиаплееры",
        "vacuum": "пылесосы",
        "lawn_mower": "газонокосилки",
        "valve": "клапаны",
        "lock": "замки",
        "scene": "сцены",
        "script": "сценарии",
    },
    # The place arrives in the nominative; Russian prepositional case cannot be built
    # without morphology, so it goes in parentheses.
    place_target="{things} ({place})",
    recognize_errors={
        "no_match": (
            "Я планирую только команды, которые могу проверить прямо сейчас: называй устройство, "
            "как оно записано в Home Assistant (например, «свет зал»), и указывай время. "
            "Таймеры и вопросы задавай ассистенту напрямую."
        ),
        "refused": (
            "Я планирую только команды, которые могу проверить прямо сейчас: называй устройство, "
            "как оно записано в Home Assistant (например, «свет зал»), и указывай время. "
            "Таймеры и вопросы задавай ассистенту напрямую."
        ),
        "no_target": "Ничего с названием {name} не найдено.",
        "no_target_domain": "Среди {domain} ничего с названием {name} не найдено.",
        "no_message_area": "Что объявить: {area}?",
        "no_message_floor": "Что объявить: {floor}?",
    },
    responses={
        "absolute": "Хорошо{day}, в {time} я {summary}.",
        "relative": "Хорошо, через {duration}, в {time}, я {summary}.",
        "today": " сегодня",
        "yesterday": " вчера",
        "tomorrow": " завтра",
        "weekday": " {weekday}",
        "date": " {day} {month}",
        "weekday_names": [
            "в понедельник",
            "во вторник",
            "в среду",
            "в четверг",
            "в пятницу",
            "в субботу",
            "в воскресенье",
        ],
        "month_names": [
            "января",
            "февраля",
            "марта",
            "апреля",
            "мая",
            "июня",
            "июля",
            "августа",
            "сентября",
            "октября",
            "ноября",
            "декабря",
        ],
        "list_empty": "Ничего не запланировано.",
        "list": "Запланировано: {count}. {items}{more}.",
        "list_item": "{summary} в {time}{day}",
        "list_more": ", и ещё {more}",
        "list_separator": "; ",
        "cancel_one": "Отменено: {item}.",
        "cancel_none": "Не нашлось запланированного задания под этот запрос.",
        "cancel_ambiguous": "Заданий по {name}: {count}. Время: {times}. Скажи «отмени задание {first}».",
        "cancel_ambiguous_by_summary": "Заданий по {name}: {count}: {items}. Скажи «отмени {first}».",
        "cancel_job": "на {time}{day}",
        "cancel_all": "Отменено заданий: {count}.",
        "cancel_all_one": "Отменено задание: {count}.",
        "cancel_all_left": " Заданий, созданных автоматизациями, не тронуто: {count}.",
        "cancel_all_left_one": " Задание, созданное автоматизацией, не тронуто: {count}.",
        "bad_time": (
            "Не удалось разобрать время. Укажи его так: «через 10 минут», «в 18:30» "
            "или «завтра в 7 утра»."
        ),
        "announced": "Готово",
        "spoken_time": format_spoken_time,
        "duration": format_duration,
    },
    logbook={
        "scheduled": "запланировано {summary} на {time}",
        "executed": "выполнено: {summary}",
        "failed": "не выполнено: {summary}: {error}",
        "failed_no_error": "не выполнено: {summary}",
        "cancelled": "отменено: {summary}",
        "missed": "пропущено: {summary} (Home Assistant был недоступен)",
    },
    messages={
        # Why a job failed (core/executor.py, ha_internal/intents.py)
        "nothing_to_run": "в задании нет действия для запуска",
        "user_gone": "Пользователь, создавший это задание, больше не существует",
        "entity_unavailable": "Объект {entity_id} недоступен",
        "entity_gone": "Объекта {entity_id} больше нет",
        "action_invalid": "{action}: сохранённое действие недействительно: {error}",
        "action_failed": "{summary}: {error}",
        "intent_not_exposed": "{intent}: {target} не показан голосовым ассистентам",
        "intent_not_found": "{intent}: {target} не найден ({reason})",
        "intent_no_match": "нет совпадения",
        "automation_triggered": "Запущено: {name}",
        "intent_gone": "{intent}: этого интента больше нет",
        "intent_failed": "{intent} для {target} завершился с ошибкой: {error}",
        # Why a picked action was refused (core/actions.py)
        "action_one_step": "действие должно состоять ровно из одного шага",
        "action_step_mapping": "шаг должен быть сопоставлением",
        "action_step_service": "шаг должен вызывать сервис",
        "action_extra_keys": "{name} не допускает {keys}",
        "target_missing": "{name} требует цель",
        "target_extra_keys": "цель {name} не допускает {keys}",
        "target_ids_strings": "идентификаторы цели {name} должны быть строками",
        "target_specific": "цель {name} должна указывать конкретные идентификаторы",
        "templates_admin_only": "Шаблоны доступны только администраторам",
        "data_mapping": "данные {name} должны быть сопоставлением",
        # Voice intents
        "not_set_up": "Извини, планирование не настроено.",
    },
    todo={
        "done": "Выполнено",
        "failed": "Ошибка: {error}",
        "failed_no_error": "Ошибка",
        "missed": "Пропущено",
        "cancelled": "Отменено",
    },
)
