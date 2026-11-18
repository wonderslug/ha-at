# Spike findings: the Home Assistant internals `at` depends on

**Tested on:** Home Assistant **2026.10.4**, hassil 3.12.1, home-assistant-intents 2026.10.6, Python 3.14,
pytest-homeassistant-custom-component (in `.venv`), 2026-11-17.

**Contract tests:** [`tests/spike/test_ha_internals.py`](../../tests/spike/test_ha_internals.py). They stay in the repo,
so a Home Assistant upgrade that breaks one of these internals fails CI. Run them with:

```bash
uv run pytest tests/spike -v
```

| #   | Item (spec §10)                                                                 | Result                                                          | Test                                                                                                                       |
| --- | ------------------------------------------------------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| 1   | Programmatic sentence triggers, wildcard + range list, both orders              | **PASS** (needs a private-contract step)                        | `test_programmatic_sentence_trigger_wildcard_both_orders`, fallback `test_trigger_with_literal_hours_uses_only_public_api` |
| 2   | Recognize without executing, with device/area context, distinguishable failures | **PASS**                                                        | `test_recognize_only_returns_intent_without_executing`                                                                     |
| 3   | Run a stored (JSON) intent later, exposure re-checked                           | **PASS**                                                        | `test_run_stored_intent_later`                                                                                             |
| 4   | Custom intents offered as LLM tools                                             | **PASS, but not automatically** (needs an `llm.py` platform)    | `test_custom_intent_offered_to_llm_api`                                                                                    |
| 5   | Sentence triggers fire with an LLM agent and prefer-local                       | **PASS** (prefer-local on _and_ off)                            | `test_sentence_trigger_fires_with_prefer_local_llm_pipeline[...]`                                                          |
| 6   | `panel_custom` registration from a custom integration                           | **PASS** (registration only; picker loading is manual, Task 21) | `test_panel_custom_registers`                                                                                              |

**Go/no-go: GO.** Items 1, 2 and 3 work. Task 15 is not deferred (item 4 works through an `llm` platform). No
"LLM tools only" caveat is needed for Task 23 (item 5 works).

## Test harness notes

- The tests are marked `@pytest.mark.real_dependencies` (module-level `pytestmark`), which turns off the autouse fixture
  in `tests/conftest.py` that fakes `conversation`, `intent`, `http`, `frontend` and `panel_custom` as loaded.
- **Real `http` works under pytest.** The only obstacle: `homeassistant/components/http/server.py` does
  `self.app["hass"] = self.hass`, which raises `aiohttp.web_exceptions.NotAppKeyWarning`, and `pyproject.toml` turns
  every warning into an error, so `http` setup failed. The fix is a module-level
  `pytest.mark.filterwarnings("ignore::aiohttp.web_exceptions.NotAppKeyWarning")`. No server port is opened
  (sockets stay blocked); nothing else is mocked. Consider adding that filter to `pyproject.toml` next to the other
  Core aiohttp ignores when voice tests arrive (Task 13+).
- `async_setup_component(hass, "conversation", {})` pulls in `http`, `intent` and `llm`. `assist_pipeline` pulls in
  `stt`, `tts`, `wake_word` and `ffmpeg`; all set up fine. `panel_custom` pulls in the full `frontend` (and
  `hass_frontend` is installed), which also sets up fine.
- Lights are entity-registry entries (`er.async_get_or_create(..., original_name="Kitchen light")`) plus
  `hass.states.async_set(...)`, the same approach as Core's conversation tests. `light.turn_on` is replaced with
  `async_mock_service`, so "the light turned on" is asserted as a `light.turn_on` service call for `light.kitchen`, and
  "unchanged" as no call plus state still `off`. The brief mentioned a script; no item needed one, so there is none.
- Exposure: `homeassistant.components.homeassistant.exposed_entities.async_expose_entity(hass, "conversation",
entity_id, should_expose)` (public; needs the `homeassistant` component set up).

## Item 1: programmatic sentence triggers (PASS)

