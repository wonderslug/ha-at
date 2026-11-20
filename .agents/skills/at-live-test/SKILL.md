---
name: at-live-test
description: >-
  Check a change to the at integration on the running development Home Assistant instance — typed and spoken
  scheduling phrases, voice sentence triggers, the LLM tools, and the at.* service actions — without leaving jobs
  behind. Use when asked to "try it on the dev instance", "test it live", "does this sentence work", "check it in
  Home Assistant", "reproduce this on the local instance", or after changing the time parser, the language pack,
  the voice sentences or the scheduling path. Use alongside ha-coordinator-debug, which owns the run loop.
  SYMPTOMS — load this if you are about to: schedule a test job and leave it pending; call at.cancel with all or
  at.clear_history on the shared instance; pass a list field such as status as key=value to script/ha call; test
  freshly edited Python without checking that Home Assistant restarted since; or report a live check as automated
  test coverage.
---

# Live testing `at` on the development instance

The instance is shared with the developer. Its run loop, restarts and log reading are in
[`ha-coordinator-debug`](../ha-coordinator-debug/SKILL.md); `script/ha` itself is in
[`ha-cli.md`](../blueprint-tooling/references/ha-cli.md). This skill covers only what is specific to `at`.

## Before testing

1. `script/ha status` and `script/ha entries` — running, and the `at` entry `loaded`.
2. **Is your code loaded?** Python, `manifest.json`, `services.yaml` and translations need a restart. Compare
   `started` with the time of your last edit; if it is older, announce the restart before running `./script/develop`.
3. `config/configuration.yaml` loads the `demo` integration, so lights such as Bed Light and Ceiling Lights exist to
   schedule against. A job that fires really switches them — on the developer's dashboard.

## Pick the path that matches the change

`live.py` below is [`scripts/live.py`](scripts/live.py), run from the repository root as
`mise exec -- python .agents/skills/at-live-test/scripts/live.py`.

| Change touches                                       | Check with                                                     | Leaves a job?           |
| ---------------------------------------------------- | -------------------------------------------------------------- | ----------------------- |
| Time parser, language pack phrases, command matching | `live.py preview "<command with time>"` — the panel's preview  | never                   |
| Voice sentence templates and trigger handling        | `live.py say "<sentence>"` — `conversation.process` via Assist | cancelled automatically |
| The `at.schedule` action and its fields              | `script/ha call at.schedule --data '{...}' --response`         | yes — cancel it         |
| The LLM tools                                        | the `home-assistant-dev` MCP server's `AtSchedule` tool        | yes — cancel it         |
| Listing and cancelling                               | `live.py jobs`, `script/ha call at.cancel job_id=<id>`         | —                       |

`preview` exercises the parser and the command check exactly as the panel does, but **not** the sentence templates:
a phrase can preview fine and still not match by voice. Changes to `lang/<code>.py` sentence lists need `say`.

`say` exits with the speech, the response type and every job it created, then cancels those jobs. `--keep` leaves
them pending — for a test that waits for one to fire. `jobs` lists what is still pending.

## Rules on the shared instance

- **Cancel what you created, by `job_id`, and nothing else.** Never `at.cancel` with `all`, never
  `at.clear_history`, never `at.run_now` on a job you did not create — the queue and history are the developer's.
- **Finish with `live.py jobs`** and confirm none of your jobs remain.
- **List fields go through `--data`.** `script/ha call at.list status=pending` is a 400; use
  `--data '{"status": ["pending"]}'`.
- **Pass `language=en`** (or the pack under test) to `conversation.process`; without it the system language decides
  which sentences apply.

## What this cannot show

- Speech-to-text: `conversation.process` starts from text, so how an engine writes "forty five" is not tested.
- Satellite and device context: it carries no device, so device-based source labels need the automated tests.
- Durable coverage. A live check is evidence for this change only — report it as such, never as a test, and add the
  automated test the change needs ([`ha-testing`](../ha-testing/SKILL.md)).
