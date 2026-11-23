"""The shared sentence matcher: runtime and translation checks pick groups through it."""

import pytest

from custom_components.at.ha_internal.sentence_triggers import (
    LanguageSentences,
    SentenceGroup,
    TriggerInput,
    match_sentence,
)
from custom_components.at.lang.en import EN
from custom_components.at.voice.triggers import sentence_groups


async def _noop(_given: TriggerInput) -> str:
    return ""


EN_SENTENCES = LanguageSentences(
    "en",
    [SentenceGroup(name, sentences, _noop) for name, sentences in sentence_groups(EN, defer_relative=False)],
    EN.sentence_lists,
    _noop,
)


def test_group_order() -> None:
    names = [name for name, _ in sentence_groups(EN, defer_relative=False)]
    assert names == ["cancel", "list", "announce", "schedule", "run"]


def test_defer_relative_drops_relative_schedule() -> None:
    groups = dict(sentence_groups(EN, defer_relative=True))
    assert not set(EN.sentences["schedule_relative"]) & set(groups["schedule"])


@pytest.mark.parametrize(
    ("text", "group"),
    [
        ("in 10 minutes turn off the kitchen light", "schedule"),
        ("what's scheduled", "list"),
        ("cancel all jobs", "cancel"),
        ("cancel the 6am job", "cancel"),
        ("run the morning routine", "run"),
    ],
)
def test_match_sentence_picks_group(text: str, group: str) -> None:
    match = match_sentence(EN_SENTENCES, text)
    assert match is not None
    assert match.group.name == group


def test_match_sentence_returns_wildcards() -> None:
    match = match_sentence(EN_SENTENCES, "in 10 minutes turn off the kitchen light")
    assert match is not None
    assert match.wildcards["command"] == "turn off the kitchen light"


def test_unmatched_sentence_returns_none() -> None:
    assert match_sentence(EN_SENTENCES, "what is the weather") is None