**What works:** the patterns `at {hour} {command}` and `{command} at {hour}`, with `hour` a 1-12 range list and
`command` a wildcard, registered from code, nothing written to `config/`. "at 11 turn on the kitchen light", "turn on
the kitchen light at 11" and "at eleven turn on the kitchen light" all fire the callback with
`command == "turn on the kitchen light"` and `hour == 11`; the light is not touched. "turn on the kitchen light at 13"
(outside the range) does not match the trigger and goes to normal Assist handling. Unregistering works.

**APIs used:**

| Symbol                           | Module                                                | Signature                                                                                                                                  | Public?                                                                                                                               |
| -------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| `get_agent_manager`              | `homeassistant.components.conversation.agent_manager` | `get_agent_manager(hass) -> AgentManager` (singleton, `@callback`)                                                                         | Semi-public: no underscore, not in `conversation.__all__`. Core's own `conversation/trigger.py` uses it.                              |
| `AgentManager.register_trigger`  | same                                                  | `register_trigger(self, sentences: list[str], trigger_callback: TRIGGER_CALLBACK_TYPE) -> CALLBACK_TYPE` (returns the unregister callback) | Semi-public: no underscore, undocumented. This is exactly what a `conversation` automation trigger calls.                             |
| `TRIGGER_CALLBACK_TYPE`          | `homeassistant.components.conversation.trigger`       | `Callable[[ConversationInput, RecognizeResult], Awaitable[str \| None]]`                                                                   | Semi-public. Return a string to set the spoken response; `None` means "no response from me" (falls back to "Done" if nobody answers). |
| `AgentManager.subscribe_intents` | `...conversation.agent_manager`                       | `subscribe_intents(self, subscriber: Callable[[dict[IntentSource, IntentSourceConfig]], None]) -> CALLBACK_TYPE`                           | Semi-public. Called **immediately** with the full, _live_ intents dict.                                                               |
| `IntentSource`                   | `homeassistant.components.conversation.const`         | `StrEnum`: `CONFIG = "config"`, `TRIGGER = "trigger"`                                                                                      | Semi-public.                                                                                                                          |
| `RecognizeResult`                | `hassil.recognize`                                    | `.entities: dict[str, MatchEntity]` (`.value`, `.text`), `.intent.name`                                                                    | Public (hassil).                                                                                                                      |

**Gotcha 1 (the important one): every `{slot}` in a trigger sentence is a wildcard.**
`DefaultAgent._rebuild_trigger_intents()` collects every list reference in every trigger sentence and sets
`trigger_intents.slot_lists[name] = WildcardSlotList(name)`. There is no public way to pass a range list. With pure
wildcards, hassil cannot split two adjacent wildcards: `at {hour} {command}` **does not match** "at 11 turn on the
kitchen light" at all (verified directly with hassil), and `{command} at {hour}` matches nonsense such as "turn on the
light at home" (`hour == "home"`).

**How the test gets real range lists (`register_at_trigger` in the test file, the prototype for the adapter):**

1. `unregister = get_agent_manager(hass).register_trigger(sentences=sentences, trigger_callback=cb)`.
2. Get the live intents dict: `live = {}; manager.subscribe_intents(live.update)()` (subscribe, which calls back
   immediately, then unsubscribe at once).
3. In `live[IntentSource.TRIGGER]["intents"]`, find the data block whose `"sentences"` **is** (identity) the list just
   passed. `register_trigger` stores it as `{"HassSentenceTrigger<N>": {"data": [{"sentences": sentences}]}}`.
4. Set `data["lists"] = {"hour": {"range": {"from": 1, "to": 12}}}`.

This works because hassil's `Intents.from_dict` parses a per-data `lists` key, and in `hassil.recognize`
data-level `slot_lists` override intent-level ones (`{**slot_lists, **intent_data.slot_lists}`), so they beat the
wildcards. The lists are scoped to our trigger only; other users' triggers that use `{hour}` keep their wildcard.

What this relies on (private contract, pin it in `ha_internal/` and keep this test):

