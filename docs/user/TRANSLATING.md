# Translating Scheduled Jobs

You can add or improve a language's strings and panel without writing any code. A voice pack is Python, so it needs
some. This page explains what can be translated, how to do it,
and how a translation is reviewed. You need a GitHub account and a text editor.

The maintainer does not speak every language. Automated checks catch structural mistakes, and a native speaker of the
language reads the result before it is called verified.

## Reviewing as a native speaker

A native speaker's approval is what verifies a language. If you were asked to review a translation, this is all you
need to do:

1. Open the pull request and select **Files changed**.
2. Read the strings and the panel in your language. Check that they are natural and that the meaning matches English.
3. If there is a voice pack, also read `tests/translations/examples/<code>.yaml`. Check that each phrase is something
   a person really says, and that the `expect` result is correct.
4. Select **Review changes**.
   - If something needs fixing, choose **Request changes** and say what.
   - If it is right, choose **Approve**, and put this line in the review text, with the pull request's language code
     in place of `uk`:

     ```text
     Native speaker review: uk
     ```

5. Select **Submit review**.

The line is your statement that you are a native speaker of that language and reviewed the translation. Without it,
an approval does not count. Put it on a line of its own, exactly as shown. For a pull request with several
languages, add one line for each language you reviewed. You can write anything else you like above or below it.

Your approval counts when all of these are true:

- You chose **Approve**. The line in a comment or a "Request changes" review does not count.
- It is on the latest commit. If the author pushes again, approve again.
- You are not the author of the pull request.
- It is your latest review. A later review from you replaces it.

If you forgot the line, edit your review and add it; you do not need to submit a new one. The labels update a few
minutes after you submit or edit a review.

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

### Announcement sentences

Announcements use five sentence template groups in `sentences`, and the reviewer checks them closely:

| Group                       | What it matches                                                  |
| --------------------------- | ---------------------------------------------------------------- |
| `announce_area`             | A message to one area, with `{area}` and `{message}`             |
| `announce_floor`            | A message to one floor, with `{floor}` and `{message}`           |
| `announce_everyone`         | A message to the whole house, with `{message}` only              |
| `announce_area_no_message`  | A sentence that names an area but has no message, `{area}` only  |
| `announce_floor_no_message` | A sentence that names a floor but has no message, `{floor}` only |

- The place can come before or after the message. When it comes after, put at least one fixed word between
  `{message}` and the place, as English does with `(in|to) [the] {area}`. Home Assistant reads every `{placeholder}`
  in a voice sentence as free text, and two free-text placeholders side by side never match.
- The `_no_message` groups catch a sentence cut off before its message, such as "announce in the kitchen". `at` then
  asks for the message with `no_message_area` or `no_message_floor` from `recognize_errors`, instead of announcing the
  place name. Translate both replies, keeping `{area}` and `{floor}`.
- Leave words such as "that" out of the message with an optional word before it: `[that[s]] {message}`.

The examples file is how a reviewer, and the automated checks, see that your pack works. It has a header with a
fixed `now` and `time_zone`, then two lists:

- `times` entries have a `category`, the `text` a person would say, and the `expect`ed date and time. An `expect` of
  `null` means the text must not be understood.
- `sentences` entries have the `text`, the `group` it must match, and optionally the `slots` it must capture.

Cover every category. The six time categories are `relative`, `clock`, `day`, `weekday`, `named` and
`spelled_number`. The five sentence groups are `schedule`, `list`, `cancel`, `run` and `announce`. A category with
no example is reported but does not fail the checks.

A voice pack is Python that runs in every user's Home Assistant, so the repository maintainer reviews it as code. The
native speaker vouches for the language by reviewing the examples file. Because registering the pack changes
`custom_components/at/lang/__init__.py`, a voice pack pull request is confirmed by the maintainer by hand, and a native
speaker's approval alone does not verify it. Put the strings and the voice pack in separate pull requests, so the
strings can be verified on their own.

## Checking your work

Every translation pull request gets an automatic report comment that runs the same checks. For strings and panel work
you can skip the local checks: if the report shows a failure, fix the file and push again. If you have the project's
development environment, described in [`CONTRIBUTING.md`](../../CONTRIBUTING.md), you can run them first. Voice pack
authors should run them, because a voice pack is code.

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

Every translation pull request gets a report comment from the automated checks, and labels. If a check fails, the
report says which one and the labels are removed until it passes.

### Change only your language's files

A pull request is verified automatically only when every file it changes is one of these, for your language:

- `custom_components/at/translations/<code>.json`
- `custom_components/at/lang/<code>.py`
- `tests/translations/examples/<code>.yaml`

Do not edit this guide, the [Languages](#languages) table, the README, or any other file, even to list your language.
The maintainer updates the table and the reviewer list after your translation is merged. A pull request that changes
any other file keeps `translation: needs native review` until the maintainer confirms it by hand.

A voice pack is the one exception. It has to be registered in `custom_components/at/lang/__init__.py`, so a voice pack
pull request is always confirmed by hand. This is why the strings go in a pull request of their own.

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
  approves it with the `Native speaker review` line. The author cannot be that reviewer.
- Someone not listed approves it with the `Native speaker review` line, and a repository maintainer approves after
  them. This is how a language's first reviewer is confirmed, so they can be added to that file afterwards. The
  maintainer's approval needs no line of its own, but it has to come after the native speaker's; one that comes
  before does not count, so approve again.

The report comment names any approval that has no `Native speaker review` line, and shows the line to paste until
the language is verified.

Only the automation sets `translation: verified`. Do not apply it by hand: the next run removes it.

The 30 days count from when `translation: needs native review` was applied with the checks passing. After 30 days
without verification the pull request gets `translation: unverified` and a comment saying so. It is not blocked, and
a listed reviewer's approval still verifies it later. A failing check removes the review labels until it passes, and a
pull request that also changes code beyond translations keeps `translation: needs native review` until it is
confirmed by hand. This includes every voice pack pull request, which changes `custom_components/at/lang/__init__.py`:
it never gets `translation: verified` or `translation: unverified`, and the maintainer confirms it by hand.

## Languages

The list of reviewers per language lives in [`.github/translation-maintainers.yml`](../../.github/translation-maintainers.yml).
To become one, ask in a translation pull request for your language. The maintainer keeps this table up to date; do not
change it in your pull request.

| Language | Strings and panel | Voice pack | Status          |
| -------- | ----------------- | ---------- | --------------- |
| English  | Yes               | Yes        | Source language |

No other language has been added yet. Yours can be the first.
