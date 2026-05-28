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
from .numbers import (
    NumberType,
    classify,
    int_to_cardinal,
    number_to_words,
    numbers_to_words,
)

__version__ = "0.1.0"

__all__ = [
    "match_rating_codex",
    "match_rating",
    "match_rating_comparison",
    "numbers_to_words",
    "number_to_words",
    "classify",
    "NumberType",
    "int_to_cardinal",
    "NumericInputError",
    "SpecialCharacterWarning",
]