- `register_trigger` storing the caller's `sentences` list object inside `{"data": [{"sentences": ...}]}` under
  `IntentSource.TRIGGER`;
- `subscribe_intents` handing out the live dict, not a copy;
- the default agent rebuilding trigger intents **lazily** (`_update_intents` sets `self._trigger_intents = None`, and the
  rebuild happens at the next `async_recognize_sentence_trigger`). Inject the lists synchronously right after
  `register_trigger`, with no `await` in between. If the dict is ever changed later, nothing forces a rebuild (that
  would need the private `AgentManager._notify_intents_subscribers(IntentSource.TRIGGER)`).

**Fallback that uses only `register_trigger` (also tested):** put the hour in the trigger as literal alternatives,
`at (1|2|...|12) {command}` and `{command} at (1|...|12)`, then re-parse `user_input.text` in the callback with `at`'s
own `hassil.Intents` (real range lists plus a `{"wildcard": True}` command list) via `hassil.recognize_best`. No
private dict access. The cost: the trigger sentence gets long once minutes, AM/PM and number words are spelled out, and
`at` parses each sentence twice. Use this if the injection above ever breaks.

**Other gotchas:**

- Range values come back as **float for digits** (`11.0`) and **int for words** (`11` from "eleven"). Normalise with
  `int(...)`.
- Wildcard values come back stripped of surrounding whitespace in `result.entities[...].value`.
- A matched trigger takes the sentence away from intent handling entirely (`DefaultAgent._async_handle_message` checks
  triggers first). If the callback decides the sentence is not really an `at` command, it cannot hand it back; it must
  answer itself. So keep the patterns tight (that is why a range list beats a wildcard hour).
- If several triggers match, all their callbacks run (`asyncio.as_completed`), and the first non-`None` string wins.
- The trigger language is `hass.config.language` (`_rebuild_trigger_intents` uses it); range-list number words follow
  it.
- `sentences` are validated only by the automation trigger schema, not by `register_trigger`. Run them through
  `homeassistant.components.conversation.trigger.has_no_punctuation` / `is_valid_sentence` in tests.

## Item 2: recognize without executing (PASS)

**What works:** `DefaultAgent.async_recognize_intent(ConversationInput(text="turn on the kitchen light",
device_id=<satellite in the Office area>, ...))` returns a `RecognizeResult` with `intent.name == "HassTurnOn"` and
`entities["name"].value == "Kitchen light"`, and calls no service. The failures are distinguishable:

| Input                                    | `async_recognize_intent` result                                  | `intent.async_match_targets(...)`                               |
| ---------------------------------------- | ---------------------------------------------------------------- | --------------------------------------------------------------- |
| "turn on the kitchen light" (exposed)    | result, `unmatched_entities` empty                               | `is_match=True`                                                 |
| "turn on the garage light" (not exposed) | result, `unmatched_entities` empty (matched against _all_ names) | `is_match=False`, `no_match_reason=MatchFailedReason.ASSISTANT` |
| "turn on the zzz light" (unknown name)   | result, `unmatched_entities["name"].text.strip() == "zzz"`       | `is_match=False`, `MatchFailedReason.NAME`                      |
| "sing me a song about turnips"           | `None` (no intent)                                               | n/a                                                             |

**APIs used:**

