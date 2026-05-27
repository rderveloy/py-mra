"""Match Rating Approach encoder (the codex)."""

import unicodedata
import warnings

from .exceptions import NumericInputError, SpecialCharacterWarning

_VOWELS = frozenset("AEIOU")


def _to_ascii(name):
    """Transliterate accented/Unicode letters to their nearest ASCII form."""
    decomposed = unicodedata.normalize("NFKD", name)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
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
    """
    if not isinstance(name, str):
        raise TypeError("name must be a str, got %r" % type(name).__name__)

    if any(unicodedata.category(c).startswith("N") for c in name):
        raise NumericInputError(
            "encoder received numeric characters in %r; convert them with "
            "numbers_to_words() first" % name
        )

    ascii_name = _to_ascii(name)

    odd = sorted({c for c in ascii_name if not c.isalpha() and not c.isspace()})
    if odd:
        warnings.warn(
            "stripped non-letter character(s) %s from %r"
            % ("".join(odd), name),
            SpecialCharacterWarning,
            stacklevel=2,
        )

    letters = [c for c in ascii_name.upper() if c.isalpha()]

    codex = []
    for i, c in enumerate(letters):
        if i != 0 and c in _VOWELS:
            continue
        if codex and codex[-1] == c:
            continue
        codex.append(c)

    if len(codex) > 6:
        codex = codex[:3] + codex[-3:]

    return "".join(codex)
