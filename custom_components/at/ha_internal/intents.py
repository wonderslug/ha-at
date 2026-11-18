"""Run a stored intent later, with exposure checked again at fire time."""

from typing import TYPE_CHECKING, Any

from custom_components.at.core.errors import JobExecutionError
from custom_components.at.lang import get_language_pack, message
from homeassistant.components import conversation
from homeassistant.helpers import device_registry as dr, intent

if TYPE_CHECKING:
    from custom_components.at.core.models import IntentSpec
    from homeassistant.core import Context, HomeAssistant

ASSISTANT = conversation.DOMAIN
_TARGET_SLOTS = ("name", "area", "floor")


def _slot_value(slot: Any) -> Any:
    return slot.get("value") if isinstance(slot, dict) else slot


def _target_name(spec: IntentSpec) -> str:
    """Name what the intent aims at, for error messages."""
    parts = [str(value) for key in _TARGET_SLOTS if (value := _slot_value(spec.slots.get(key))) is not None]
    return " ".join(parts) if parts else spec.type


def _slots_with_area(hass: HomeAssistant, spec: IntentSpec) -> dict[str, Any]:
    """Return the stored slots plus the satellite's area, as the default agent adds it."""
    slots = dict(spec.slots)
    if "preferred_area_id" not in slots and spec.device_id:
        device = dr.async_get(hass).async_get(spec.device_id)
        if device is not None and device.area_id:
            slots["preferred_area_id"] = {"value": device.area_id}
    return slots


async def async_run_intent(hass: HomeAssistant, spec: IntentSpec, context: Context) -> None:
    """
    Run a stored intent now.

    Raises:
        JobExecutionError: The intent could not be matched, was not exposed, or failed.

    """
    target = _target_name(spec)
    pack = get_language_pack(hass.config.language)
    try:
        response = await intent.async_handle(
            hass,
            ASSISTANT,
            spec.type,
            _slots_with_area(hass, spec),
            None,
            context,
            spec.language,
            assistant=ASSISTANT,
            device_id=spec.device_id,
            satellite_id=spec.satellite_id,
        )
    except intent.MatchFailedError as err:
        reason = err.result.no_match_reason
        if reason is intent.MatchFailedReason.ASSISTANT:
            text = message(pack, "intent_not_exposed", intent=spec.type, target=target)
        else:
            why = reason.name if reason else message(pack, "intent_no_match")
            text = message(pack, "intent_not_found", intent=spec.type, target=target, reason=why)
        raise JobExecutionError(text) from err
    except intent.UnknownIntent as err:
        raise JobExecutionError(message(pack, "intent_gone", intent=spec.type)) from err
    except intent.IntentError as err:
        raise JobExecutionError(message(pack, "intent_failed", intent=spec.type, target=target, error=err)) from err
    if response.response_type is intent.IntentResponseType.ERROR:
        raise JobExecutionError(
            message(pack, "intent_failed", intent=spec.type, target=target, error=response.error_code)
        )


def probe() -> dict[str, bool]:
    """Report whether the Home Assistant hooks this adapter uses resolved."""
    return {
        "async_handle": hasattr(intent, "async_handle"),
        "match_failed_error": hasattr(intent, "MatchFailedError"),
        "unknown_intent": hasattr(intent, "UnknownIntent"),
    }
