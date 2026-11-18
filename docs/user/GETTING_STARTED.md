# Getting started with at

`at` runs a Home Assistant command once, at a later time you choose. This page covers installing it, setting it up, scheduling a first job, and removing it.

## Prerequisites

- Home Assistant 2026.10.0 or newer.
- The built-in Assist conversation agent, for voice and text scheduling. The `conversation`, `intent`, `http`, `frontend` and `panel_custom` integrations are required, and Home Assistant loads them for you.
- Entities you want to schedule voice commands for must be exposed to Assist.

## Installation

### Marketplace (Home Assistant 2026.11 and newer)

1. Go to **Settings** > **Marketplace**.
2. Add `https://github.com/PLACEHOLDER_OWNER/ha-at` as a custom repository with the category **Integration**.
3. Open **at (placeholder)** and select **Download**.

### HACS (before Home Assistant 2026.11)

1. Open HACS, then select the three-dot menu > **Custom repositories**.
2. Add `https://github.com/PLACEHOLDER_OWNER/ha-at` with the category **Integration**.
3. Find **at (placeholder)**, select **Download**, and restart Home Assistant.

### Manual installation

1. Download the latest release from the [releases page](https://github.com/PLACEHOLDER_OWNER/ha-at/releases).
2. Copy the `at` folder to `custom_components/at/` in your Home Assistant configuration directory.
3. Restart Home Assistant.

## Setup

1. Go to **Settings** > **Devices & services**.
2. Select **Add integration** and search for **at (placeholder)**.
3. Select **Submit**.

There is nothing to enter. The display name is a placeholder for now, so the integration and its sidebar panel show as "at (placeholder)".

## Your first job

Say or type to Assist:

```text
turn on the porch light at 11 pm
```

Assist answers with the time it will run. To check it, say "what's scheduled", or open the **at (placeholder)** panel in the sidebar and look at the **Upcoming** tab.

The [configuration page](CONFIGURATION.md) lists every phrase, the panel, the entities, and the actions.

## Removing the integration

1. Go to **Settings** > **Devices & services** and select **at (placeholder)**.
2. Open the three-dot menu and select **Delete**.

This removes the sidebar panel, the entities, the voice sentences and the intents. The job queue and history are deleted too. If you installed through the Marketplace or HACS, you can also remove the download there, which asks for a restart. Delete any automations that use `at.*` actions or `at_job_*` events yourself.
