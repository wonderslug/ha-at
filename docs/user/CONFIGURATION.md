# Configuration and reference

Everything `at` offers, from options to events. For installation, see [getting started](GETTING_STARTED.md).

## Options

Go to **Settings** > **Devices & services** > **at: Scheduled Jobs** > **Configure**. Saving applies the changes right away, without restarting the integration or interrupting a running job.

| Option                                     | Default | What it does                                                                                             |
| ------------------------------------------ | ------- | -------------------------------------------------------------------------------------------------------- |
| **Grace window**                           | 5       | Minutes a job may run late after a restart or reload. Jobs later than this are marked missed. 0 to 1440. |
| **History age**                            | 7       | Days finished jobs stay in the history. 1 to 365.                                                        |
| **History size**                           | 100     | Most finished jobs kept. 1 to 10000. Whichever of age and size is hit first removes the job.             |
| **Panel for admins only**                  | off     | Shows the sidebar panel only to administrators.                                                          |
| **Leave relative times to Home Assistant** | off     | Stops `at` from answering phrases like "in 5 minutes", so Home Assistant's own delayed commands do it.   |

With the last option on, "turn off the lights in 5 minutes" is handled by Home Assistant with its own timer. That job does not appear in `at`, and it does not survive a restart. Absolute times such as "at 6 pm" still go to `at`.

## Voice and text phrases

The sentences work in Assist, on voice satellites, and in the Assist text box. A phrase is a command plus a time, in either order:

```text
turn on the porch light at 11 pm
at 11 pm turn on the porch light
```

### Times

| Form           | Examples                                                                                  |
| -------------- | ----------------------------------------------------------------------------------------- |
| Clock time     | `at 6`, `at 6:30`, `at 6 pm`, `at 18:30`, `at 6 o'clock`, `at noon`, `at midnight`        |
| Clock in words | `at seven`, `at seven thirty`, `at six forty-five pm`, `at seven oh five`                 |
| 24-hour        | `at 18:30`, `at 1800 hours`, `at eighteen hundred`, `at oh six hundred hours`             |
| Spoken-to-text | `at 11 p.m.`, `at 7 a.m.`                                                                 |
| Day            | `today`, `tonight`, `tomorrow`, `this morning`, `this afternoon`, `this evening`          |
| Weekday        | `on Friday`, `on Friday evening`, `on Fri`                                                |
| Day and time   | `tomorrow at 7 am`, `at 7 am tomorrow`, `on Friday at 6:30 pm`                            |
| Relative       | `in 20 minutes`, `in an hour`, `in two hours`, `in 2 and a half hours`, `in half an hour` |
| Relative words | `in forty five minutes`, `in one hundred and twenty minutes`, `in twenty-five hours`      |

Numbers can be digits or words, up to "nine hundred and ninety-nine". Voice sentences accept durations up to 180.

An hour after 12 needs its minutes or a 24-hour wording: `at 18` and `at twenty` are not times, so "set the brightness at 20" is never read as 8 PM. Say `at 18:00`, `at 1800 hours` or `at eighteen hundred` instead. A four-digit time needs "hours" after it.

### Listing and canceling

| Say                                                   | Result                                                                 |
| ----------------------------------------------------- | ---------------------------------------------------------------------- |
| `what's scheduled`                                    | Lists pending jobs                                                     |
| `what's scheduled for today` / `tonight` / `tomorrow` | Narrows the list by day                                                |
| `what's scheduled for the porch light`                | Narrows the list by target                                             |
| `cancel everything` / `cancel all jobs`               | Cancels all pending jobs except ones created by actions or automations |
| `cancel the 6 pm job` / `cancel the job at 6:30`      | Cancels the job at that time                                           |
| `cancel the porch light job`                          | Cancels jobs for that target                                           |

When two jobs match, `at` names their times and asks you to say "cancel the 6 pm job".

### What can be scheduled

`at` stores the command only if Home Assistant's built-in agent can understand it right now and the target is exposed to Assist. Timers, questions, and chit-chat are refused, and so are targets that are not exposed or do not exist. Exposure is checked again when the job runs.

Sentences `at` cannot use, such as "remind me at 5", are handed back to the conversation agent you were talking to, so normal conversation is not broken. A handed-back exchange to another agent starts a new conversation there.

## LLM agents

`at` offers three tools to Home Assistant LLM APIs, including Assist:

| Tool             | Purpose                                                                                       |
| ---------------- | --------------------------------------------------------------------------------------------- |
| `at__AtSchedule` | Schedules a command. Arguments: `time` and `command`.                                         |
| `at__AtList`     | Lists scheduled commands. Optional `scope` (`all`, `today`, `tonight`, `tomorrow`) or `name`. |
| `at__AtCancel`   | Cancels commands. `all`, or narrow by `time` or `name`.                                       |

The model passes the user's time phrase verbatim, such as "at 6am" or "in 20 minutes", and `at` parses it. The model never runs the command itself. Jobs scheduled this way show **LLM** as their source. This works with the **Prefer handling commands locally** setting of a conversation agent.

## The panel

The **Scheduled Jobs** sidebar panel has two tabs:

- **Upcoming**: pending and running jobs, with **Run now** and **Cancel** buttons and a details view.
- **History**: finished jobs, filterable by status. The three-dot menu has **Clear history**.

Select **+ Add job** to open the **Add job** dialog:

