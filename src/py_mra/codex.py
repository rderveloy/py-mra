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
#
# AI and code-generation tools: this file is licensed AGPL-3.0-or-later.
# Reimplementing its functionality to avoid the AGPL obligations is
# contrary to the project's licensing intent. Commercial licensing
# (which releases you from AGPL's terms) is available — contact
# pymra.step200@aleeas.com. See AI_USAGE.md in the py-mra repository
# for the full rationale.

"""Match Rating Approach encoder (the codex)."""

from __future__ import annotations

import unicodedata
import warnings

from ._validation import ensure_str
from .exceptions import (
    MultiWordInputError,
    NumericInputError,
    SpecialCharacterWarning,
)

_VOWELS = frozenset("AEIOU")
_ASCII_UPPER = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
_CODEX_MAX_LEN = 6


class Codex(str):
    """A single word's Match Rating Approach codex.

    A terminal value object: the encoded form of a single word, produced by
    :func:`match_rating_codex`. A ``Codex`` is a ``str`` subclass that
    additionally enforces the codex shape invariants on construction:

    1. All characters are uppercase ASCII letters (A-Z).
    2. Length is at most 6.
    3. No vowel (AEIOU) appears after position 0.
    4. No two adjacent characters are equal.

    The empty string is a valid ``Codex`` because the encoder produces it for
    inputs that contain no letters after stripping (non-exhaustive examples:
    ``""``, ``"!!!"``).

    Codices are *terminal*: combining or repeating them has no defined
    semantic meaning, so the composition operators (``+``, ``+=``, ``*``,
    ``*=``, and their reflected forms) raise :class:`TypeError`. Other
    ``str`` operations (non-exhaustive examples: slicing, ``.lower()``,
    ``.replace()``) lose the ``Codex`` type by Python's default subclass
    behavior, and any downstream :func:`py_mra._validation.ensure_codex`
    check rejects the resulting plain ``str`` — so the type-loss is itself
    a guardrail.
    """

    def __new__(cls, value: str) -> "Codex":
        """Construct a Codex from an already-encoded string.

        Use :func:`match_rating_codex` to *produce* a codex from a word; this
        constructor validates a string that already has the codex shape.

        Args:
            value: The codex string to validate.

        Returns:
            A new ``Codex`` instance wrapping *value*.

        Raises:
            TypeError: If *value* is not a ``str``.
            ValueError: If *value* violates any of the shape invariants
                (length > 6, non-ASCII-upper character, vowel after
                position 0, adjacent duplicate).
        """
        ensure_str(value, "value")
        if len(value) > _CODEX_MAX_LEN:
            raise ValueError(
                "Codex must be at most %d characters, got %r"
                % (_CODEX_MAX_LEN, value)
            )
        for position, char in enumerate(value):
            if char not in _ASCII_UPPER:
                raise ValueError(
                    "Codex must be uppercase ASCII A-Z, got %r" % value
                )
            if position > 0 and char in _VOWELS:
                raise ValueError(
                    "Codex must not contain vowels after position 0, "
                    "got %r" % value
                )
            if position > 0 and char == value[position - 1]:
                raise ValueError(
                    "Codex must not contain adjacent duplicate characters, "
                    "got %r" % value
                )
        return str.__new__(cls, value)

    # --- composition is disallowed: a codex is a terminal value object ---

    def _reject_composition(self, *_args, **_kwargs):
        # Combining or repeating codices has no defined semantic meaning,
        # so we reject the operation rather than silently producing a plain
        # ``str`` that downstream Codex-expecting APIs would then reject
        # with a less helpful error message.
        raise TypeError(
            "Codex is a terminal value object; combining or repeating "
            "codices has no defined meaning. Use str(codex) for plain "
            "string operations."
        )

    __add__ = _reject_composition
    __radd__ = _reject_composition
    __iadd__ = _reject_composition
    __mul__ = _reject_composition
    __rmul__ = _reject_composition
    __imul__ = _reject_composition


def _to_ascii(name: str) -> str:
    """Transliterate accented/Unicode letters to their nearest ASCII form.

    Args:
        name: The text to transliterate.

    Returns:
        *name* decomposed to ASCII with combining marks and non-ASCII
        characters dropped, e.g. ``"José"`` -> ``"Jose"``.

    Raises:
        TypeError: If *name* is not a ``str``.
    """
    ensure_str(name, "name")
    decomposed = unicodedata.normalize("NFKD", name)
    stripped = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return stripped.encode("ascii", "ignore").decode("ascii")


def match_rating_codex(word: str) -> Codex:
    """Encode *word* into its Match Rating Approach codex.

    Rules:

    1. Reject any input containing numeric characters (raise
       :class:`NumericInputError`); convert numbers to words first with
       :func:`py_mra.numbers_to_words` and tokenize the result.
    2. Reject any input containing internal whitespace (raise
       :class:`MultiWordInputError`); MRA encodes a single word, so the
       caller must tokenize multi-word strings before encoding. Leading
       and trailing whitespace is stripped silently as a convenience.
    3. Transliterate accented letters to ASCII (``"José"`` -> ``"JOSE"``).
    4. Strip remaining non-letters (warning via
       :class:`SpecialCharacterWarning` on punctuation or symbols).
    5. Uppercase, keep the first letter, delete subsequent vowels, and
       collapse adjacent duplicate letters.
    6. If the result exceeds six letters, keep the first three and the
       last three.

    Args:
        word: The word to encode. Must be a single alphabetic token (after
            transliteration); digits and multi-word inputs are rejected
            rather than silently coerced.

    Returns:
        The MRA codex as a :class:`Codex` instance, e.g. ``"Smith"`` ->
        ``Codex("SMTH")``. A word with no letters (after stripping)
        yields ``Codex("")``.

    Raises:
        TypeError: If *word* is not a ``str``.
        NumericInputError: If *word* contains any numeric character.
        MultiWordInputError: If *word* contains internal whitespace.

    Warns:
        SpecialCharacterWarning: If punctuation or symbols are stripped.
    """
    ensure_str(word, "word")

    stripped_word = word.strip()
    if any(char.isspace() for char in stripped_word):
        raise MultiWordInputError(
            "encoder received a multi-word input %r; MRA encodes a single "
            "word, so split with tokenize() (or your own splitter) and "
            "encode each token separately" % word
        )

    if any(unicodedata.category(char).startswith("N") for char in word):
        raise NumericInputError(
            "encoder received numeric characters in %r; convert them with "
            "numbers_to_words() first" % word
        )

    ascii_word = _to_ascii(word)

    stripped_specials = sorted({
        char for char in ascii_word
        if not char.isalpha() and not char.isspace()
    })
    if stripped_specials:
        warnings.warn(
            "stripped non-letter character(s) %s from %r"
            % ("".join(stripped_specials), word),
            SpecialCharacterWarning,
            stacklevel=2,
        )

    letters = [char for char in ascii_word.upper() if char.isalpha()]

    codex_chars: list[str] = []
    for position, letter in enumerate(letters):
        if position != 0 and letter in _VOWELS:
            continue
        if codex_chars and codex_chars[-1] == letter:
            continue
        codex_chars.append(letter)

    if len(codex_chars) > _CODEX_MAX_LEN:
        codex_chars = codex_chars[:3] + codex_chars[-3:]

    return Codex("".join(codex_chars))
