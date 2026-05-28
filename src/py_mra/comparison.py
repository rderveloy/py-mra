# Copyright (C) 2026 Robert Derveloy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Match Rating Approach similarity comparison."""

from __future__ import annotations

from itertools import zip_longest

from ._validation import ensure_int, ensure_str
from .codex import match_rating_codex


def _minimum_rating(length_sum: int) -> int:
    """Return the minimum rating required for a match given the code lengths.

    Args:
        length_sum: The sum of the two codices' lengths (non-negative).

    Returns:
        The MRA minimum rating threshold (2-5).

    Raises:
        TypeError: If *length_sum* is not an ``int``.
        ValueError: If *length_sum* is negative.
    """
    ensure_int(length_sum, "length_sum")
    if length_sum < 0:
        raise ValueError(
            "length_sum must be non-negative, got %r" % length_sum
        )
    if length_sum <= 4:
        return 5
    if length_sum <= 7:
        return 4
    if length_sum <= 11:
        return 3
    return 2


def _rating_from_codices(codex1: str, codex2: str) -> int | None:
    """Compute the similarity rating of two already-encoded names.

    Args:
        codex1: The first name's codex.
        codex2: The second name's codex.

    Returns:
        The rating ``6 - max_unmatched``, or ``None`` if the codices' lengths
        differ by three or more (incomparable).

    Raises:
        TypeError: If either *codex1* or *codex2* is not a ``str``.
    """
    ensure_str(codex1, "codex1")
    ensure_str(codex2, "codex2")
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
    reversed_pairs = zip_longest(
        reversed(remaining1), reversed(remaining2)
    )
    for char1, char2 in reversed_pairs:
        if char1 != char2:
            if char1:
                unmatched1 += 1
            if char2:
                unmatched2 += 1

    return 6 - max(unmatched1, unmatched2)


def match_rating(name1: str, name2: str) -> int | None:
    """Return the similarity rating of two names, or ``None`` if incomparable.

    The two names are encoded; if their code lengths differ by three or more
    they are deemed incomparable and ``None`` is returned. Otherwise the codes
    are reduced by removing characters that match position-for-position from
    the left and then from the right; the rating is ``6 - max_unmatched``.

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
    ensure_str(name1, "name1")
    ensure_str(name2, "name2")
    return _rating_from_codices(
        match_rating_codex(name1), match_rating_codex(name2)
    )


def match_rating_comparison(name1: str, name2: str) -> bool | None:
    """Return ``True``/``False`` if two names match per the MRA threshold.

    Args:
        name1: The first name to compare.
        name2: The second name to compare.

    Returns:
        ``True`` or ``False`` for the match decision, or ``None`` when the
        names are incomparable (encoded lengths differ by three or more).

    Raises:
        TypeError: If either name is not a ``str``.
        NumericInputError: If either name contains a numeric character.

    Warns:
        SpecialCharacterWarning: If punctuation or symbols are stripped from
            either name during encoding.
    """
    ensure_str(name1, "name1")
    ensure_str(name2, "name2")
    codex1 = match_rating_codex(name1)
    codex2 = match_rating_codex(name2)

    rating = _rating_from_codices(codex1, codex2)
    if rating is None:
        return None
    return rating >= _minimum_rating(len(codex1) + len(codex2))
