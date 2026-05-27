"""Match Rating Approach similarity comparison."""

from itertools import zip_longest

from .codex import match_rating_codex


def _minimum_rating(length_sum):
    """Return the minimum rating required for a match given the code lengths.

    Args:
        length_sum: The sum of the two codices' lengths.

    Returns:
        The MRA minimum rating threshold (2-5).
    """
    if length_sum <= 4:
        return 5
    if length_sum <= 7:
        return 4
    if length_sum <= 11:
        return 3
    return 2


def _rating_from_codices(codex1, codex2):
    """Compute the similarity rating of two already-encoded names.

    Args:
        codex1: The first name's codex.
        codex2: The second name's codex.

    Returns:
        The rating ``6 - max_unmatched``, or ``None`` if the codices' lengths
        differ by three or more (incomparable).
    """
    if abs(len(codex1) - len(codex2)) >= 3:
        return None

    remaining1, remaining2 = [], []
    for char1, char2 in zip_longest(codex1, codex2):
        if char1 != char2:
            if char1:
                remaining1.append(char1)
            if char2:
                remaining2.append(char2)

    unmatched1 = unmatched2 = 0
    for char1, char2 in zip_longest(reversed(remaining1), reversed(remaining2)):
        if char1 != char2:
            if char1:
                unmatched1 += 1
            if char2:
                unmatched2 += 1

    return 6 - max(unmatched1, unmatched2)


def match_rating(name1, name2):
    """Return the similarity rating of two names, or ``None`` if incomparable.

    The two names are encoded; if their code lengths differ by three or more
    they are deemed incomparable and ``None`` is returned. Otherwise the codes
    are reduced by removing characters that match position-for-position from the
    left and then from the right, and the rating is ``6 - max_unmatched``.

    Args:
        name1: The first name to compare.
        name2: The second name to compare.

    Returns:
        The integer similarity rating, or ``None`` if the names are
        incomparable.

    Raises:
        TypeError: If either name is not a ``str``.
        NumericInputError: If either name contains a numeric character.

    Warns:
        SpecialCharacterWarning: If punctuation or symbols are stripped from
            either name during encoding.
    """
    return _rating_from_codices(match_rating_codex(name1), match_rating_codex(name2))


def match_rating_comparison(name1, name2):
    """Return ``True``/``False`` if two names match per the MRA threshold.

    Args:
        name1: The first name to compare.
        name2: The second name to compare.

    Returns:
        ``True`` or ``False`` for the match decision, or ``None`` when the names
        are incomparable (encoded lengths differ by three or more).

    Raises:
        TypeError: If either name is not a ``str``.
        NumericInputError: If either name contains a numeric character.

    Warns:
        SpecialCharacterWarning: If punctuation or symbols are stripped from
            either name during encoding.
    """
    codex1 = match_rating_codex(name1)
    codex2 = match_rating_codex(name2)

    rating = _rating_from_codices(codex1, codex2)
    if rating is None:
        return None
    return rating >= _minimum_rating(len(codex1) + len(codex2))
