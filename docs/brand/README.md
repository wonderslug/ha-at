# Brand guide

The name, mark, colors and type for at: Scheduled Jobs, and the files that carry them. Use this page when you make
anything that represents the project: a release graphic, a dashboard card, a forum post, a new panel screen.

## Name

| Name                   | Where it's used                                                                                                                          |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **at: Scheduled Jobs** | The integration's name: `manifest.json`, `hacs.json`, the README title, the docs, the logo and the social preview                        |
| **Scheduled Jobs**     | What it shows inside Home Assistant: the sidebar panel, the config entry, its device and logbook entries (`PANEL_TITLE`, `DISPLAY_NAME`) |
| `at`                   | The domain, and the prefix of actions and events (`at.schedule`, `at_job_executed`). Always in code formatting                           |

- Write "at" in lowercase, also at the start of the name. It refers to the Unix `at` command.
- Keep the colon and the space: "at: Scheduled Jobs", never "At Scheduled Jobs" or "at:Scheduled Jobs".
- Inside Home Assistant, don't promote "at". The panel and the entry say "Scheduled Jobs" because that's what users
  are looking for there.

**Tagline:** Run any Home Assistant action later, once.

## The mark: Clock @

An @ whose inner bowl is a clock face. It reads as "at a time" and still reads as an @ at 16 px.

| Light                                  | Dark                                        |
| -------------------------------------- | ------------------------------------------- |
| <img src="icon.svg" alt="" width="96"> | <img src="icon-dark.svg" alt="" width="96"> |

### Construction

Drawn in a 100 × 100 box. The visible artwork spans 16 to 84 on both axes, which is the crop every icon file uses.

| Part          | Geometry                                                                   | Stroke         |
| ------------- | -------------------------------------------------------------------------- | -------------- |
| Bowl          | Circle, center (50, 50), radius 14                                         | 8, ring color  |
| Stem and ring | `M64 38 V56 a8 8 0 0 0 16 0 V50 a30 30 0 1 0 -15 26`                       | 8, ring color  |
| Clock hands   | `M50 50 V43 M50 50 l5 3`: hour hand up, minute hand toward about 4 o'clock | 4, hands color |

All strokes have round caps and round joins. No fills, no background.

### Usage

- ✅ Use it on a transparent or plain background in one of the two color sets below.
- ✅ Leave clear space around it of at least a quarter of its width.
- ✅ Use the dark set on any background darker than `#808080`.
- ❌ Don't recolor it, add a gradient, outline or shadow, or put it on a tile. The social preview is the one place it
  sits on a colored panel.
- ❌ Don't rotate it or move the clock hands. They are part of the shape, not a live clock.
- ❌ Don't place it next to the Home Assistant logo or in Home Assistant's light blue (`#18BCF2`). The integration is
  not an official one, and the brand must not suggest it is.
- ⚠️ Below 24 px the hands blur into the bowl. That's acceptable; the @ still carries the mark.

## Colors

| Role              | Light theme | Dark theme | Notes                                           |
| ----------------- | ----------- | ---------- | ----------------------------------------------- |
| Ring (primary)    | `#364FC7`   | `#BAC8FF`  | The mark, and the "at:" in the wordmark         |
| Hands (accent)    | `#F59F00`   | `#FFD43B`  | Clock hands only                                |
| Text              | `#1A1D23`   | `#F1F3F5`  | "Scheduled Jobs" in the wordmark, and body text |
| Background        | `#F4F5F7`   | `#14171C`  | Neutral surfaces behind the mark                |
| Feature panel     | —           | `#1B2559`  | Social preview and other large brand panels     |
| Panel subtle text | —           | `#C5CEF5`  | Taglines on the feature panel                   |

**Contrast** (WCAG):

| Pair                                 | Ratio   |                                                    |
| ------------------------------------ | ------- | -------------------------------------------------- |
| Ring `#364FC7` on white              | 6.77:1  | ✅ Fine for text                                   |
| Text `#1A1D23` on white              | 16.88:1 | ✅                                                 |
| Ring `#BAC8FF` on `#14171C`          | 10.94:1 | ✅                                                 |
| Hands `#FFD43B` on `#14171C`         | 12.6:1  | ✅                                                 |
| White on feature panel `#1B2559`     | 14.43:1 | ✅                                                 |
| `#C5CEF5` on feature panel `#1B2559` | 9.29:1  | ✅                                                 |
| Hands `#F59F00` on white             | 2.13:1  | ⚠️ Decoration only. Never use it for text on light |
| Ring `#364FC7` on `#14171C`          | 2.65:1  | ❌ Use the dark set on dark backgrounds            |

## Typography