| Symbol                                     | Module                                                | Signature                                                                                                                                                                                         | Public?                                                                                                                                                                    |
| ------------------------------------------ | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `AgentManager.default_agent`               | `...conversation.agent_manager`                       | attribute, `DefaultAgent \| None`                                                                                                                                                                 | Semi-public. `conversation.async_get_agent(hass)` (no agent id) returns the same object and is exported from `agent_manager`, but is not in `conversation.__all__` either. |
| `DefaultAgent.async_recognize_intent`      | `homeassistant.components.conversation.default_agent` | `async_recognize_intent(self, user_input: ConversationInput, strict_intents_only: bool = False) -> RecognizeResult \| None`                                                                       | Semi-public: no underscore, undocumented. Used by Core's debug websocket (`async_debug_recognize`) and pipeline code.                                                      |
| `ConversationInput`                        | `homeassistant.components.conversation`               | dataclass: `text, context, conversation_id, device_id, satellite_id, language, agent_id, extra_system_prompt=None`                                                                                | Public (`__all__`).                                                                                                                                                        |
| `intent.async_match_targets`               | `homeassistant.helpers.intent`                        | `async_match_targets(hass, constraints: MatchTargetsConstraints, preferences: MatchTargetsPreferences \| None = None, states=None, area_candidate_filter=...) -> MatchTargetsResult`              | Public helper (no underscore), used by every Assist handler.                                                                                                               |
| `MatchTargetsConstraints`                  | `homeassistant.helpers.intent`                        | dataclass: `name, area_name, floor_name, domains, device_classes, features, states, assistant, allow_duplicate_names, single_target`                                                              | Public. Set `assistant="conversation"` to check exposure.                                                                                                                  |
| `MatchTargetsResult` / `MatchFailedReason` | same                                                  | `is_match, no_match_reason, states, no_match_name, areas, floors`; reasons `NAME, AREA, FLOOR, DOMAIN, DEVICE_CLASS, FEATURE, STATE, ASSISTANT, INVALID_AREA, INVALID_FLOOR, DUPLICATE_NAME, ...` | Public.                                                                                                                                                                    |

**Gotchas:**

- **Recognition alone does not check exposure.** `async_recognize_intent` (non-strict) first tries exposed names, then
  _unexposed_ names (so it can say "not exposed" later), then unknown names. An unexposed match looks exactly like an
  exposed one. Check targets with `intent.async_match_targets(..., assistant="conversation")` (or `strict_intents_only=True`,
  which returns `None` for both unexposed and unknown names, so it can't tell them apart).
- **Intent cache trap:** the default agent caches by `(text, language, satellite_id, device_id)` and stage. Calling
  `strict_intents_only=True` **first** and then non-strict for the same text returns `None` from the non-strict call
  (the cached "exposed stage = no match" entry makes it skip the later stages). Call non-strict first, or only
  non-strict. Non-strict first, then strict, gives the right answers.
- **Area beats name:** with an area named "Kitchen", "turn on the kitchen light" was recognized as
  `{area: Kitchen, domain: light}` (template `<turn> on [<all>] [<the>] {area} <light>`), not as the entity named
  "Kitchen light". The spike moved the satellite to an "Office" area to get the name match. `at` must accept either
  shape; it should store whatever slots HA recognized and let the handler resolve them, as Assist would.
- Entities with a registry entry get their names from the registry (`er.async_get_entity_aliases`), not from the
  `friendly_name` state attribute. Test entities need `original_name` (or `name`) in the registry.
- Building the slot dict for item 3 mirrors `DefaultAgent._async_process_intent_result`:
  `{e.name: {"value": e.value, "text": e.text or e.value} for e in result.entities_list}`.
- The default agent's own error wording lives in private helpers (`_get_unmatched_response`, `_get_match_error_response`,
  `_get_error_text`, `ErrorKey`). Reusing HA's wording (spec §5.2 step 5) means calling private code or copying the
  `error_responses` strings from `lang_intents`. `DefaultAgent.async_get_or_load_intents(language)` (semi-public) returns
  `LanguageIntents` with `.error_responses`.
- `async_debug_recognize(user_input)` exists (the dev-tools "recognize without executing" endpoint) but returns a
  display dict, and checks sentence triggers first; it would match `at`'s own trigger. Not useful for us.

## Item 3: run a stored intent later (PASS)

**What works:** the intent type and slots from item 2, `json.dumps`'d and `json.loads`'d, run through
`intent.async_handle(hass, "conversation", "HassTurnOn", slots, "turn on the kitchen light", Context(), "en",
assistant="conversation", device_id=<satellite>)`. Response type `ACTION_DONE`, and `light.turn_on` is called for
`light.kitchen`. After `async_expose_entity(hass, "conversation", "light.kitchen", False)`, the same call raises
`intent.MatchFailedError` with `result.no_match_reason is MatchFailedReason.ASSISTANT`, and no service is called.

