"""Match Rating Approach encoder (the codex)."""

import unicodedata
import warnings

from .exceptions import NumericInputError, SpecialCharacterWarning

_VOWELS = frozenset("AEIOU")


def _to_ascii(name):
    """Transliterate accented/Unicode letters to their nearest ASCII form.

    Args:
        name: The text to transliterate.

    Returns:
        *name* decomposed to ASCII with combining marks and non-ASCII
        characters dropped, e.g. ``"José"`` -> ``"Jose"``.
    """
    decomposed = unicodedata.normalize("NFKD", name)
    stripped = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return stripped.encode("ascii", "ignore").decode("ascii")


def match_rating_codex(name):
    """Encode *name* into its Match Rating Approach code.

    Rules:

    1. Reject any input containing numeric characters (raise
       :class:`NumericInputError`); run :func:`py_mra.numbers_to_words` first
       if the name contains numbers.
    2. Transliterate accented letters to ASCII (``"José"`` -> ``"JOSE"``).
    3. Strip remaining non-letters (whitespace silently, punctuation/symbols
       with a :class:`SpecialCharacterWarning`).
    4. Uppercase, keep the first letter, delete subsequent vowels, and collapse
       adjacent duplicate letters.
    5. If the result exceeds six letters, keep the first three and last three.

    Args:
        name: The name to encode. Must be alphabetic (after transliteration);
            digits are rejected rather than silently dropped.

    Returns:
        The MRA codex, e.g. ``"Smith"`` -> ``"SMTH"``. A name with no letters
        (after stripping) yields ``""``.

    Raises:
        TypeError: If *name* is not a ``str``.
        NumericInputError: If *name* contains any numeric character.

    Warns:
        SpecialCharacterWarning: If punctuation or symbols are stripped.
    """
    if not isinstance(name, str):
        raise TypeError("name must be a str, got %r" % type(name).__name__)

    if any(unicodedata.category(char).startswith("N") for char in name):
        raise NumericInputError(
            "encoder received numeric characters in %r; convert them with "
            "numbers_to_words() first" % name
        )

    ascii_name = _to_ascii(name)

    stripped_specials = sorted({
        char for char in ascii_name
        if not char.isalpha() and not char.isspace()
    })
    if stripped_specials:
        warnings.warn(
            "stripped non-letter character(s) %s from %r"
            % ("".join(stripped_specials), name),
            SpecialCharacterWarning,
            stacklevel=2,
        )

    letters = [char for char in ascii_name.upper() if char.isalpha()]

    codex = []
    for position, letter in enumerate(letters):
        if position != 0 and letter in _VOWELS:
            continue
        if codex and codex[-1] == letter:
            continue
        codex.append(letter)

    if len(codex) > 6:
        codex = codex[:3] + codex[-3:]

    return "".join(codex)
