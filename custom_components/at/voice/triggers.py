"""Built-in agent sentence triggers: each one hands its slots to the AtSchedule, AtList or AtCancel intent."""

from collections.abc import Callable
from typing import Any

from custom_components.at.const import DOMAIN, LOGGER
from custom_components.at.ha_internal.fallthrough import async_hand_off
from custom_components.at.ha_internal.sentence_triggers import (
    SentenceGroup,
    TriggerInput,
    async_register_sentence_triggers,
)
from custom_components.at.lang import LanguagePack
from custom_components.at.voice.intents import INTENT_CANCEL, INTENT_LIST, INTENT_SCHEDULE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent


async def _async_respond(
    hass: HomeAssistant, intent_type: str, slots: dict[str, Any], given: TriggerInput
) -> intent.IntentResponse:
    return await intent.async_handle(
        hass,
        DOMAIN,
        intent_type,
        {name: {"value": value} for name, value in slots.items() if value is not None},
        text_input=given.sentence,
        context=given.context,
        language=given.language,
        device_id=given.device_id,
        satellite_id=given.satellite_id,
        conversation_agent_id=given.agent_id,
    )


def _speech(response: intent.IntentResponse) -> str:
    return str(response.speech.get("plain", {}).get("speech", ""))


async def _async_handle(hass: HomeAssistant, intent_type: str, slots: dict[str, Any], given: TriggerInput) -> str:
    return _speech(await _async_respond(hass, intent_type, slots, given))


def _cancel_time(pack: LanguagePack, wildcards: dict[str, str]) -> str | None:
    if "hour" not in wildcards:
        return None
    clock = pack.sentence_clock.format(
        hour=int(wildcards["hour"]),
        minute=int(wildcards.get("minute", "0")),
        meridiem=wildcards.get("meridiem", ""),
    ).strip()
    if "day" in wildcards:
        return f"{clock} {wildcards['day']}"
    if "weekday" in wildcards:
        return f"{clock} {pack.sentence_weekday.format(weekday=wildcards['weekday'])}"
    return clock


def async_setup_triggers(hass: HomeAssistant, pack: LanguagePack, *, defer_relative: bool) -> Callable[[], None]:
    """
    Register the schedule, list and cancel sentences for one language.

    With ``defer_relative`` the relative-time schedule sentences are left out, so Home
    Assistant's own delayed commands answer them. A schedule sentence whose command Assist
    doesn't know ("remind me at 5") goes back, whole, to the agent it was meant for.

    Returns:
        The callback that unregisters every sentence.

    """
    sentences = pack.sentences

    async def hand_off_or(given: TriggerInput, refusal: str) -> str:
        """Let the sentence's own agent answer it, and refuse only when nothing else can."""
        try:
            speech = await async_hand_off(hass, given)
        except Exception:  # noqa: BLE001 - another agent's code; whatever it raises, the user still gets an answer
            LOGGER.exception("Handing %r back to its agent failed", given.sentence)
            return pack.recognize_errors["no_match"]
        return refusal if speech is None else speech

    async def schedule(given: TriggerInput) -> str:
        slots = {"time": given.sentence_without("command"), "command": given.wildcards["command"]}
        response = await _async_respond(hass, INTENT_SCHEDULE, slots, given)
        if response.error_code is intent.IntentResponseErrorCode.NO_INTENT_MATCH:
            return await hand_off_or(given, _speech(response))
        return _speech(response)

    async def unparsed(given: TriggerInput) -> str:
        return await hand_off_or(given, pack.recognize_errors["no_match"])

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
    return async_register_sentence_triggers(
        hass, groups, lists=pack.sentence_lists, language=pack.code, unparsed=unparsed
    )