**APIs used:**

| Symbol                                                                                                       | Module                         | Signature                                                                                                                                                                                                                                                                                                                                     | Public? |
| ------------------------------------------------------------------------------------------------------------ | ------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- |
| `intent.async_handle`                                                                                        | `homeassistant.helpers.intent` | `async_handle(hass, platform: str, intent_type: str, slots: dict \| None = None, text_input: str \| None = None, context: Context \| None = None, language: str \| None = None, assistant: str \| None = None, device_id: str \| None = None, satellite_id: str \| None = None, conversation_agent_id: str \| None = None) -> IntentResponse` | Public. |
| `intent.MatchFailedError`                                                                                    | same                           | `.result: MatchTargetsResult`, `.constraints`, `.preferences`                                                                                                                                                                                                                                                                                 | Public. |
| `intent.IntentHandleError`, `intent.IntentUnexpectedError`, `intent.UnknownIntent`, `intent.InvalidSlotInfo` | same                           | exceptions                                                                                                                                                                                                                                                                                                                                    | Public. |
| `IntentResponse.response_type`                                                                               | same                           | `IntentResponseType.ACTION_DONE / QUERY_ANSWER / ERROR`                                                                                                                                                                                                                                                                                       | Public. |

**Gotchas:**

- Exposure is enforced only because `assistant="conversation"` is passed; without it the handler matches unexposed
  entities too.
- Failure to match **raises** (`MatchFailedError`); it does not return an error response. The default agent converts it
  to an error response itself. `at`'s fire path must catch `MatchFailedError`, `IntentHandleError`,
  `IntentUnexpectedError` and `UnknownIntent` (an intent that disappeared, for example after its integration was
  removed).
- The default agent adds `"preferred_area_id": {"value": <satellite area id>}` to the slots when the satellite has an
  area (`DefaultAgent._async_execute_intent`). Store it with the job, or recompute it from the stored `device_id`, so
  "turn on the lights" picks the same area at fire time.
- `platform` is `"conversation"` (what the default agent passes). Handlers may filter on `platforms`.
- `HassTurnOn` on a `light` calls `light.turn_on` with `entity_id` as a **list** (`[["light.kitchen"]]` in the calls).
- The slot values must be JSON-safe: hassil range values are floats/ints, names and areas are strings. They
  round-trip unchanged.

## Item 4: custom intents as LLM tools (PASS, needs an `llm` platform)

**Big change from older HA:** in 2026.10 the Assist LLM API (`homeassistant.components.llm.AssistAPI`) does **not**
turn every registered intent into a tool any more. Tools come from per-integration **`llm.py` platforms**. Registering
`AtSchedule` with `intent.async_register` alone gives **no** tool (asserted in the test). The `intent` integration only
offers its own fixed list (`HassTurnOn`, `HassTurnOff`, timers, ...), each named `intent__<IntentType>`.

**What works:** an `llm` platform for `at` whose `async_get_tools` returns
`LLMTools(tools=[llm.IntentTool("at__AtSchedule", handler, integration="at")])`. The Assist API then lists a tool named
**`at__AtSchedule`** with the handler's `description` and a parameter schema from `slot_schema`, and
`api.async_call_tool(ToolInput(tool_name="at__AtSchedule", tool_args={...}))` runs the handler (`response_type ==
"action_done"`). The spike mocks the platform module with `pytest_homeassistant_custom_component.common.mock_platform(hass,
"at.llm", module)`; Task 15 adds a real `custom_components/at/llm.py`.

**APIs used:**

