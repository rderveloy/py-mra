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

import warnings

import pytest

from py_mra import (
    Codex,
    MultiWordInputError,
    NumericInputError,
    SpecialCharacterWarning,
    match_rating_codex,
)


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Smith", "SMTH"),
        ("Smyth", "SMYTH"),
        ("Catherine", "CTHRN"),
        ("Kathryn", "KTHRYN"),
        ("Byrne", "BYRN"),
        ("Boern", "BRN"),
        ("Knuth", "KNTH"),
    ],
)
def test_known_codices(name, expected):
    assert match_rating_codex(name) == expected


def test_returns_codex_instance():
    # The return type is a Codex, not a plain str, so downstream functions
    # taking Codex parameters accept it without explicit construction.
    assert isinstance(match_rating_codex("Smith"), Codex)


def test_first_letter_vowel_is_kept():
    assert match_rating_codex("Aaron").startswith("A")


def test_long_name_keeps_first_and_last_three():
    code = match_rating_codex("Alexandria")
    assert len(code) == 6
    assert code[:3] + code[-3:] == code


def test_adjacent_duplicates_collapse():
    assert "LL" not in match_rating_codex("Hollow")


def test_transliterates_accents():
    assert match_rating_codex("José") == match_rating_codex("Jose")
    assert match_rating_codex("Müller") == match_rating_codex("Muller")


def test_numeric_input_raises():
    # Single-word numeric input so the test isolates NumericInputError
    # rather than tripping the multi-word rejection first.
    with pytest.raises(NumericInputError):
        match_rating_codex("Route66")


def test_unicode_numeric_input_raises():
    # Both are Unicode category N (numeric) characters; rejection must cover
    # the whole category, not just ASCII 0-9, or callers leak a meaningless
    # codex when they paste in localized text. Single-word inputs so the
    # numeric rejection is the one being exercised.
    with pytest.raises(NumericInputError):
        match_rating_codex("Apt３")
    with pytest.raises(NumericInputError):
        match_rating_codex("½pint")


def test_multi_word_input_raises():
    # MRA encodes a single word; concatenating multiple words produces a
    # codex that doesn't reflect the algorithm's design, so the encoder
    # refuses rather than silently mis-encoding.
    with pytest.raises(MultiWordInputError):
        match_rating_codex("van der Berg")


def test_multi_word_with_tab_or_newline_also_rejected():
    # Any internal whitespace counts as multi-word, not just spaces, so
    # transcription artifacts (tabs, newlines) don't sneak through.
    with pytest.raises(MultiWordInputError):
        match_rating_codex("Smith\tJones")
    with pytest.raises(MultiWordInputError):
        match_rating_codex("Smith\nJones")


def test_leading_and_trailing_whitespace_is_stripped():
    # Stray padding from data-loading should be tolerated rather than
    # rejected, so we strip leading/trailing whitespace before testing
    # for the multi-word condition.
    assert match_rating_codex("  Smith  ") == "SMTH"


def test_special_characters_warn():
    with pytest.warns(SpecialCharacterWarning):
        code = match_rating_codex("O'Brien")
    assert "'" not in code


def test_non_string_raises_type_error():
    with pytest.raises(TypeError):
        match_rating_codex(None)


def test_empty_string_returns_empty():
    assert match_rating_codex("") == Codex("")


def test_name_with_no_letters_returns_empty_with_warning():
    with pytest.warns(SpecialCharacterWarning):
        assert match_rating_codex("!!!") == Codex("")


def test_injection_like_punctuation_is_stripped():
    # Injection-shaped strings carry only letters and punctuation, so the
    # encoder should strip and warn — never crash or echo the payload back.
    # Uses a single-word injection shape so the test isolates the
    # punctuation-stripping behavior from the multi-word rejection.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SpecialCharacterWarning)
        code = match_rating_codex("Robert');DROP--")
    assert code.isalpha()


def test_very_long_name_is_handled_and_truncated():
    code = match_rating_codex("Ab" * 10000)
    assert len(code) <= 6