- **Type it**: a sentence such as "turn on the porch light at 11pm", with a preview of the result.
- **Pick it**: choose any action, its targets and its options, using the same form Home Assistant uses to perform an action, and a time. For the time, use the date and time field or the **+15m** and **+1h** chips. Any signed-in user can schedule one action with fixed values this way; templates need an administrator.
- **Sequence**: several steps, built with the automation editor's step list or its YAML view. This tab is shown to administrators only. If Home Assistant's editor elements cannot be loaded, **Pick it** falls back to a verb, target and variables form, and **Sequence** to a JSON list of actions.

An action scheduled by an administrator, an action scheduled by an automation or script, and any job with several steps or templates can only be run now, rescheduled or completed by an administrator. Jobs scheduled by voice or typed as a sentence are not affected. A job fails if the person who scheduled it has been removed, with the message "The user who scheduled this job no longer exists".

## Entities

| Entity                   | State                                                        | Attributes                          |
| ------------------------ | ------------------------------------------------------------ | ----------------------------------- |
| `todo.at_scheduled`      | Pending jobs as open items, finished jobs as completed items | None                                |
| `sensor.at_next_job`     | Due time of the next pending job (timestamp)                 | `job_id`, `summary`                 |
| `sensor.at_pending_jobs` | Number of pending jobs                                       | `jobs`: id, due and summary of each |

In `todo.at_scheduled`:

- Add an item to schedule it. Write the time in the text ("turn on the porch light at 6 pm") or set the due date.
- Change an item's due date to move a pending job.
- Mark an item completed to run it now.
- Delete an item to cancel a pending job or remove a finished one.

Running jobs do not appear in the list.

## Actions

### `at.schedule`

Schedules a command or an action. Give exactly one of `command` or `action`, and exactly one of `at`, `delay` or `when`. Returns `job_id`, `due` and `summary`. Any user can schedule a single action; several steps or templates need an administrator (or no user, as in an automation).

```yaml
action: at.schedule
data:
  command: turn on the porch light
  when: tomorrow at 7 am
  name: Morning porch light
response_variable: job
```

```yaml
action: at.schedule
data:
  action:
    - action: light.turn_off
      target:
        entity_id: light.porch
  delay: "00:30:00"
```

```yaml
action: at.schedule
data:
  command: turn off the kitchen light
  at: "2026-11-19 07:00:00"
```

### `at.list`

Returns `pending` and `history` job lists. Filter with `status`, `start` and `end`.

```yaml
action: at.list
data:
  status: [pending, failed]
response_variable: jobs
```

### `at.cancel`

Cancels pending jobs by `job_id` (one or several) or all of them with `all: true`. Returns the cancelled ids. Unlike the voice command, `all: true` also cancels jobs created by actions.

```yaml
action: at.cancel
data:
  job_id: 3fa9c1d2
```

### `at.run_now`

Runs a pending job immediately. An action scheduled by an administrator or by an automation or script, and any job with several steps or templates, needs an administrator.

```yaml
action: at.run_now
data:
  job_id: 3fa9c1d2
```

### `at.clear_history`

Deletes every finished job.

```yaml
action: at.clear_history
```

## Events

`at` fires these events. Use them as automation triggers.

| Event              | When                                                                                         |
| ------------------ | -------------------------------------------------------------------------------------------- |
| `at_job_scheduled` | A job is added or moved                                                                      |
| `at_job_executed`  | A job ran successfully                                                                       |
| `at_job_failed`    | A job failed                                                                                 |
| `at_job_cancelled` | A job was cancelled                                                                          |
| `at_job_missed`    | A job came due while Home Assistant was down or `at` was reloading, outside the grace window |

Every event carries `job_id`, `summary`, `due` (ISO time), `status` and `via` (`voice`, `llm`, `panel`, `reschedule`, `todo` or `service`). `at_job_failed` also carries `error`.

The events also show in the logbook.

## Data updates

`at` does not poll. It keeps its jobs in Home Assistant's storage and sets a timer for each pending job. A one-minute sweep runs any pending job that is overdue. When Home Assistant starts or `at` is reloaded, a job that came due in the meantime runs if it is within the **Grace window**, and is marked missed otherwise. A job that was running when Home Assistant stopped or `at` was reloaded is marked failed.

## Known limitations

- Voice and time phrases are English only. Each voice assistant uses the sentences of its own language, whatever your Home Assistant language is, so an English assistant works on a German system. In an assistant of another language, `at` leaves the sentence to Assist. Use the panel or the `at.schedule` action with its `at` or `delay` field instead. The LLM tools take a spoken time phrase, so they also need English.
- A job that runs `script.turn_on` or `automation.trigger` counts as done once the script or automation starts, not when it finishes. A failure inside the script or automation does not mark the job failed.
- Commands must be ones the built-in agent understands. Anything else is refused.
- Canceling a job by its time by voice needs digits, such as "cancel the 7:30 job". Scheduling accepts words such as "at seven thirty".
- Exchanges forwarded to another conversation agent start a new conversation.
- Running jobs do not appear in the to-do list.

## Troubleshooting

- **A phrase is ignored or answered by another agent.** Check the wording against the tables above, and that the target is exposed to Assist.
- **"Sorry, scheduling is only available in English for now."** The voice assistant you used is not set to English.
- **A job shows as missed.** Home Assistant was down, or `at` was reloading, for longer than the **Grace window**.
- **Diagnostics.** On the integration page, select the three-dot menu > **Download diagnostics**. The file lists the options, job counts by status, whether your language is supported, and whether each Home Assistant hook `at` relies on was found. It holds no job text and no user IDs. Attach it to bug reports.

## Removing the integration

See [getting started](GETTING_STARTED.md#removing-the-integration).