| Symbol                                                 | Module                         | Signature                                                                                                                                                               | Public?                                                                                      |
| ------------------------------------------------------ | ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `async_get_tools` (platform function `at` must define) | `custom_components/at/llm.py`  | `@callback def async_get_tools(hass, llm_context: LLMContext, api_id: str) -> LLMTools \| None` (protocol `LLMToolsPlatformProtocol` in `homeassistant.components.llm`) | Public platform contract. Return `None` when `api_id != llm.LLM_API_ASSIST`.                 |
| `LLMTools`                                             | `homeassistant.components.llm` | dataclass `LLMTools(tools: list[Tool], prompt: str \| None = None)`                                                                                                     | Public. `prompt` is merged into the API prompt.                                              |
| `IntentTool`                                           | `homeassistant.helpers.llm`    | `IntentTool(name: str, intent_handler: IntentHandler, *, title: str \| None = None, integration: str \| None = None, annotations: ToolAnnotations = ToolAnnotations())` | Public.                                                                                      |
| `ToolAnnotations`                                      | same                           | `read_only, destructive, idempotent, open_world` flags                                                                                                                  | Public. Core uses `ToolAnnotations(destructive=False, open_world=False)` for additive tools. |
| `llm.async_get_api`                                    | same                           | `async_get_api(hass, api_id: str \| list[str], llm_context: LLMContext) -> APIInstance`                                                                                 | Public. `APIInstance.tools`, `.async_call_tool(tool_input)`.                                 |
| `LLMContext`                                           | same                           | dataclass `platform, context, language, assistant, device_id`                                                                                                           | Public.                                                                                      |
| `intent.IntentHandler`                                 | `homeassistant.helpers.intent` | class attrs `intent_type`, `description`, `platforms`; property `slot_schema -> dict \| None` (probatio keys); `async_handle(intent_obj) -> IntentResponse`             | Public.                                                                                      |

**Gotchas:**

- **Tool names must be prefixed `<domain>__`** (`at__AtSchedule`, `at__AtList`, `at__AtCancel`).
  `homeassistant.components.llm._async_report_tool_issues` logs a deprecation for unprefixed names
  (`TOOL_PREFIX_BREAKS_IN_HA_VERSION = "2027.3"`). Our `fail_on_deprecation_report` fixture would catch it.
- **Set `integration="at"` on each tool**, or `report_untagged_tool` logs a deprecation as well.
- The platform is loaded lazily (`LazyIntegrationPlatforms`), only for integrations in
  `hass.config.top_level_components`, and only if `llm.py` exists in the integration directory. A platform that is
  missing the first time is cached as missing.
- The intent name inside HA stays `AtSchedule`; only the LLM-facing tool name has the prefix. The spec's intent names
  are unchanged.
- `slot_schema` keys become the tool's parameters; `preferred_area_id` / `preferred_floor_id` are hidden from the LLM
  and filled in from the device's area by `IntentTool`.
- Like Core's own platforms, filter by exposure if a tool only makes sense with exposed entities
  (`async_should_expose(hass, llm_context.assistant, entity_id)`).

## Item 5: sentence triggers with an LLM agent and prefer-local (PASS)

**What works:** a pipeline whose `conversation_engine` is a stub non-default `AbstractConversationAgent`, with
`prefer_local_intents=True` **and** with `False`: running "at 11 turn on the kitchen light" through the pipeline fires
the item 1 trigger (`command == "turn on the kitchen light"`), the stub agent is never called, no light service runs,
and `INTENT_END` reports `processed_locally is True` with the trigger's speech.

Why: `assist_pipeline/default_pipeline.py` calls `conversation.async_handle_sentence_triggers(...)` for **every**
non-default agent before anything else (unless the run is a follow-up the agent asked to continue,
`_intent_agent_only`). `prefer_local_intents` only gates the later `conversation.async_handle_intents(...)` step.
So no "LLM tools only" caveat is needed. The one exception: a continued conversation (the LLM asked a follow-up
question) skips triggers and goes straight to the LLM, which then needs the `at__` tools from item 4.

**APIs used (test-side only; `at` itself needs none of these):**

