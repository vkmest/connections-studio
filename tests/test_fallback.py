import random

from test_models import WORDS, groups

from connections.fallback import random_solution
from connections.models import Solution, SolveRequest


def test_random_fallback_uses_every_word_and_has_no_category_claims():
    result = random_solution(SolveRequest(words=WORDS), rng=random.Random(7))
    result.validate_for(SolveRequest(words=WORDS))
    assert all(group.title.startswith("Random test group") for group in result.groups)
    assert all(
        group.confidence == "low" and "Random" in group.explanation for group in result.groups
    )


def test_fallback_preserves_confirmations_and_excludes_feedback_and_history():
    request = SolveRequest(
        words=WORDS,
        locked=groups()[:2],
        rejected=[groups()[2].words],
        previous_attempts=[Solution(groups=groups())],
    )
    result = random_solution(request, rng=random.Random(2))
    result.validate_for(request)
    assert result.groups[:2] == groups()[:2]


def test_no_random_fallback_is_invented_when_last_group_is_excluded():
    request = SolveRequest(words=WORDS, locked=groups()[:3], rejected=[groups()[3].words])
    assert random_solution(request, rng=random.Random(1)) is None
