import pytest

from py_mra import (
    NumericInputError,
    match_rating,
    match_rating_comparison,
    numbers_to_words,
)


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
    # Very different code lengths -> incomparable.
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
    # Numbers must be expanded before comparison.
    numeric_form = numbers_to_words("Route 66")
    spelled_form = numbers_to_words("Route sixty six")
    assert match_rating_comparison(numeric_form, spelled_form) is True


def test_comparison_rejects_non_string():
    with pytest.raises(TypeError):
        match_rating_comparison("Smith", None)
    with pytest.raises(TypeError):
        match_rating(5, "Smith")


def test_comparison_rejects_numeric_input():
    with pytest.raises(NumericInputError):
        match_rating_comparison("Route 66", "Route 66")
