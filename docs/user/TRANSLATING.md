# Translating Scheduled Jobs

You can add or improve a language without writing any code. This page explains what can be translated, how to do it,
and how a translation is reviewed. You need a GitHub account and a text editor.

The maintainer does not speak every language. Automated checks catch structural mistakes, and a native speaker of the
language reads the result before it is called verified.

## What can be translated

A language has up to three parts. You can contribute one or all of them.

| Part                | File                                            | What it covers                                                                       |
| ------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------ |
| Strings and panel   | `custom_components/at/translations/<code>.json` | Everything Home Assistant shows, including the Scheduled Jobs panel (`config_panel`) |
| Voice pack          | `custom_components/at/lang/<code>.py`           | How times, days, numbers and voice sentences are understood and answered             |
| Voice pack examples | `tests/translations/examples/<code>.yaml`       | Phrases in your language with the result each one must give                          |

`<code>` is the language tag Home Assistant uses, such as `de`, `fr` or `pt-BR`. The strings and panel need no
programming. A voice pack is larger work and needs the examples file next to it.

## Translating the strings and panel

1. Copy `custom_components/at/translations/en.json` to `custom_components/at/translations/<code>.json`.
2. Translate the values. Never change the keys on the left of each colon.
3. Keep every `{placeholder}` exactly as written, such as `{name}` or `{count}`. You can move it within the sentence.
   Placeholders in the panel strings are plain `{name}` only. Rephrase a count so it reads well without plural
   forms, for example `Jobs: {count}`.
4. Do not add HTML, web addresses, or spaces at the start or end of a value.
5. Leave out any key you cannot translate yet. A missing key falls back to English, and the report lists it. Do not
   copy the English text in its place.

Do not translate the file names, the keys, or the name of the integration's domain, `at`.

## Adding a voice pack

A voice pack lets people schedule and manage jobs by speaking or typing in your language, such as "in 20 minutes turn
off the kitchen light". It is optional.

1. Copy `custom_components/at/lang/en.py` to `custom_components/at/lang/<code>.py` and translate the word tables,
   sentence templates and responses. Keep each template's `{placeholders}` the same as in English.
2. Register the pack in `_PACKS` in `custom_components/at/lang/__init__.py`, next to the English entry.
3. Copy `tests/translations/examples/en.yaml` to `tests/translations/examples/<code>.yaml` and rewrite it in your
   language.

The examples file is how a reviewer, and the automated checks, see that your pack works. It has a header with a
fixed `now` and `time_zone`, then two lists:

- `times` entries have a `category`, the `text` a person would say, and the `expect`ed date and time. An `expect` of
  `null` means the text must not be understood.
- `sentences` entries have the `text`, the `group` it must match, and optionally the `slots` it must capture.

Cover every category. The six time categories are `relative`, `clock`, `day`, `weekday`, `named` and
`spelled_number`. The five sentence groups are `schedule`, `list`, `cancel`, `run` and `announce`. A category with
no example is reported but does not fail the checks.

## Checking your work

Run these before you open the pull request. They need the project's development environment, described in
[`CONTRIBUTING.md`](../../CONTRIBUTING.md).

```bash
script/test tests/translations
script/translations-report --all
```

`script/test tests/translations` runs the checks as tests. `script/translations-report --all` prints the same report
a pull request gets. Use `--changed-files PATH` instead of `--all` to check only the languages named in a list of
changed files.

What fails, and must be fixed:

- A key that does not exist in English.
- A value that is not a string.
- A changed or missing `{placeholder}`, in the strings or in a voice pack template.
- HTML, a web address, or spaces at the start or end of a value.
- A registered voice pack with no examples file, or an examples file with no registered pack.
- An example whose result differs from `expect`, or one that is malformed.

What is only reported, and never fails:

- Keys you left out of the strings.
- Values identical to English.
- Example categories with no example, and sentence groups the pack leaves empty.

## Opening the pull request

1. Fork the repository and add your files on a branch.
2. Open the pull request with the translation template:
   [`https://github.com/wonderslug/ha-at/compare/main...?template=translation.md`](https://github.com/wonderslug/ha-at/compare/main...?template=translation.md).
   From a fork, pick your branch on that page.
3. Fill in the language code, what you changed, whether you are a native speaker, and how you tried it. Say only what
   you did: running it on a live Home Assistant instance and running only the tests are different things.
4. If you know a native speaker, name them in the "Reviewer I have asked" line.

A pull request that changes only translation files gets a report comment from the automated checks, and labels. If a
check fails, the report says which one and the labels are removed until it passes. A pull request that also changes
code is confirmed by hand.

## Reviewing as a native speaker

A native speaker's approval is what verifies a language. To review a translation pull request:

1. Read the strings and the panel in your language. Check that they are natural and that the meaning matches English.
2. If there is a voice pack, read `tests/translations/examples/<code>.yaml`. Check that each phrase is something a
   person really says, and that the `expect` result is correct.
3. Select **Review changes** on the pull request, then **Approve** or **Request changes**, and write what needs
   fixing.

The pull request author cannot verify their own translation. An approval counts only for the commit it was made on,
so a new push needs a fresh approval. A later review from you replaces your earlier one.

## Verified and unverified

The report comment ends with a review line for each language, and these labels show where a pull request stands:

| Label                              | Meaning                                                             |
| ---------------------------------- | ------------------------------------------------------------------- |
| `translation`                      | The pull request changes translations                               |
| `translation: needs native review` | The checks pass and no native speaker has verified the language yet |
| `translation: verified`            | A native speaker has approved the current commit                    |
| `translation: unverified`          | Nobody verified it within 30 days. It can still be merged           |

A language is verified when one of these is true on the current commit:

- A reviewer listed for that language in [`.github/translation-maintainers.yml`](../../.github/translation-maintainers.yml)
  approves it. The author cannot be that reviewer.
- A repository maintainer approves it together with another approver. This is how a language's first reviewer is
  confirmed, so they can be added to that file afterwards.

The 30 days count from when `translation: needs native review` was applied with the checks passing. After 30 days
without verification the pull request gets `translation: unverified` and a comment saying so. It is not blocked, and
a listed reviewer's approval still verifies it later. A failing check removes the review labels until it passes, and a
pull request that also changes code beyond translations keeps `translation: needs native review` until it is
confirmed by hand.

## Languages

The list of reviewers per language lives in [`.github/translation-maintainers.yml`](../../.github/translation-maintainers.yml).
To become one, ask in a translation pull request for your language.

| Language | Strings and panel | Voice pack | Status          |
| -------- | ----------------- | ---------- | --------------- |
| English  | Yes               | Yes        | Source language |

No other language has been added yet. Yours can be the first.
