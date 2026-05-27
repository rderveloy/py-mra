"""Match Rating Approach similarity comparison."""

from itertools import zip_longest

from .codex import match_rating_codex


def _minimum_rating(length_sum):
    if length_sum <= 4:
        return 5
    if length_sum <= 7:
        return 4
    if length_sum <= 11:
        return 3
    return 2


def _rating_from_codices(codex1, codex2):
    """Similarity rating of two already-encoded names, or ``None``."""
    if abs(len(codex1) - len(codex2)) >= 3:
        return None

    res1, res2 = [], []
    for c1, c2 in zip_longest(codex1, codex2):
        if c1 != c2:
            if c1:
                res1.append(c1)
            if c2:
                res2.append(c2)

    unmatched1 = unmatched2 = 0
    for c1, c2 in zip_longest(reversed(res1), reversed(res2)):
        if c1 != c2:
            if c1:
                unmatched1 += 1
            if c2:
                unmatched2 += 1

    return 6 - max(unmatched1, unmatched2)


def match_rating(name1, name2):
    """Return the similarity rating of two names, or ``None`` if incomparable.

    The two names are encoded; if their code lengths differ by three or more
    they are deemed incomparable and ``None`` is returned. Otherwise the codes
    are reduced by removing characters that match position-for-position from the
    left and then from the right, and the rating is ``6 - max_unmatched``.
    """
    return _rating_from_codices(match_rating_codex(name1), match_rating_codex(name2))


def match_rating_comparison(name1, name2):
    """Return ``True``/``False`` if two names match per the MRA threshold.

    Returns ``None`` when the names are incomparable (encoded lengths differ by
    three or more).
    """
    codex1 = match_rating_codex(name1)
    codex2 = match_rating_codex(name2)

    rating = _rating_from_codices(codex1, codex2)
    if rating is None:
        return None
    return rating >= _minimum_rating(len(codex1) + len(codex2))
