"""py-mra: a Python implementation of the Match Rating Approach algorithm.

Typical use::

    from py_mra import match_rating_codex, match_rating_comparison

    match_rating_codex("Smith")            # -> "SMTH"
    match_rating_comparison("Smith", "Smyth")  # -> True

Names containing numbers must be expanded first::

    from py_mra import numbers_to_words, match_rating_codex

    match_rating_codex(numbers_to_words("Route 66"))
"""

from .codex import match_rating_codex
from .comparison import match_rating, match_rating_comparison
from .exceptions import NumericInputError, SpecialCharacterWarning
from .numbers import int_to_cardinal, numbers_to_words

__version__ = "0.1.0"

__all__ = [
    "match_rating_codex",
    "match_rating",
    "match_rating_comparison",
    "numbers_to_words",
    "int_to_cardinal",
    "NumericInputError",
    "SpecialCharacterWarning",
]
