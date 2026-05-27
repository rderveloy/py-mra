import re

import pytest

from py_mra._validation import (
    ensure_digits,
    ensure_has_digit,
    ensure_int,
    ensure_match,
    ensure_str,
)


# --- happy paths return the value unchanged ----------------------------------

def test_ensure_str_returns_value():
    assert ensure_str("hi", "label") == "hi"


def test_ensure_int_returns_value():
    assert ensure_int(7, "label") == 7


def test_ensure_match_returns_value():
    match = re.match(r".", "a")
    assert ensure_match(match, "label") is match


@pytest.mark.parametrize("digits", ["", "0", "90210"])
def test_ensure_digits_returns_value(digits):
    assert ensure_digits(digits, "label") == digits


@pytest.mark.parametrize("value", ["5", "a5", "12x"])
def test_ensure_has_digit_returns_value(value):
    assert ensure_has_digit(value, "label") == value


# --- wrong types raise TypeError ---------------------------------------------

@pytest.mark.parametrize("bad", [5, None, b"x", ["x"]])
def test_ensure_str_rejects_non_str(bad):
    with pytest.raises(TypeError):
        ensure_str(bad, "label")


@pytest.mark.parametrize("bad", ["5", None, 3.0, True])
def test_ensure_int_rejects_non_int(bad):
    with pytest.raises(TypeError):
        ensure_int(bad, "label")


@pytest.mark.parametrize("bad", ["x", None, 5])
def test_ensure_match_rejects_non_match(bad):
    with pytest.raises(TypeError):
        ensure_match(bad, "label")


def test_ensure_digits_rejects_non_str():
    with pytest.raises(TypeError):
        ensure_digits(123, "label")


def test_ensure_has_digit_rejects_non_str():
    with pytest.raises(TypeError):
        ensure_has_digit(123, "label")


# --- a non-string label is itself rejected -----------------------------------

@pytest.mark.parametrize("validator", [ensure_str, ensure_int, ensure_match])
def test_validators_reject_non_string_label(validator):
    with pytest.raises(TypeError):
        validator("value", 123)


# --- value-domain violations raise ValueError --------------------------------

@pytest.mark.parametrize("bad", ["12a", "1 2", "½", "1.5"])
def test_ensure_digits_rejects_non_digit_characters(bad):
    with pytest.raises(ValueError):
        ensure_digits(bad, "label")


@pytest.mark.parametrize("bad", ["", "abc", "   ", "½"])
def test_ensure_has_digit_rejects_no_ascii_digit(bad):
    with pytest.raises(ValueError):
        ensure_has_digit(bad, "label")
