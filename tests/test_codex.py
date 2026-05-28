import warnings

import pytest

from py_mra import (
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
    with pytest.raises(NumericInputError):
        match_rating_codex("Route 66")


def test_unicode_numeric_input_raises():
    # Both are Unicode category N (numeric) characters; rejection must cover
    # the whole category, not just ASCII 0-9, or callers leak a meaningless
    # codex when they paste in localized text.
    with pytest.raises(NumericInputError):
        match_rating_codex("Apt ３")
    with pytest.raises(NumericInputError):
        match_rating_codex("½ pint")


def test_special_characters_warn():
    with pytest.warns(SpecialCharacterWarning):
        code = match_rating_codex("O'Brien")
    assert "'" not in code


def test_whitespace_does_not_warn():
    with warnings.catch_warnings():
        warnings.simplefilter("error", SpecialCharacterWarning)
        match_rating_codex("van der Berg")


def test_non_string_raises_type_error():
    with pytest.raises(TypeError):
        match_rating_codex(None)


def test_empty_string_returns_empty():
    assert match_rating_codex("") == ""


def test_name_with_no_letters_returns_empty_with_warning():
    with pytest.warns(SpecialCharacterWarning):
        assert match_rating_codex("!!!") == ""


def test_injection_like_punctuation_is_stripped():
    # Injection-shaped strings carry only letters and punctuation, so the
    # encoder should strip and warn — never crash or echo the payload back.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SpecialCharacterWarning)
        code = match_rating_codex("Robert'); DROP--")
    assert code.isalpha()


def test_very_long_name_is_handled_and_truncated():
    code = match_rating_codex("Ab" * 10000)
    assert len(code) <= 6
