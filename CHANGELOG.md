# Changelog

## [0.1.1](https://github.com/wonderslug/ha-at/compare/v0.1.0...v0.1.1) (2026-11-21)


### Features

* add at one-shot scheduler integration ([c47b8ce](https://github.com/wonderslug/ha-at/commit/c47b8ce4dc399a810de6d4ec434d39e44f7d9d0a))
* answer voice sentences in each assistant's own language ([#19](https://github.com/wonderslug/ha-at/issues/19)) ([4ad732b](https://github.com/wonderslug/ha-at/commit/4ad732b04c27d37ee47f0a02e4d038f3da1a8b99))
* name the integration "at: Scheduled Jobs" and add the Clock @ logo ([#18](https://github.com/wonderslug/ha-at/issues/18)) ([bde8b1b](https://github.com/wonderslug/ha-at/commit/bde8b1b1d5e695bb348c4544e1a6a1d70770a352))
* **panel:** build the panel from Home Assistant's own list-page elements ([#14](https://github.com/wonderslug/ha-at/issues/14)) ([08687e6](https://github.com/wonderslug/ha-at/commit/08687e61dbc1d6267722d4cf1444dcaf3bc9f0cb))
* **panel:** pick any action with Home Assistant's own pickers ([#43](https://github.com/wonderslug/ha-at/issues/43)) ([195a5bd](https://github.com/wonderslug/ha-at/commit/195a5bda4e1382730107a6eb52c50740e3de759c))
* **panel:** plain-text source labels that name Assist, the satellite and the automation ([#17](https://github.com/wonderslug/ha-at/issues/17)) ([de86fc3](https://github.com/wonderslug/ha-at/commit/de86fc3b5e33f745e314e2d3b0586308ed9453df))
* **panel:** rename to "Scheduled Jobs" and match Home Assistant styling ([#13](https://github.com/wonderslug/ha-at/issues/13)) ([c30a58f](https://github.com/wonderslug/ha-at/commit/c30a58f24e927faa870d62ce64cb4f574ba35596))
* record who cancelled a job and show it in the panel's history ([#16](https://github.com/wonderslug/ha-at/issues/16)) ([cdaa9e9](https://github.com/wonderslug/ha-at/commit/cdaa9e9a1c1a4453b4827466b71144079bd5022c))
* understand compound number words and clock times in words ([#23](https://github.com/wonderslug/ha-at/issues/23)) ([b972e58](https://github.com/wonderslug/ha-at/commit/b972e58c4fa612e2fbfde7e53fcca8dca0a8a903))
* **voice:** run automations by voice, now or scheduled ([#12](https://github.com/wonderslug/ha-at/issues/12)) ([0da4a38](https://github.com/wonderslug/ha-at/commit/0da4a38fd602c616480001b9c035e1262a86403f))


### Bug Fixes

* **config-flow:** apply saved options without reloading the entry ([#5](https://github.com/wonderslug/ha-at/issues/5)) ([4b88086](https://github.com/wonderslug/ha-at/commit/4b88086d97b30d489109e72757f328150a94c471))
* **coordinator:** keep stopping when a stop callback raises ([#7](https://github.com/wonderslug/ha-at/issues/7)) ([786d23a](https://github.com/wonderslug/ha-at/commit/786d23a662ad26cbba95e5308d6bbacd6d576eab))
* keep finished jobs and in-flight saves consistent in the job manager ([#26](https://github.com/wonderslug/ha-at/issues/26)) ([2fc9d5f](https://github.com/wonderslug/ha-at/commit/2fc9d5fde01bd462f9ed43b3f95b84f1ed26aa52))
* keep leading acronyms and name past days in spoken replies ([#29](https://github.com/wonderslug/ha-at/issues/29)) ([7b3dc83](https://github.com/wonderslug/ha-at/commit/7b3dc831a1689ec32c39db41f547877515b03f11))
* keep loading jobs when one stored record is unreadable ([#25](https://github.com/wonderslug/ha-at/issues/25)) ([4f43a49](https://github.com/wonderslug/ha-at/commit/4f43a49535bb7b933cf0729ef3e65bb6acd6e7a2))
* name area, floor, device and label targets in action summaries ([#27](https://github.com/wonderslug/ha-at/issues/27)) ([91447cd](https://github.com/wonderslug/ha-at/commit/91447cd7fe658bf3d95fbba38e633d010d70833f))
* **panel:** keep the add job dialog open while adding and trap its focus ([#37](https://github.com/wonderslug/ha-at/issues/37)) ([515eda4](https://github.com/wonderslug/ha-at/commit/515eda41b9990fc417b828afcbbec1b51808dfb8))
* **service-actions:** check admin before pending status in run now ([#32](https://github.com/wonderslug/ha-at/issues/32)) ([963531b](https://github.com/wonderslug/ha-at/commit/963531b2c912482cac63edeefca4cc2d2fa6c4c1))
* show logbook entries in the current Home Assistant language ([#28](https://github.com/wonderslug/ha-at/issues/28)) ([2eed3e5](https://github.com/wonderslug/ha-at/commit/2eed3e574ffa5d110dc7eff15f0f2591da94111f))
* tell same-time jobs apart when cancelling and end tonight at dawn ([#30](https://github.com/wonderslug/ha-at/issues/30)) ([3addfca](https://github.com/wonderslug/ha-at/commit/3addfca10c5170de5798806c243566ff8a5216f2))
* **todo:** refuse reopening a finished to-do item instead of ignoring it ([#34](https://github.com/wonderslug/ha-at/issues/34)) ([94de397](https://github.com/wonderslug/ha-at/commit/94de39728aee96fc795e9de5744e0e6b9c5981d8))
* **voice:** cancel jobs by relative time instead of raising a parse error ([#4](https://github.com/wonderslug/ha-at/issues/4)) ([fad71b5](https://github.com/wonderslug/ha-at/commit/fad71b56541743123c10ec8281f8b5043e617cca))
* **voice:** check scheduled commands against their intent's targets and name them properly ([#44](https://github.com/wonderslug/ha-at/issues/44)) ([9a10691](https://github.com/wonderslug/ha-at/commit/9a10691fb9f14fbf90f3405b7a00319ede1de0a6))
* **voice:** stop reading a bare hour after 12 as a time and understand 24-hour wording ([#39](https://github.com/wonderslug/ha-at/issues/39)) ([ca6b73f](https://github.com/wonderslug/ha-at/commit/ca6b73f4e5d3b8e794dc24a5c98426d4264cdbac))


### Performance

* **sensor:** keep job lists out of the recorder and share entity setup ([#33](https://github.com/wonderslug/ha-at/issues/33)) ([1e939b1](https://github.com/wonderslug/ha-at/commit/1e939b198c797301373d8f1596c3295b84bcd501))
