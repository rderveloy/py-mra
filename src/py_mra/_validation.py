"""Shared argument-validation helpers.

Per project convention every callable validates its own arguments, including
private helpers, because Python offers no real access control. These helpers
centralize the common checks so each call site stays a single statement while
still raising at that boundary. Each helper is a base case: it inlines its own
checks rather than assuming any caller validated first.
"""

from __future__ import annotations

import re

_DIGIT_CHARS = frozenset("0123456789")


def ensure_str(value: object, label: str) -> str:
    """Return *value* unchanged if it is a ``str``.

    Args:
        value: The argument to validate.
        label: The parameter name, used in the error message.

    Returns:
        *value*.

    Raises:
        TypeError: If *label* is not a ``str``, or *value* is not a ``str``.
    """
    if not isinstance(label, str):
        raise TypeError("label must be a str, got %r" % type(label).__name__)
    if not isinstance(value, str):
        raise TypeError(
            "%s must be a str, got %r" % (label, type(value).__name__)
        )
    return value


def ensure_int(value: object, label: str) -> int:
    """Return *value* unchanged if it is an ``int`` (``bool`` is rejected).

    Args:
        value: The argument to validate.
        label: The parameter name, used in the error message.

    Returns:
        *value*.

    Raises:
        TypeError: If *label* is not a ``str``, or *value* is not an ``int``
            (``bool`` is treated as the wrong type).
    """
    if not isinstance(label, str):
        raise TypeError("label must be a str, got %r" % type(label).__name__)
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            "%s must be an int, got %r" % (label, type(value).__name__)
        )
    return value


def ensure_match(value: object, label: str) -> re.Match:
    """Return *value* unchanged if it is a :class:`re.Match`.

    Args:
        value: The argument to validate.
        label: The parameter name, used in the error message.

    Returns:
        *value*.

    Raises:
        TypeError: If *label* is not a ``str``, or *value* is not a
            :class:`re.Match`.
    """
    if not isinstance(label, str):
        raise TypeError("label must be a str, got %r" % type(label).__name__)
    if not isinstance(value, re.Match):
        raise TypeError(
            "%s must be a re.Match, got %r" % (label, type(value).__name__)
        )
    return value


def ensure_digits(value: object, label: str) -> str:
    """Return *value* if it is a string of ASCII digits (or empty).

    Args:
        value: The argument to validate.
        label: The parameter name, used in the error message.

    Returns:
        *value*.

    Raises:
        TypeError: If *label* is not a ``str``, or *value* is not a ``str``.
        ValueError: If *value* contains any non-``0``-``9`` character.
    """
    ensure_str(value, label)
    if any(char not in _DIGIT_CHARS for char in value):
        raise ValueError(
            "%s must contain only digits, got %r" % (label, value)
        )
    return value


def ensure_has_digit(value: object, label: str) -> str:
    """Return *value* if it is a string containing at least one ASCII digit.

    Args:
        value: The argument to validate.
        label: The parameter name, used in the error message.

    Returns:
        *value*.

    Raises:
        TypeError: If *label* is not a ``str``, or *value* is not a ``str``.
        ValueError: If *value* contains no ``0``-``9`` character.
    """
    ensure_str(value, label)
    if not any(char in _DIGIT_CHARS for char in value):
        raise ValueError(
            "%s must contain at least one digit, got %r" % (label, value)
        )
    return value
