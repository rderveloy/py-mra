import pytest

from py_mra import match_rating, match_rating_comparison, numbers_to_words


@pytest.mark.parametrize(
    "a, b",
    [
        ("Smith", "Smyth"),
        ("Catherine", "Kathryn"),
        ("Robert", "Rupert"),
    ],
)
def test_matches(a, b):
    assert match_rating_comparison(a, b) is True


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
    assert match_rating_comparison("Smith", "Smyth") == match_rating_comparison(
        "Smyth", "Smith"
    )


def test_pipeline_with_numbers():
    # Numbers must be expanded before comparison.
    a = numbers_to_words("Route 66")
    b = numbers_to_words("Route sixty six")
    assert match_rating_comparison(a, b) is True
