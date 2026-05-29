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

from py_mra import (
    Codex,
    MultiWordInputError,
    NumericInputError,
    SpecialCharacterWarning,
    comparison_from_codices,
    match_rating,
    match_rating_codex,
    match_rating_comparison,
    numbers_to_words,
    rating_from_codices,
)
from py_mra.comparison import _minimum_rating


@pytest.mark.parametrize(
    "first_name, second_name",
    [
        ("Smith", "Smyth"),
        ("Catherine", "Kathryn"),
        ("Robert", "Rupert"),
    ],
)
def test_matches(first_name, second_name):
    assert match_rating_comparison(first_name, second_name) is True


def test_clear_mismatch():
    assert match_rating_comparison("Smith", "Johnson") is False


def test_incomparable_lengths_return_none():
    assert match_rating_comparison("Al", "Alexandria") is None


def test_match_rating_is_int_or_none():
    rating = match_rating("Smith", "Smyth")
    assert isinstance(rating, int)
    assert match_rating("Al", "Alexandria") is None


def test_symmetry():
    forward = match_rating_comparison("Smith", "Smyth")
    backward = match_rating_comparison("Smyth", "Smith")
    assert forward == backward


def test_pipeline_with_numbers():
    # Expanding numbers produces multi-word output, so the documented
    # pipeline is now numbers_to_words -> split into tokens -> encode each
    # token. This exercises that per-token contract end to end.
    numeric_tokens = numbers_to_words("Route 66").split()
    spelled_tokens = numbers_to_words("Route sixty six").split()
    assert numeric_tokens == spelled_tokens
    for numeric_token, spelled_token in zip(numeric_tokens, spelled_tokens):
        assert match_rating_comparison(numeric_token, spelled_token) is True


def test_comparison_rejects_non_string():
    with pytest.raises(TypeError):
        match_rating_comparison("Smith", None)
    with pytest.raises(TypeError):
        match_rating(5, "Smith")


def test_comparison_rejects_numeric_input():
    # Single-word numeric input so the test isolates NumericInputError
    # rather than tripping the multi-word rejection first.
    with pytest.raises(NumericInputError):
        match_rating_comparison("Route66", "Route66")


def test_match_rating_rejects_numeric_input():
    with pytest.raises(NumericInputError):
        match_rating("Route66", "Smith")


def test_comparison_rejects_multi_word_input():
    with pytest.raises(MultiWordInputError):
        match_rating_comparison("Mary Ann", "Mary Ann")


def test_match_rating_rejects_multi_word_input():
    with pytest.raises(MultiWordInputError):
        match_rating("Mary Ann", "Smith")


def test_comparison_warns_on_special_characters():
    # The warning is part of the comparison contract too, not just the
    # encoder's, so callers can detect dirty inputs at either entry point.
    with pytest.warns(SpecialCharacterWarning):
        match_rating_comparison("O'Brien", "OBrien")


def test_short_names_high_threshold_match():
    # Names chosen for codex sum 4 — the strictest threshold (>=5). A True
    # result here verifies the high-threshold branch of _minimum_rating.
    assert match_rating_comparison("Al", "Ale") is True


def test_short_names_high_threshold_non_match():
    # Same sum-4 threshold, but a rating of 4 must fail; pins the lower
    # boundary of the strictest band.
    assert match_rating_comparison("Al", "Ed") is False


def test_mid_length_threshold_match():
    # Codices summing 5 land in the >=4 band; pins the middle threshold.
    assert match_rating_comparison("Sam", "Sammy") is True


def test_long_names_low_threshold():
    # Codices summing >= 12 (both length-6) land in the lowest >=2 band;
    # pins the deepest tier of _minimum_rating.
    # "Christopher" -> CHRPHR (6) and "Kathryn" -> KTHRYN (6) sum to 12.
    assert match_rating_comparison("Christopher", "Kathryn") is False


def test_minimum_rating_rejects_negative():
    with pytest.raises(ValueError):
        _minimum_rating(-1)


def test_minimum_rating_rejects_non_int():
    with pytest.raises(TypeError):
        _minimum_rating("5")


# --- codex-taking batch path -------------------------------------------------

def test_rating_from_codices_matches_name_path():
    # The codex-taking path must produce identical results to the name-taking
    # convenience path; this is the contract that lets users switch to the
    # batch idiom without surprises.
    codex1 = match_rating_codex("Smith")
    codex2 = match_rating_codex("Smyth")
    assert rating_from_codices(codex1, codex2) == match_rating(
        "Smith", "Smyth"
    )


def test_comparison_from_codices_matches_name_path():
    codex1 = match_rating_codex("Smith")
    codex2 = match_rating_codex("Smyth")
    assert comparison_from_codices(codex1, codex2) == (
        match_rating_comparison("Smith", "Smyth")
    )


def test_rating_from_codices_incomparable_lengths_return_none():
    codex1 = match_rating_codex("Al")
    codex2 = match_rating_codex("Alexandria")
    assert rating_from_codices(codex1, codex2) is None


def test_comparison_from_codices_incomparable_lengths_return_none():
    codex1 = match_rating_codex("Al")
    codex2 = match_rating_codex("Alexandria")
    assert comparison_from_codices(codex1, codex2) is None


def test_rating_from_codices_rejects_plain_str():
    # A plain str "SMTH" happens to be codex-shaped but isn't a Codex
    # instance; the boundary check protects callers from accidentally
    # passing names where codices are expected.
    with pytest.raises(TypeError):
        rating_from_codices("SMTH", "SMYTH")


def test_comparison_from_codices_rejects_plain_str():
    with pytest.raises(TypeError):
        comparison_from_codices("SMTH", "SMYTH")
