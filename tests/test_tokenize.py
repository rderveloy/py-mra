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

import pytest

from py_mra import match_rating_codex, tokenize


def test_simple_whitespace_split():
    assert tokenize("Mary Ann") == ["Mary", "Ann"]


def test_collapses_runs_of_whitespace():
    # Multiple spaces / tabs / newlines all collapse to a single split, the
    # same way str.split() handles them — predictable and consistent.
    assert tokenize("Mary   Ann\tJones\nSmith") == [
        "Mary", "Ann", "Jones", "Smith"
    ]


def test_empty_string_returns_empty_list():
    assert tokenize("") == []


def test_whitespace_only_returns_empty_list():
    # No tokens to encode means the caller has nothing to do; empty list is
    # the natural signal, not a raised exception.
    assert tokenize("   \t \n  ") == []


def test_strips_leading_and_trailing_whitespace():
    assert tokenize("  Mary Ann  ") == ["Mary", "Ann"]


def test_single_word_is_one_token():
    assert tokenize("Smith") == ["Smith"]


def test_preserves_internal_punctuation():
    # Punctuation embedded within tokens is left attached — the encoder
    # strips it (with a warning) on each per-token call.
    assert tokenize("Smith,John") == ["Smith,John"]
    assert tokenize("O'Brien") == ["O'Brien"]


def test_pipeline_per_token_encoding():
    # The documented pipeline: tokenize, then encode each token; this
    # exercises that end to end and confirms the result feeds the encoder
    # without raising.
    tokens = tokenize("Mary Ann Jones")
    codices = [match_rating_codex(token) for token in tokens]
    assert all(isinstance(code, str) for code in codices)
    assert len(codices) == 3


@pytest.mark.parametrize("bad", [None, 123, b"hi", ["x"]])
def test_rejects_non_string(bad):
    with pytest.raises(TypeError):
        tokenize(bad)