All three are free under the SIL Open Font License, from [Google Fonts](https://fonts.google.com/).

| Typeface                                                           | Weight      | Use                                         |
| ------------------------------------------------------------------ | ----------- | ------------------------------------------- |
| [Space Grotesk](https://fonts.google.com/specimen/Space+Grotesk)   | Bold 700    | The wordmark and headings in brand graphics |
| [Inter](https://fonts.google.com/specimen/Inter)                   | Regular 400 | Taglines and body text                      |
| [JetBrains Mono](https://fonts.google.com/specimen/JetBrains+Mono) | Medium 500  | URLs, code, the repository name             |

Inside Home Assistant, the panel uses Home Assistant's own font and styling, not these.

## Wordmark and logo

The mark followed by "at: Scheduled Jobs" in Space Grotesk Bold. "at:" is in the ring color, "Scheduled Jobs" in the
text color.

| Light                                   | Dark                                         |
| --------------------------------------- | -------------------------------------------- |
| <img src="logo.svg" alt="" height="48"> | <img src="logo-dark.svg" alt="" height="48"> |

Proportions, for a mark of height H:

- Font size: H / 2
- Gap between mark and text: 0.234 × H
- Text baseline: 0.676 × H from the top, which centers the lowercase letters on the mark

The text in the SVG files is converted to outlines, so they render the same without the font installed. Edit the
wordmark from the font, not by editing those paths.

## Social preview

`social-preview.png`, 1280 × 640, for GitHub's repository card.

- Background `#1B2559`
- Mark (dark set) 300 px, left edge at 120, top at 150
- "at: Scheduled Jobs" in Space Grotesk Bold 76 px at x 480; "at:" in `#BAC8FF`, the rest white
- Tagline in Inter Regular 32 px, `#C5CEF5`
- `github.com/wonderslug/ha-at` in JetBrains Mono Medium 28 px, `#BAC8FF`, bottom left

GitHub doesn't read this from the repository. Upload it under **Settings** > **General** > **Social preview**
whenever it changes.

## Files

| File                                              | Size                  | Purpose                                                 |
| ------------------------------------------------- | --------------------- | ------------------------------------------------------- |
| `custom_components/at/brand/icon.png`             | 256 × 256             | Integration icon in Home Assistant and the Marketplace  |
| `custom_components/at/brand/icon@2x.png`          | 512 × 512             | High-density icon                                       |
| `custom_components/at/brand/dark_icon.png`, `@2x` | 256, 512              | Icon for dark themes                                    |
| `custom_components/at/brand/logo.png`, `@2x`      | 656 × 128, 1313 × 256 | Logo with wordmark                                      |
| `custom_components/at/brand/dark_logo.png`, `@2x` | same                  | Logo for dark themes                                    |
| `docs/brand/icon.svg`, `icon-dark.svg`            | vector                | Source of the icon                                      |
| `docs/brand/logo.svg`, `logo-dark.svg`            | vector                | Source of the logo; the README header uses these        |
| `docs/brand/social-preview.svg`, `.png`           | 1280 × 640            | GitHub social preview                                   |
| `docs/brand/ways-to-schedule.svg`, `-dark.svg`    | 1200 × 650            | README infographic: the ways in, the queue, the results |
| `docs/brand/archive/`                             | vector                | The 14 options that weren't chosen, light and dark      |

Home Assistant's requirements for the `brand/` folder: PNG, square icon, transparent background, cropped to the
artwork. See [brand images for custom integrations](https://contributors.home-assistant.io/core/integrations/brands/#brand-images-for-custom-integrations).
The brands site takes the images from the latest release, so a change only appears there after the next release.

To change an asset, edit the SVG source, then export the PNGs at the sizes above with a transparent background.

## Archived options

Kept in `archive/` as `<number>-<name>.svg` and `<number>-<name>-dark.svg` in case the brand changes direction.

| #   | Option         | Idea                                                        |
| --- | -------------- | ----------------------------------------------------------- |
| 02  | @t ligature    | A two-storey "a" joined to a "t" by a shared crossbar       |
| 03  | Countdown @    | The ring stops short like a timer; a dot marks the next job |
| 04  | Calendar @     | A calendar page with the @ as the date                      |
| 05  | Play-later @   | The bowl is a play button: run this, later                  |
| 06  | at> prompt     | A shell prompt, an @ and a cursor, on a dark tile           |
| 07  | Orbit @        | A solid @ with a dot circling it                            |
| 08  | Queue ticket   | A take-a-number ticket stamped with @                       |
| 09  | Timeline pin   | A map pin dropped on a timeline                             |
| 10  | Segmented dial | An @ inside a dial cut into quarters, one lit               |
| 11  | Hourglass @    | An hourglass in the bowl                                    |
| 12  | Bell @         | A reminder bell with the @ cut out                          |
| 13  | Forward @      | The ring ends in an arrowhead                               |
| 14  | Night @        | A crescent moon in the bowl, with a star                    |
| 15  | Job list @     | A list whose first bullet is an @                           |
