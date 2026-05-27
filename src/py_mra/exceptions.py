"""Exceptions and warnings raised by py-mra."""


class NumericInputError(ValueError):
    """Raised when a name passed to the encoder contains numeric characters.

    The Match Rating Approach is defined for alphabetic names. Digits have no
    phonetic encoding, so the encoder refuses them rather than silently
    producing a meaningless code. Convert numbers to words first with
    :func:`py_mra.numbers.numbers_to_words`.
    """


class SpecialCharacterWarning(UserWarning):
    """Warned when non-letter characters are stripped from a name.

    Whitespace is normalized silently; this warning fires only for punctuation
    or symbols (e.g. the apostrophe in ``O'Brien``) so callers can detect dirty
    input without being spammed by ordinary multi-word names.
    """
