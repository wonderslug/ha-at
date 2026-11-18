"""Built-in agent sentence triggers: each one hands its slots to the AtSchedule, AtList or AtCancel intent."""

from collections.abc import Callable
from typing import Any

from custom_components.at.const import DOMAIN
from custom_components.at.ha_internal.sentence_triggers import (
    SentenceGroup,
    TriggerInput,
    async_register_sentence_triggers,
)
from custom_components.at.lang import LanguagePack
from custom_components.at.voice.intents import INTENT_CANCEL, INTENT_LIST, INTENT_SCHEDULE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent


async def _async_handle(hass: HomeAssistant, intent_type: str, slots: dict[str, Any], given: TriggerInput) -> str:
    response = await intent.async_handle(
        hass,
        DOMAIN,
        intent_type,
        {name: {"value": value} for name, value in slots.items() if value is not None},
        text_input=given.sentence,
        context=given.context,
        language=given.language,
        device_id=given.device_id,
        satellite_id=given.satellite_id,
    )
    return str(response.speech.get("plain", {}).get("speech", ""))


def _cancel_time(pack: LanguagePack, wildcards: dict[str, str]) -> str | None:
    if "hour" not in wildcards:
        return None
    return pack.sentence_clock.format(
        hour=int(wildcards["hour"]),
        minute=int(wildcards.get("minute", "0")),
        meridiem=wildcards.get("meridiem", ""),
    ).strip()


def async_setup_triggers(hass: HomeAssistant, pack: LanguagePack, *, defer_relative: bool) -> Callable[[], None]:
    """
    Register the schedule, list and cancel sentences for one language.

    With ``defer_relative`` the relative-time schedule sentences are left out, so Home
    Assistant's own delayed commands answer them.

    Returns:
        The callback that unregisters every sentence.

    """
    sentences = pack.sentences

    async def schedule(given: TriggerInput) -> str:
        slots = {"time": given.sentence_without("command"), "command": given.wildcards["command"]}
        return await _async_handle(hass, INTENT_SCHEDULE, slots, given)

    async def list_jobs(given: TriggerInput) -> str:
        slots = {"scope": given.wildcards.get("scope"), "name": given.wildcards.get("name")}
        return await _async_handle(hass, INTENT_LIST, slots, given)

    async def cancel(given: TriggerInput) -> str:
        slots = {
            "all": True if "all" in given.wildcards else None,
            "name": given.wildcards.get("name"),
            "time": _cancel_time(pack, given.wildcards),
        }
        return await _async_handle(hass, INTENT_CANCEL, slots, given)

    schedule_sentences = [*sentences["schedule_absolute"]]
    if not defer_relative:
        schedule_sentences += sentences["schedule_relative"]
    groups = [
        SentenceGroup(sentences["cancel"], cancel),
        SentenceGroup(sentences["list"], list_jobs),
        SentenceGroup(schedule_sentences, schedule),
    ]
    return async_register_sentence_triggers(hass, groups, lists=pack.sentence_lists, language=pack.code)
