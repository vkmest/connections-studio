"""Enumerate the small final-eight search space before asking a model to rank it."""

from itertools import combinations

from connections.models import SolveRequest


def remaining_options(request: SolveRequest) -> list[list[list[str]]]:
    locked = {word for group in request.locked for word in group.words}
    words = [word for word in request.words if word not in locked]
    if len(words) != 8:
        raise ValueError("Exhaustive option search requires exactly eight unresolved words.")
    remaining = set(words)
    rejected = {frozenset(group) for group in request.rejected}
    previous = {
        frozenset(
            frozenset(group.words)
            for group in attempt.groups
            if set(group.words).issubset(remaining)
        )
        for attempt in request.previous_attempts
    }
    options = []
    # Anchor the first word so swapping the two groups doesn't duplicate a partition.
    for others in combinations(words[1:], 3):
        first = [words[0], *others]
        second = [word for word in words if word not in first]
        partition = frozenset((frozenset(first), frozenset(second)))
        if partition & rejected or partition in previous:
            continue
        options.append([first, second])
    return options
