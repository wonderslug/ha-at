"""The shared sentence matcher: runtime and translation checks pick groups through it."""

import pytest

from custom_components.at.ha_internal.sentence_triggers import (
    LanguageSentences,
    SentenceGroup,
    TriggerInput,
    match_sentence,
)
from custom_components.at.lang.en import EN
from custom_components.at.voice.announce import trigger_sentences
from custom_components.at.voice.triggers import sentence_groups
from homeassistant.components.conversation.trigger import has_no_punctuation, is_valid_sentence


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
        ("announce that its bed time in the suite room", "announce"),
        ("tell everyone that dinner is ready in the kitchen", "announce"),
        ("announce in the suite room", "announce"),
        ("in 5 minutes announce the pizza is here in the kitchen", "schedule"),
        ("at 11pm announce in the kitchen", "schedule"),
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


def test_announcement_trigger_sentences() -> None:
    """Place-last sentences register whole; the no-message ones would catch every "tell ..." and stay out."""
    sentences = trigger_sentences(EN)

    assert "(announce|broadcast) [that[s]] {message} (in|to) [the] {area}" in sentences
    assert "tell (everyone|everybody) [that[s]] {message} (on|in) [the] {floor}" in sentences
    assert not {*EN.sentences["announce_area_no_message"], *EN.sentences["announce_floor_no_message"]} & set(sentences)
    assert has_no_punctuation(sentences) == sentences
    assert is_valid_sentence(sentences) == sentences
