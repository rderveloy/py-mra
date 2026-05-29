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

"""Exceptions and warnings raised by py-mra."""


class NumericInputError(ValueError):
    """Raised when a word passed to the encoder contains numeric characters.

    The Match Rating Approach is defined for alphabetic words. Digits have no
    phonetic encoding, so the encoder refuses them rather than silently
    producing a meaningless code. Convert numbers to words first with
    :func:`py_mra.numbers.numbers_to_words`, then tokenize.
    """


class MultiWordInputError(ValueError):
    """Raised when a word passed to the encoder contains internal whitespace.

    The Match Rating Approach is defined for single words; concatenating
    multiple words and treating the result as one name produces a codex that
    no longer reflects the algorithm's design. The encoder refuses such input
    rather than silently producing a misleading code. Split the input with
    :func:`py_mra.tokenize` (or with your own logic) and call the encoder on
    each token separately.
    """


class SpecialCharacterWarning(UserWarning):
    """Warned when non-letter characters are stripped from a word.

    This warning fires only for punctuation or symbols (non-exhaustive
    example: the apostrophe in ``O'Brien``) so callers can detect dirty input
    without being spammed by routine cleanup.
    """
