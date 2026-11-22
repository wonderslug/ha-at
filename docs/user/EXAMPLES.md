# Examples

Replace entity IDs with your own.

## Notify when a job fails

```yaml
automation:
  - alias: Tell me when a scheduled job fails
    triggers:
      - trigger: event
        event_type: at_job_failed
    actions:
      - action: notify.notify
        data:
          message: "{{ trigger.event.data.summary }} failed: {{ trigger.event.data.error }}"
```

## Notify when a job is missed

```yaml
automation:
  - alias: Tell me when a job was missed
    triggers:
      - trigger: event
        event_type: at_job_missed
    actions:
      - action: notify.notify
        data:
          message: "Missed: {{ trigger.event.data.summary }}"
```

## Turn off the lights 30 minutes after a door opens

```yaml
automation:
  - alias: Porch light off later
    triggers:
      - trigger: state
        entity_id: binary_sensor.front_door
        to: "on"
    actions:
      - action: at.schedule
        data:
          action:
            - action: light.turn_off
              target:
                entity_id: light.porch
          delay: "00:30:00"
          name: Porch light off
```

## Remind the kitchen about the laundry

Announces in the kitchen an hour after the washer finishes. The time is given by `delay`, so the message can say anything.

```yaml
automation:
  - alias: Laundry reminder
    triggers:
      - trigger: state
        entity_id: binary_sensor.washer_running
        to: "off"
    actions:
      - action: at.schedule
        data:
          command: announce in the kitchen that the laundry is still in the washer
          delay: "01:00:00"
          name: Laundry reminder
```

## Confirm a scheduled job on your phone

`at.schedule` returns the job's `due` time and `summary`, so a script can tell you what it set up.

```yaml
script:
  porch_light_tonight:
    alias: Porch light at sunset tonight
    sequence:
      - action: at.schedule
        data:
          command: turn on the porch light
          at: "{{ states('sensor.sun_next_setting') }}"
        response_variable: job
      - action: notify.notify
        data:
          message: "{{ job.summary }} at {{ as_timestamp(job.due) | timestamp_custom('%-I:%M %p') }}"
```

## Cancel everything when you leave

`at.cancel` with `all: true` cancels every pending job, including ones created by automations.

```yaml
automation:
  - alias: Clear scheduled jobs when away
    triggers:
      - trigger: state
        entity_id: group.family
        to: not_home
    actions:
      - action: at.cancel
        data:
          all: true
```

## Show the next job on a dashboard

```yaml
type: entities
entities:
  - entity: sensor.at_next_job
  - entity: sensor.at_pending_jobs
  - entity: todo.at_scheduled
```
