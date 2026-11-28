# Native speaker attestation on translation reviews

## Why

An approval on a translation pull request counts today by its state alone; nothing says the approver speaks the
language. The maintainer wants each counted approval to carry an explicit statement from a native speaker, checked by
the triage automation, and the steps a native reviewer must take documented exactly and prominently.

## Goals

- An approval verifies a language only when its text attests native-speaker review of that language.
- A reviewer sees the exact text to paste both in `docs/user/TRANSLATING.md` and on the pull request itself.
- Labels change within minutes of a review, not at the next daily run.

## Non-goals

- Proving anyone's identity or fluency. The attestation is a statement the maintainer can rely on and point to.
- Verifying voice pack pull requests automatically; that waits for #71.

## Anti-goals

- An approval without the attestation counting toward verification, silently.
- The attestation counting in a "Comment" or "Request changes" review.

## Approaches

1. Attestation required on top of today's rules (an unlisted reviewer still needs maintainer confirmation).
2. Attestation verifies on its own, from anyone but the author.
3. **Chosen.** Listed reviewers need the attestation, and it verifies on its own. Anyone else's attested approval
   needs the maintainer's confirmation, as today. Keeps the existing trust model and makes the confirmation step
   meaningful.

## Design

**The attestation** is a line in the review text, on its own line, matched without regard to case or surrounding
spaces:

```text
Native speaker review: uk
```

The code must be one of the pull request's languages, compared the way language codes are compared elsewhere in the
triage (`_` and `-` equivalent, case-insensitive). A pull request with several languages needs one line per language
the reviewer vouches for. Free text after it is for people and is ignored.

**What counts**, per language, on the current head commit, using each reviewer's latest review as today:

| Reviewer                                         | Approve with attestation           | Approve without |
| ------------------------------------------------ | ---------------------------------- | --------------- |
| Listed for the language                          | verifies                           | not counted     |
| Not listed, not the author                       | needs maintainer confirmation      | not counted     |
| Maintainer (write access), after an attested one | confirms it; no attestation needed | —               |

The author never counts. An attested approval from a maintainer who is not listed for the language is treated like
any other unlisted reviewer's.

**The report comment** gains, for a language with no counted approval, the exact block to paste and one line on
selecting **Approve**. An approval that is not counted is named with the reason ("no native speaker attestation for
`uk`").

**Trigger.** A new workflow, `Translation review`, runs on `pull_request_review` (`submitted`, `edited`,
`dismissed`) with no permissions and does nothing but exist; `Translation triage` adds it to its `workflow_run`
triggers and runs the existing daily pass over open translation pull requests when it fires. This works for pull
requests from forks, whose review events only get a read-only token.

**Documentation.** "Reviewing as a native speaker" moves near the top of `docs/user/TRANSLATING.md` as numbered
steps with the paste block, what makes a review count, and that a new push needs a fresh review. The translation pull
request template gets one line pointing reviewers to that section.

## Constraints

- Agents in this repository cannot edit `.github/workflows/`; the maintainer applies the two workflow changes, or
  lifts that restriction for this task.
- The triage reads review text from the API as untrusted data; matching is a fixed line pattern, never evaluated.

## Left to the builder

- Function and field names; whether the review body is stored on `Review` or fetched separately.
- The exact report wording, following the existing report style.
- Test cases, covering every row of the table, the author case, a stale commit, a Comment review with the line, and
  a multi-language pull request.
