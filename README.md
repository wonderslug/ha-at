# Scheduled Jobs

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

## What it does

`at` runs a Home Assistant command once, later. Say "turn on the porch light at 11 pm", and `at` stores the command and runs it at that time. It works from voice, Assist text, LLM agents, a sidebar panel, a to-do list, and service actions.

- **Voice and text:** sentence triggers on Home Assistant's built-in conversation agent. Both word orders work: "at 6 am turn on the lights" and "turn on the lights at 6 am".
- **LLM agents:** the `at__AtSchedule`, `at__AtList` and `at__AtCancel` tools.
- **Panel:** the **at** sidebar panel with **Upcoming** and **History** tabs and an **Add job** dialog.
- **Entities:** `todo.at_scheduled`, `sensor.at_next_job` and `sensor.at_pending_jobs`.
- **Actions:** `at.schedule`, `at.list`, `at.cancel`, `at.run_now` and `at.clear_history`.
- **Events:** `at_job_scheduled`, `at_job_executed`, `at_job_failed`, `at_job_cancelled` and `at_job_missed`.

Jobs survive restarts. A job that comes due while Home Assistant is down still runs if it is within the grace window, and otherwise is marked missed.

> [!NOTE]
> Voice and text scheduling is English only. Only commands that Home Assistant's built-in agent understands can be scheduled. See [known limitations](docs/user/CONFIGURATION.md#known-limitations).

## Installation

Open the integration in the Marketplace (Home Assistant 2026.11 and newer) or in HACS:

[![Open your Home Assistant instance and open this repository in the Marketplace.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=wonderslug&repository=ha-at&category=integration)

Then add the integration:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=at)

The setup asks for nothing. Only one instance can be added.

## Documentation

- [Getting started](docs/user/GETTING_STARTED.md): install, set up, first job, and removal
- [Configuration and reference](docs/user/CONFIGURATION.md): voice phrases, LLM agents, the panel, entities, actions, events, options, and known limitations
- [Examples](docs/user/EXAMPLES.md): automations that use `at`

## Contributing

See [`docs/development/`](docs/development/) for the architecture and local setup.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Made with ❤️ by [@wonderslug][user_profile]**

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/wonderslug/ha-at.svg?style=for-the-badge
[commits]: https://github.com/wonderslug/ha-at/commits/main
[hacs]: https://www.hacs.xyz/docs/marketplace/
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/wonderslug/ha-at.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40wonderslug-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/wonderslug/ha-at.svg?style=for-the-badge
[releases]: https://github.com/wonderslug/ha-at/releases
[user_profile]: https://github.com/wonderslug
