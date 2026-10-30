import pytest
from pydantic import ValidationError

from connections.models import Group, Solution, SolveRequest, normalize_words

WORDS = [f"WORD {i}" for i in range(16)]


def groups():
    return [
        Group(
            title=f"Group {i}",
            words=WORDS[i : i + 4],
            explanation="Shared meaning",
            confidence="medium",
        )
        for i in range(0, 16, 4)
    ]


def test_normalize_preserves_phrases_and_collapses_whitespace():
    assert normalize_words(["  Ice   Cream ", "rock'n'roll"]) == ["ICE CREAM", "ROCK'N'ROLL"]


@pytest.mark.parametrize(
    "words", [WORDS[:15], WORDS + ["EXTRA"], [""] + WORDS[1:], ["word 1"] + WORDS[1:]]
)
def test_invalid_board_rejected_before_call(words):
    with pytest.raises(ValueError):
        SolveRequest(words=words)


def test_partition_rejects_duplicate_missing_and_invented_words():
    for replacement in [WORDS[4], "INVENTED"]:
        bad = groups()
        bad[0].words[0] = replacement
        with pytest.raises(ValueError):
            Solution(groups=bad).validate_for(SolveRequest(words=WORDS))


def test_partition_keeps_locked_groups_and_rejects_failed_sets():
    valid = groups()
    request = SolveRequest(words=WORDS, locked=[valid[0]], rejected=[valid[1].words])
    with pytest.raises(ValueError, match="rejected"):
        Solution(groups=valid).validate_for(request)
    changed = groups()
    changed[0].words[0], changed[1].words[0] = changed[1].words[0], changed[0].words[0]
    with pytest.raises(ValueError, match="locked"):
        Solution(groups=changed).validate_for(SolveRequest(words=WORDS, locked=[valid[0]]))


def test_valid_partition_accepted():
    Solution(groups=groups()).validate_for(SolveRequest(words=WORDS))


def test_history_from_another_board_is_rejected():
    previous = Solution(groups=groups())
    previous.groups[0].words[0] = "OTHER BOARD"
    with pytest.raises(ValueError, match="Previous attempts"):
        SolveRequest(words=WORDS, previous_attempts=[previous])


def test_conflicting_locks_and_unknown_rejections_rejected():
    with pytest.raises(ValueError):
        SolveRequest(words=WORDS, locked=[groups()[0], groups()[0]])
    with pytest.raises(ValueError):
        SolveRequest(words=WORDS, rejected=[["UNKNOWN", *WORDS[:3]]])
    with pytest.raises(ValueError):
        SolveRequest(words=WORDS, locked=[groups()[0]], rejected=[WORDS[:4]])


def test_exactly_four_words_per_group():
    with pytest.raises(ValidationError):
        Group(title="Empty", words=WORDS[:3], explanation="test", confidence="low")


@pytest.mark.parametrize("field", ["title", "explanation"])
def test_category_text_cannot_be_visually_empty(field):
    data = groups()[0].model_dump()
    data[field] = " \n\t "
    with pytest.raises(ValidationError):
        Group.model_validate(data)
