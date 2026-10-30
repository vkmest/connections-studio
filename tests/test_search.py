from test_models import WORDS, groups

from connections.models import Solution, SolveRequest
from connections.search import remaining_options


def key(partition):
    return frozenset(frozenset(words) for words in partition)


def test_all_35_splits_cover_eight_words_once_without_order_duplicates():
    options = remaining_options(SolveRequest(words=WORDS, locked=groups()[:2]))
    assert len(options) == 35
    assert len({key(option) for option in options}) == 35
    for option in options:
        assert len(option) == 2 and all(len(words) == 4 for words in option)
        assert sorted(word for words in option for word in words) == sorted(WORDS[8:])


def test_rejections_and_previous_partitions_are_removed_before_model_sees_choices():
    original = SolveRequest(words=WORDS, locked=groups()[:2])
    all_options = remaining_options(original)
    request = SolveRequest(
        words=WORDS,
        locked=groups()[:2],
        rejected=[all_options[1][1]],
        previous_attempts=[Solution(groups=groups())],
    )
    options = remaining_options(request)
    assert len(options) == 33
    assert key(all_options[0]) not in {key(option) for option in options}
    assert all(set(all_options[1][1]) != set(words) for option in options for words in option)


def test_all_rejected_options_leave_no_candidates():
    all_options = remaining_options(SolveRequest(words=WORDS, locked=groups()[:2]))
    # History and rejection limits are independently bounded at 32.
    request = SolveRequest(
        words=WORDS,
        locked=groups()[:2],
        rejected=[option[0] for option in all_options[:32]],
        previous_attempts=[
            Solution(
                groups=[
                    *groups()[:2],
                    *(
                        groups()[index + 2].model_copy(update={"words": words})
                        for index, words in enumerate(option)
                    ),
                ]
            )
            for option in all_options[32:]
        ],
    )
    assert remaining_options(request) == []
