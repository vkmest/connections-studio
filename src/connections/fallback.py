"""Local random test arrangements, never presented as model/category evidence."""

import random

from connections.models import Group, Solution, SolveRequest
from connections.search import remaining_options


def random_solution(request: SolveRequest, *, rng=None) -> Solution | None:
    request = SolveRequest.model_validate(request.model_dump())
    rng = rng or random.SystemRandom()
    locked_words = {word for group in request.locked for word in group.words}
    remaining = [word for word in request.words if word not in locked_words]
    if not remaining:
        return Solution(groups=[group.model_copy(deep=True) for group in request.locked])
    options = remaining_options(request) if len(remaining) == 8 else None
    if options == []:
        return None
    for _ in range(256):
        if options is not None:
            partition = rng.choice(options)
        else:
            shuffled = rng.sample(remaining, len(remaining))
            partition = [shuffled[index : index + 4] for index in range(0, len(shuffled), 4)]
        groups = [group.model_copy(deep=True) for group in request.locked]
        for words in partition:
            groups.append(
                Group(
                    title=f"Random test group {len(groups) + 1}",
                    words=words,
                    explanation="Random arrangement for testing in the game. "
                    "No category connection has been identified.",
                    confidence="low",
                )
            )
        solution = Solution(groups=groups)
        try:
            solution.validate_for(request)
            return solution
        except ValueError:
            continue
    return None