| Symbol                                                                                                                                                                                                                           | Module                                                     | Public?                                                 |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------- |
| `conversation.async_set_agent(hass, config_entry, agent)`                                                                                                                                                                        | `homeassistant.components.conversation`                    | Public. Agent id = `config_entry.entry_id`.             |
| `conversation.AbstractConversationAgent` (`supported_languages`, `async_process`)                                                                                                                                                | same                                                       | Public.                                                 |
| `async_get_pipelines(hass)`, `async_update_pipeline(hass, pipeline, *, conversation_engine=..., prefer_local_intents=...)`                                                                                                       | `homeassistant.components.assist_pipeline`                 | Public (`__all__`).                                     |
| `async_get_pipeline(hass, pipeline_id)`                                                                                                                                                                                          | `homeassistant.components.assist_pipeline.pipeline`        | Not exported from the package.                          |
| `PipelineInput(session=..., intent_input=..., device_id=..., run=PipelineRun(hass, context=..., pipeline=..., start_stage=PipelineStage.INTENT, end_stage=PipelineStage.INTENT, event_callback=...))`, `.execute(validate=True)` | `homeassistant.components.assist_pipeline.run` / `.models` | Internal; what Core's pipeline tests use for text runs. |
| `chat_session.async_get_chat_session(hass)`                                                                                                                                                                                      | `homeassistant.helpers.chat_session`                       | Public.                                                 |

## Item 6: panel_custom (PASS, registration only)

**What works:** after `async_setup_component(hass, "panel_custom", {})` (which sets up the real `frontend`),
`await panel_custom.async_register_panel(hass, frontend_url_path="at", webcomponent_name="at-panel",
sidebar_title="At", sidebar_icon="mdi:clock-outline", module_url="/at_static/at-panel.js", require_admin=False)` adds
`hass.data["frontend_panels"]["at"]` (`homeassistant.components.frontend.DATA_PANELS`), whose
`to_response()["config"]["_panel_custom"]["name"] == "at-panel"`.

**API:** `homeassistant.components.panel_custom.async_register_panel(hass, frontend_url_path, webcomponent_name,
sidebar_title=None, sidebar_icon=None, js_url=None, module_url=None, embed_iframe=False, trust_external=False,
config=None, require_admin=False, config_panel_domain=None, ...)`, public and documented. Remove it with
`homeassistant.components.frontend.async_remove_panel(hass, "at")` on unload.

**Gotchas:**

- `at`'s manifest should list `panel_custom` in `dependencies` (it already does, which is why `tests/conftest.py`
  fakes it as loaded), so `frontend` and its `DATA_PANELS` are set up before `at` registers the panel. The spike did
  not test registering without `frontend`.
- Serving the JS bundle (`hass.http.async_register_static_paths([StaticPathConfig(...)])`) is not part of this spike.
- **Manual check, Task 21:** whether a custom panel can reliably load HA's own `ha-selector` target and action pickers
  in the browser can't be tested in pytest. If it can't, ship the simpler built-in pickers (spec §10 item 6).
  - **Status (Task 21):** the manual check is still pending (headless environment). The Add job dialog ships the
    plain `<select>` pickers built from `hass.states` and does not use `ha-selector`, so it works either way.

## Summary for the adapters (`ha_internal/`)

| Need                          | Use                                                                                                                            | Risk                                                                                                 |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| Register voice sentences      | `get_agent_manager(hass).register_trigger(...)` + inject data-level `lists` via `subscribe_intents`                            | Medium: undocumented dict shape and lazy rebuild. Fallback: literal alternatives + own hassil parse. |
| Recognize only                | `get_agent_manager(hass).default_agent.async_recognize_intent(input)` (non-strict, once)                                       | Medium: undocumented method; mind the cache order.                                                   |
| Check targets without running | `intent.async_match_targets(hass, MatchTargetsConstraints(..., assistant="conversation"))`                                     | Low: public helper.                                                                                  |
| Run later                     | `intent.async_handle(hass, "conversation", type, slots, text, context, language, assistant="conversation", device_id=...)`     | Low: public.                                                                                         |
| LLM tools                     | `custom_components/at/llm.py` → `async_get_tools` → `LLMTools([IntentTool("at__AtSchedule", handler, integration="at"), ...])` | Low: public platform; the name prefix is required.                                                   |
| Sidebar panel                 | `panel_custom.async_register_panel(...)`                                                                                       | Low: public.                                                                                         |
