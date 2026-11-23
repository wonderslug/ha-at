"""Built-in agent sentence triggers: schedule, list, cancel, run an automation, and announce."""

from collections.abc import Callable, Sequence
import re
from typing import Any

from custom_components.at.const import DOMAIN, INTENT_AUTOMATION_RUN, LOGGER
from custom_components.at.core.timeparse import TimeParseError, split_time_and_command
from custom_components.at.ha_internal.fallthrough import async_hand_off, async_no_intent_speech
from custom_components.at.ha_internal.recognize import RecognizeError, async_recognize_command
from custom_components.at.ha_internal.sentence_triggers import (
    LanguageSentences,
    SentenceGroup,
    TriggerInput,
    async_register_sentence_triggers,
)
from custom_components.at.lang import LanguagePack
from custom_components.at.voice.announce import parse_announcement, trigger_sentences
from custom_components.at.voice.intents import INTENT_CANCEL, INTENT_LIST, INTENT_SCHEDULE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent

# The built-in agent's own last resort, for a language Home Assistant has no sentences for either.
_NOT_UNDERSTOOD = "Sorry, I couldn't understand that"


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


def async_setup_triggers(
    hass: HomeAssistant, packs: Sequence[LanguagePack], *, defer_relative: bool
) -> Callable[[], None]:
    """
    Register the schedule, list and cancel sentences of every language pack.

    Each spoken sentence is answered in its own pipeline's language. A sentence in a language
    with no pack goes back, whole, to the agent it was meant for, as if `at` weren't installed.

    Returns:
        The callback that unregisters every sentence.

    """

    async def other_language(given: TriggerInput) -> str:
        try:
            speech = await async_hand_off(hass, given)
        except Exception:  # noqa: BLE001 - another agent's code; whatever it raises, the user still gets an answer
            LOGGER.exception("Handing %r back to its agent failed", given.sentence)
            speech = None
        return speech or await async_no_intent_speech(hass, given.language) or _NOT_UNDERSTOOD

    return async_register_sentence_triggers(
        hass,
        [_language_sentences(hass, pack, defer_relative=defer_relative) for pack in packs],
        other_language=other_language,
    )


def _language_sentences(hass: HomeAssistant, pack: LanguagePack, *, defer_relative: bool) -> LanguageSentences:
    """
    Build one language's schedule, list and cancel sentences and their callbacks.

    With ``defer_relative`` the relative-time schedule sentences are left out, so Home
    Assistant's own delayed commands answer them. A schedule sentence whose command Assist
    doesn't know ("remind me at 5") goes back, whole, to the agent it was meant for.

    Returns:
        The sentences, ready to register.

    """

    async def hand_off_or(given: TriggerInput, refusal: str) -> str:
        """Let the sentence's own agent answer it, and refuse only when nothing else can."""
        try:
            speech = await async_hand_off(hass, given)
        except Exception:  # noqa: BLE001 - another agent's code; whatever it raises, the user still gets an answer
            LOGGER.exception("Handing %r back to its agent failed", given.sentence)
            return pack.recognize_errors["no_match"]
        return refusal if speech is None else speech

    async def announce(given: TriggerInput) -> str:
        """Announce now; a sentence that turns out not to be an announcement goes back to its agent."""
        if (announcement := parse_announcement(hass, pack, given.sentence)) is None:
            return await hand_off_or(given, pack.recognize_errors["no_match"])
        try:
            command = await async_recognize_command(
                hass,
                given.sentence,
                language=given.language,
                device_id=given.device_id,
                satellite_id=given.satellite_id,
                context=given.context,
                pack=pack,
            )
        except RecognizeError as err:
            return err.message
        slots = {name: slot["value"] for name, slot in command.intent.slots.items() if name in announcement.slots}
        await _async_respond(hass, command.intent.type, slots, given)
        return str(pack.responses["announced"])

    async def schedule(given: TriggerInput) -> str:
        slots = {"time": given.sentence_without("command"), "command": given.wildcards["command"]}
        response = await _async_respond(hass, INTENT_SCHEDULE, slots, given)
        if response.error_code is intent.IntentResponseErrorCode.NO_INTENT_MATCH:
            # "tell everyone dinner is at 6": the time is part of the message, so announce it now.
            if parse_announcement(hass, pack, given.sentence) is not None:
                return await announce(given)
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

    async def run(given: TriggerInput) -> str:
        name = given.wildcards["name"].strip()
        try:
            return _speech(
                await _async_respond(
                    hass,
                    INTENT_AUTOMATION_RUN,
                    {"name": re.sub(r"\s+automation$", "", name, flags=re.IGNORECASE)},
                    given,
                )
            )
        except intent.MatchFailedError:
            pass
        try:
            _, rest = split_time_and_command(name, pack)
        except TimeParseError:
            return await hand_off_or(given, pack.recognize_errors["no_target"].format(name=name))
        # "run X in 30 minutes" also fits this sentence, so route it to scheduling.
        slots = {
            "time": name.replace(rest, "", 1).strip(),
            "command": f"{given.sentence[: given.spans['name'][0]]}{rest}".strip(),
        }
        response = await _async_respond(hass, INTENT_SCHEDULE, slots, given)
        if response.error_code is intent.IntentResponseErrorCode.NO_INTENT_MATCH:
            return await hand_off_or(given, _speech(response))
        return _speech(response)

    callbacks = {"cancel": cancel, "list": list_jobs, "announce": announce, "schedule": schedule, "run": run}
    groups = [
        SentenceGroup(name, group_sentences, callbacks[name])
        for name, group_sentences in sentence_groups(pack, defer_relative=defer_relative)
    ]
    return LanguageSentences(pack.code, groups, pack.sentence_lists, unparsed)


def sentence_groups(pack: LanguagePack, *, defer_relative: bool) -> list[tuple[str, list[str]]]:
    """
    Name each group of sentence templates a pack registers, in registration order.

    With ``defer_relative`` the relative-time schedule sentences are left out.

    Returns:
        ``(name, sentences)`` pairs for cancel, list, announce, schedule and run.

    """
    sentences = pack.sentences
    schedule_sentences = [*sentences["schedule_absolute"]]
    if not defer_relative:
        schedule_sentences += sentences["schedule_relative"]
    return [
        ("cancel", sentences["cancel"]),
        ("list", sentences["list"]),
        ("announce", trigger_sentences(pack)),
        ("schedule", schedule_sentences),
        ("run", sentences["run"]),
    ]
