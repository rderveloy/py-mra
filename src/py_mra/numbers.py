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

"""Convert numeric runs in text into spoken words.

The Match Rating Approach encoder refuses numeric input. This module is the
explicit opt-in path for callers who want numbers expanded into words before
encoding. :func:`numbers_to_words` scans a string and replaces each numeric run
with words, choosing a style based on context:

* currency      -- ``"$19.99"`` -> ``"nineteen dollars and ninety nine cents"``
* unit/apt/box  -- ``"Apt 4B"`` -> ``"Apt four B"`` (label kept, id read out)
* phone         -- ``"555-1234"`` -> ``"five five five one two three four"``
* zip code      -- ``"90210-1234"`` -> ``"nine zero two one zero one two ..."``
* decimal       -- ``"3.14"`` -> ``"three point one four"``
* integer       -- ``"66"`` -> ``"sixty six"`` (cardinal)

Style by context: *quantities* (bare integers such as a house number) are read
as cardinals, while *identifiers* (zip codes, apartment/unit/suite/box numbers)
are read digit by digit, since they are labels rather than amounts and are
often alphanumeric (``"4B"``). Output is space-separated with no hyphens, so it
flows cleanly into the encoder. The phone, zip and unit heuristics are
intentionally simple and documented here so they can be tuned for a dataset.

Two levels of API are provided:

* :func:`numbers_to_words` scans free text and auto-detects each numeric run.
  Pass ``kind`` to force every run to a single :class:`NumberType` instead.
* :func:`number_to_words` converts a single field value. Pass ``kind`` when the
  caller already knows the type, or omit it to let :func:`classify` guess.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from enum import Enum
from types import MappingProxyType

from ._validation import (
    ensure_digits,
    ensure_has_digit,
    ensure_int,
    ensure_match,
    ensure_str,
)

_DIGIT_CHARS = frozenset("0123456789")


class NumberType(Enum):
    """The kind of number a value represents, used to pick a verbalization.

    The styles are: ``CARDINAL`` reads a quantity as words (``"66"`` ->
    ``"sixty six"``); ``DECIMAL`` reads the whole as a cardinal and the
    fraction digit by digit (``"3.14"`` -> ``"three point one four"``);
    ``CURRENCY`` formats money with unit names (``"$19.99"`` -> ``"nineteen
    dollars and ninety nine cents"``); ``PHONE`` reads the digits individually
    (``"555-1234"`` -> ``"five five five one two three four"``);
    ``ZIP`` likewise reads a postal code's digits (``"90210"`` -> ``"nine zero
    two one zero"``);
    and ``UNIT`` reads an identifier alphanumerically, keeping letters and
    spelling digits (``"4B"`` -> ``"four B"``).
    """

    CARDINAL = "cardinal"
    DECIMAL = "decimal"
    CURRENCY = "currency"
    PHONE = "phone"
    ZIP = "zip"
    UNIT = "unit"


_ONES = (
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen",
)
_TENS = (
    "", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
    "eighty", "ninety",
)
_SCALES = (
    "", "thousand", "million", "billion", "trillion", "quadrillion",
    "quintillion",
)

# Tuples and MappingProxyType keep the lookup tables read-only: a caller
# reaching in to "fix" a name (e.g. mutating _CURRENCY["$"]) would silently
# corrupt every subsequent conversion, so close that hole at the boundary.
_DIGIT_WORDS = MappingProxyType(
    {str(digit): _ONES[digit] for digit in range(10)}
)

_CURRENCY = MappingProxyType({
    "$": (("dollar", "dollars"), ("cent", "cents")),
    "£": (("pound", "pounds"), ("penny", "pence")),
    "€": (("euro", "euros"), ("cent", "cents")),
})


def _words_under_1000(number: int) -> list[str]:
    """Return the word tokens for an integer in 1..999.

    Args:
        number: An integer strictly between 0 and 1000.

    Returns:
        A list of word tokens, e.g. ``221`` -> ``["two", "hundred", "twenty",
        "one"]``.

    Raises:
        TypeError: If *number* is not an ``int``.
        ValueError: If *number* is not in the range 1..999.
    """
    ensure_int(number, "number")
    if not 1 <= number <= 999:
        raise ValueError("number must be in 1..999, got %r" % number)
    words = []
    if number >= 100:
        words.append(_ONES[number // 100])
        words.append("hundred")
        number %= 100
    if number >= 20:
        words.append(_TENS[number // 10])
        number %= 10
        if number:
            words.append(_ONES[number])
    elif number > 0:
        words.append(_ONES[number])
    return words


def int_to_cardinal(number: int) -> str:
    """Render an integer as cardinal words (American style, no "and").

    Args:
        number: The integer to convert. Negative values are rendered with a
            leading "negative".

    Returns:
        The number written out, e.g. ``42`` -> ``"forty two"``, ``-5`` ->
        ``"negative five"``. Numbers beyond the largest named scale
        (>= 10**21) are read digit by digit.

    Raises:
        TypeError: If *number* is not an ``int`` (``bool`` is rejected).
    """
    ensure_int(number, "number")
    if number < 0:
        return "negative " + int_to_cardinal(-number)
    if number == 0:
        return "zero"

    chunks = []
    remaining = number
    while remaining > 0:
        chunks.append(remaining % 1000)
        remaining //= 1000

    if len(chunks) > len(_SCALES):
        # No word exists for groups beyond the largest named scale, so fall
        # back to reading the digits one by one. (This also sidesteps
        # CPython's int<->str length cap on very long inputs.)
        return _digits_to_words(str(number))

    parts = []
    for chunk_index in range(len(chunks) - 1, -1, -1):
        chunk = chunks[chunk_index]
        if chunk == 0:
            continue
        parts.extend(_words_under_1000(chunk))
        if chunk_index > 0:
            parts.append(_SCALES[chunk_index])
    return " ".join(parts)


def _digits_to_words(digits: str) -> str:
    """Read a run of digit characters one by one.

    Args:
        digits: A string of ASCII digit characters (``"0"``-``"9"``).

    Returns:
        The digits spoken individually, e.g. ``"90"`` -> ``"nine zero"``.

    Raises:
        TypeError: If *digits* is not a ``str``.
        ValueError: If *digits* contains a non-``0``-``9`` character.
    """
    ensure_digits(digits, "digits")
    return " ".join(_DIGIT_WORDS[digit] for digit in digits)


def _cardinal_from_digits(digit_string: str) -> str:
    """Read a run of digits as a cardinal number.

    Falls back to reading the digits one by one when the run is longer than the
    largest named scale. That also sidesteps CPython's int/str length cap, so
    an oversized numeric token is read rather than raising ``ValueError``.

    Args:
        digit_string: Digit characters only, no separators; ``""`` means zero.

    Returns:
        The cardinal reading, e.g. ``"221"`` -> ``"two hundred twenty one"``.

    Raises:
        TypeError: If *digit_string* is not a ``str``.
        ValueError: If *digit_string* contains a non-``0``-``9`` character.
    """
    ensure_digits(digit_string, "digit_string")
    if len(digit_string) > len(_SCALES) * 3:
        return _digits_to_words(digit_string)
    return int_to_cardinal(int(digit_string or "0"))


def _spell_identifier(ident: str) -> str:
    """Read an alphanumeric identifier: digits spoken singly, letters kept.

    Args:
        ident: An identifier that may mix digits and letters (and other
            characters, which are dropped), e.g. ``"4B"`` or ``"Apt 4B"``.

    Returns:
        The identifier read out, e.g. ``"4B"`` -> ``"four B"``, ``"200"`` ->
        ``"two zero zero"``. Only ASCII digits are spoken; other characters
        besides ASCII letters are dropped.

    Raises:
        TypeError: If *ident* is not a ``str``.
    """
    ensure_str(ident, "ident")
    tokens = []
    for part in re.findall(r"[0-9]+|[A-Za-z]+", ident):
        if part.isdigit():
            tokens.extend(_DIGIT_WORDS[digit] for digit in part)
        else:
            tokens.append(part)
    return " ".join(tokens)


def _pad(match: re.Match, words: str) -> str:
    """Pad a replacement with spaces when the numeric run abuts a letter.

    Args:
        match: The regex match for the numeric run being replaced.
        words: The spoken-word replacement text.

    Returns:
        *words* with a leading and/or trailing space added where the original
        run touched a letter, so ``"221B"`` becomes ``"... one B"`` not
        ``"... oneB"``.

    Raises:
        TypeError: If *match* is not a :class:`re.Match`, or *words* is not a
            ``str``.
    """
    ensure_match(match, "match")
    ensure_str(words, "words")
    source = match.string
    if match.start() > 0 and source[match.start() - 1].isalpha():
        words = " " + words
    if match.end() < len(source) and source[match.end()].isalpha():
        words = words + " "
    return words


def _say_cardinal(value: str) -> str:
    """Convert a (comma-grouped) integer string to cardinal words.

    Args:
        value: An integer as text, optionally with thousands separators, e.g.
            ``"1,000"``.

    Returns:
        The cardinal reading, e.g. ``"1,000"`` -> ``"one thousand"``.

    Raises:
        TypeError: If *value* is not a ``str``.
        ValueError: If *value* has no digit, or a non-digit, non-comma
            character.
    """
    ensure_has_digit(value, "value")
    return _cardinal_from_digits(value.replace(",", ""))


def _say_decimal(value: str) -> str:
    """Convert a decimal string to words, the fraction read digit by digit.

    Args:
        value: A number as text. With no decimal point it falls back to a
            cardinal reading.

    Returns:
        The reading, e.g. ``"3.14"`` -> ``"three point one four"``.

    Raises:
        TypeError: If *value* is not a ``str``.
        ValueError: If *value* has no digit, or a non-digit character other
            than a single decimal point and commas.
    """
    ensure_has_digit(value, "value")
    if "." not in value:
        return _say_cardinal(value)
    whole, fraction = value.split(".", 1)
    whole_words = _cardinal_from_digits(whole.replace(",", ""))
    fraction_words = _digits_to_words(fraction)
    return "%s point %s" % (whole_words, fraction_words)


def _say_currency(value: str) -> str:
    """Convert a currency value to words.

    Args:
        value: An amount, optionally led by a supported symbol (``$``, ``£``,
            ``€``); a symbol-less amount is treated as dollars.

    Returns:
        The money reading, e.g. ``"$19.99"`` -> ``"nineteen dollars and ninety
        nine cents"``.

    Raises:
        TypeError: If *value* is not a ``str``.
        ValueError: If *value* contains no digit.
    """
    ensure_has_digit(value, "value")
    value = value.strip()
    symbol = "$"
    if value[:1] in _CURRENCY:
        symbol = value[0]
        value = value[1:].strip()
    if "." in value:
        major, minor = value.split(".", 1)
    else:
        major, minor = value, ""
    major = re.sub(r"[^0-9]", "", major) or "0"
    minor = re.sub(r"[^0-9]", "", minor) if minor else None
    return _currency_words(symbol, major, minor)


def _currency_words(
    symbol: str, major_str: str, minor_str: str | None
) -> str:
    """Assemble the spoken form of a currency amount from its parts.

    Args:
        symbol: A key of :data:`_CURRENCY` selecting the unit names.
        major_str: The whole-unit amount as digits (optionally comma-grouped).
        minor_str: The fractional digits, or ``None`` when absent.

    Returns:
        The reading, with singular/plural units and an "and" joining the major
        and minor parts when both are present.

    Raises:
        TypeError: If *symbol* or *major_str* is not a ``str``, or *minor_str*
            is neither a ``str`` nor ``None``.
        ValueError: If *symbol* is not a supported currency symbol.
    """
    ensure_str(symbol, "symbol")
    ensure_str(major_str, "major_str")
    if minor_str is not None:
        ensure_str(minor_str, "minor_str")
    if symbol not in _CURRENCY:
        raise ValueError("symbol is not a known currency: %r" % symbol)
    # Strip separators and leading zeros so the major part is compared and read
    # without int(), which keeps oversized amounts from raising ValueError.
    major_digits = major_str.replace(",", "").lstrip("0") or "0"
    (major_sing, major_plur), (minor_sing, minor_plur) = _CURRENCY[symbol]

    parts = []
    if major_digits != "0" or not minor_str:
        unit = major_sing if major_digits == "1" else major_plur
        parts.append("%s %s" % (_cardinal_from_digits(major_digits), unit))

    if minor_str:
        # ".5" should mean 50 cents (half a dollar) per common convention,
        # not 5 cents, so pad to two digits before parsing.
        cents = int(minor_str.ljust(2, "0")[:2])
        if cents:
            unit = minor_sing if cents == 1 else minor_plur
            parts.append("%s %s" % (int_to_cardinal(cents), unit))

    return " and ".join(parts) if parts else "%s %s" % ("zero", major_plur)


def _say_phone(value: str) -> str:
    """Read a phone number digit by digit.

    Args:
        value: A phone number in any format; non-digits are ignored apart
            from a leading ``+``, which becomes "plus".

    Returns:
        The digits spoken individually, e.g. ``"555-1234"`` -> ``"five five
        five one two three four"``.

    Raises:
        TypeError: If *value* is not a ``str``.
        ValueError: If *value* contains no digit.
    """
    ensure_has_digit(value, "value")
    words = _digits_to_words(re.sub(r"[^0-9]", "", value))
    if value.lstrip().startswith("+"):
        words = "plus " + words
    return words


def _say_zip(value: str) -> str:
    """Read a postal code digit by digit.

    Args:
        value: A zip code, optionally ``ZIP+4`` with a hyphen.

    Returns:
        The digits spoken individually, e.g. ``"90210"`` -> ``"nine zero two
        one zero"``.

    Raises:
        TypeError: If *value* is not a ``str``.
        ValueError: If *value* contains no digit.
    """
    ensure_has_digit(value, "value")
    return _digits_to_words(re.sub(r"[^0-9]", "", value))


def _say_unit(value: str) -> str:
    """Read a secondary-address identifier (apartment, suite, box, ...).

    Args:
        value: An identifier, possibly alphanumeric and possibly including a
            designator label, e.g. ``"4B"`` or ``"Apt 4B"``.

    Returns:
        The identifier read out with digits spoken singly and letters kept,
        e.g. ``"Apt 4B"`` -> ``"Apt four B"``.

    Raises:
        TypeError: If *value* is not a ``str``.
        ValueError: If *value* contains no digit.
    """
    ensure_has_digit(value, "value")
    return _spell_identifier(value)


_CONVERTERS: Mapping[NumberType, Callable[[str], str]] = MappingProxyType({
    NumberType.CARDINAL: _say_cardinal,
    NumberType.DECIMAL: _say_decimal,
    NumberType.CURRENCY: _say_currency,
    NumberType.PHONE: _say_phone,
    NumberType.ZIP: _say_zip,
    NumberType.UNIT: _say_unit,
})


def _currency_repl(match: re.Match) -> str:
    """Replace a matched currency run (groups ``sym``/``major``/``minor``).

    Raises:
        TypeError: If *match* is not a :class:`re.Match`.
    """
    ensure_match(match, "match")
    return _pad(match, _currency_words(
        match.group("sym"), match.group("major"), match.group("minor")))


def _unit_repl(match: re.Match) -> str:
    """Replace a matched unit run (groups ``desig`` and ``id``).

    Raises:
        TypeError: If *match* is not a :class:`re.Match`.
    """
    ensure_match(match, "match")
    designator = match.group("desig").rstrip()
    identifier = _spell_identifier(match.group("id"))
    return _pad(match, "%s %s" % (designator, identifier))


def _zip_repl(match: re.Match) -> str:
    """Replace a matched zip-code run.

    Raises:
        TypeError: If *match* is not a :class:`re.Match`.
    """
    ensure_match(match, "match")
    return _pad(match, _say_zip(match.group(0)))


def _phone_repl(match: re.Match) -> str:
    """Replace a matched phone-number run.

    Raises:
        TypeError: If *match* is not a :class:`re.Match`.
    """
    ensure_match(match, "match")
    return _pad(match, _say_phone(match.group(0)))


def _decimal_repl(match: re.Match) -> str:
    """Replace a matched decimal run.

    Raises:
        TypeError: If *match* is not a :class:`re.Match`.
    """
    ensure_match(match, "match")
    return _pad(match, _say_decimal(match.group(0)))


def _integer_repl(match: re.Match) -> str:
    """Replace a matched integer run.

    Raises:
        TypeError: If *match* is not a :class:`re.Match`.
    """
    ensure_match(match, "match")
    return _pad(match, _say_cardinal(match.group(0)))


def _street_after_repl(match: re.Match) -> str:
    """Replace a matched ``<number> ... <street-designator>`` span.

    The number is read digit by digit; the optional intervening street name
    and the designator itself are preserved verbatim.

    Raises:
        TypeError: If *match* is not a :class:`re.Match`.
    """
    ensure_match(match, "match")
    number_words = _digits_to_words(match.group("number"))
    rest = match.group("rest")
    designator = match.group("designator")
    return _pad(match, "%s%s %s" % (number_words, rest, designator))


def _alphanum_repl(match: re.Match) -> str:
    """Replace a matched mixed alphanumeric token.

    The token is read out with digits spoken singly and letters preserved,
    via :func:`_spell_identifier`.

    Raises:
        TypeError: If *match* is not a :class:`re.Match`.
    """
    ensure_match(match, "match")
    return _pad(match, _spell_identifier(match.group(0)))


_CURRENCY_RE = re.compile(
    r"(?P<sym>[$£€])\s?"
    # Requiring a comma in the grouped form is what prevents a plain
    # 4+ digit number ("$1234") from matching only its 3-digit prefix.
    r"(?P<major>\d{1,3}(?:,\d{3})+|\d+)"
    r"(?:\.(?P<minor>\d{1,2}))?",
    # ASCII so Unicode/full-width digits don't reach the ASCII digit map.
    re.ASCII,
)

# Match a designator label plus an alphanumeric identifier (containing at
# least one digit). Reading those digits singly is what lets mixed forms
# like "4B" decompose cleanly into letters we keep and digits we spell.
# Route/Highway/Interstate are designators-before too: "Route 66" should
# read as identifier digits, matching how "Apt 5" and "Box 88" already do.
_UNIT_RE = re.compile(
    r"(?P<desig>#|\b(?:apartment|apt|unit|suite|ste|building|bldg|floor|fl|"
    r"room|rm|lot|space|spc|dept|trailer|trlr|box|number|no|route|hwy|"
    r"highway|interstate)\b\.?)\s*"
    r"(?P<id>[0-9A-Za-z]*[0-9][0-9A-Za-z]*)",
    re.IGNORECASE | re.ASCII,
)

# Street designators that follow the number in an address ("221 Baker St").
# A house number sitting in front of one of these reads digit by digit,
# because that's how people actually say addresses — "two-two-one Baker
# Street," never "two hundred twenty-one Baker Street."
_STREET_DESIGNATORS = (
    "st", "street", "ave", "avenue", "rd", "road",
    "blvd", "boulevard", "ln", "lane", "way",
    "ct", "court", "pl", "place", "dr", "drive",
    "cir", "circle", "pkwy", "parkway", "hwy", "highway",
    "trl", "trail", "aly", "alley", "sq", "square",
    "ter", "terrace", "fwy", "freeway", "tpke", "turnpike",
)

# Match a pure-digit token followed by 0-3 word tokens and then a street
# designator. The 0-3 window is what lets "221 Baker St" and "221 N Main
# St" both trigger without false-positive on prose like "He read 5 books
# yesterday at the Way" (which would need more than 3 intervening words).
_STREET_AFTER_RE = re.compile(
    r"\b(?P<number>\d+)"
    r"(?P<rest>(?:[\s.,]+[A-Za-z][A-Za-z.]*){0,3})"
    r"[\s.,]+(?P<designator>(?:"
    + r"|".join(_STREET_DESIGNATORS)
    + r"))\b\.?",
    re.IGNORECASE | re.ASCII,
)

# Mixed alphanumeric token (at least one digit, at least one letter, no
# internal whitespace). Reading the digits singly while keeping the letters
# is how people speak alphanumeric identifiers like "221B" or "4G".
_ALPHANUM_RE = re.compile(
    r"\b"
    r"(?=[0-9A-Za-z]*[0-9])(?=[0-9A-Za-z]*[A-Za-z])"
    r"[0-9A-Za-z]+"
    r"\b",
    re.ASCII,
)

# Isolated five-digit run (or zip+4). Anchoring with lookarounds is what
# prevents grabbing a five-digit slice out of a longer numeric token.
_ZIP_RE = re.compile(r"(?<!\d)\d{5}(?:-\d{4})?(?!\d)", re.ASCII)

# Detect phones by shape (separators / parens / leading +), not by digit
# count, so a plain large integer such as 1000000 is still read as a
# cardinal rather than mistaken for a phone number. Each alternative covers
# a NANP/international form commonly seen in user-supplied data; the verbose
# labels are kept so the pattern stays scannable as it grows.
_PHONE_RE = re.compile(
    r"""
    (?<![\w])(?:
        \+\d[\d\s().\-]{5,}\d                  # international: + then digits
      | \(?\d{3}\)?[\s.\-]\d{3}[\s.\-]\d{4}    # 10-digit, (555) 123-4567
      | (?<!\d)\d{3}[\s.\-]\d{4}(?!\d)         # 7-digit local, 555-1234
    )(?![\w])
    """,
    re.VERBOSE | re.ASCII,
)

_DECIMAL_RE = re.compile(r"(?<!\d)(\d+)\.(\d+)(?!\d)", re.ASCII)
_INTEGER_RE = re.compile(r"\d[\d,]*\d|\d", re.ASCII)

_VALUE_ZIP_RE = re.compile(r"\d{5}(?:-\d{4})?", re.ASCII)
_VALUE_DECIMAL_RE = re.compile(r"\d+\.\d+", re.ASCII)
_VALUE_PHONE_RE = re.compile(r"\+?[\d().\-\s]*\d[\d().\-\s]*", re.ASCII)


def _looks_like_phone(value: str) -> bool:
    """Report whether a value has the shape of a phone number.

    Args:
        value: The candidate field value.

    Returns:
        ``True`` if *value* is digits and phone separators only, has at least
        seven digits, and carries a separator or leading ``+``.

    Raises:
        TypeError: If *value* is not a ``str``.
    """
    ensure_str(value, "value")
    if not _VALUE_PHONE_RE.fullmatch(value):
        return False
    digits = re.sub(r"[^0-9]", "", value)
    return len(digits) >= 7 and bool(re.search(r"[().\-\s]|^\+", value))


def classify(value: str) -> NumberType:
    """Best-guess the :class:`NumberType` of a single field value.

    Precedence is currency, zip, phone, decimal, unit, then cardinal. Bare
    digit runs default to ``CARDINAL``; an isolated five-digit run is read as a
    ``ZIP`` and a mixed alphanumeric token (``"4B"``) as a ``UNIT``.

    Args:
        value: The field value to classify, e.g. ``"4B"`` or ``"$19.99"``.

    Returns:
        The best-guess :class:`NumberType`.

    Raises:
        TypeError: If *value* is not a ``str``.
        ValueError: If *value* contains no ASCII digit, so there is nothing to
            classify.
    """
    ensure_has_digit(value, "value")
    stripped = value.strip()
    if stripped[:1] in _CURRENCY:
        return NumberType.CURRENCY
    if _VALUE_ZIP_RE.fullmatch(stripped):
        return NumberType.ZIP
    if _looks_like_phone(stripped):
        return NumberType.PHONE
    if _VALUE_DECIMAL_RE.fullmatch(stripped):
        return NumberType.DECIMAL
    if any(char.isalpha() for char in stripped):
        return NumberType.UNIT
    return NumberType.CARDINAL


def number_to_words(value: str, kind: NumberType | None = None) -> str:
    """Convert a single numeric field *value* to words.

    If *kind* is ``None`` the type is guessed with :func:`classify`; otherwise
    the supplied :class:`NumberType` is used directly. Useful when the caller
    already knows the field's type (e.g. a zip-code column)::

        number_to_words("90210", NumberType.ZIP)  # 'nine zero two one zero'
        number_to_words("90210")                  # same, via classify()

    Args:
        value: The field value to convert. Must contain at least one digit.
        kind: The :class:`NumberType` to use, or ``None`` to classify *value*.

    Returns:
        The value read out as words.

    Raises:
        TypeError: If *value* is not a ``str``, or *kind* is neither a
            :class:`NumberType` nor ``None``.
        ValueError: If *value* contains no digit (nothing to convert).
    """
    ensure_str(value, "value")
    if kind is None:
        # classify() enforces the has-digit check, so we don't repeat it
        # here in the auto-detect path.
        kind = classify(value)
    else:
        if not isinstance(kind, NumberType):
            raise TypeError(
                "kind must be a NumberType or None, got %r" % (kind,)
            )
        ensure_has_digit(value, "value")
    return _CONVERTERS[kind](value)


_TOKEN_EDGE_RE = re.compile(r"^([^0-9A-Za-z$£€+]*)(.*?)([^0-9A-Za-z$£€+]*)$")


def _force_token(token: str, kind: NumberType) -> str:
    """Convert one whitespace-delimited token under a forced number type.

    Leading and trailing punctuation is split off and re-attached so it is
    preserved around the spoken form.

    Args:
        token: A single non-whitespace token from the input text.
        kind: The :class:`NumberType` to apply.

    Returns:
        The token unchanged if it carries no digit, otherwise its spoken form
        with the original surrounding punctuation restored.

    Raises:
        TypeError: If *token* is not a ``str``, or *kind* is not a
            :class:`NumberType`.
    """
    ensure_str(token, "token")
    if not isinstance(kind, NumberType):
        raise TypeError("kind must be a NumberType, got %r" % (kind,))
    prefix, core, suffix = _TOKEN_EDGE_RE.match(token).groups()
    if not any(char in _DIGIT_CHARS for char in core):
        return token
    return prefix + number_to_words(core, kind) + suffix


def numbers_to_words(text: str, kind: NumberType | None = None) -> str:
    """Replace every numeric run in *text* with its spoken-word equivalent.

    Letters and other characters are left untouched, so ``"221B Baker St"``
    becomes ``"two hundred twenty one B Baker St"``. The result contains no
    digits and is therefore safe to pass to :func:`py_mra.match_rating_codex`.

    With ``kind=None`` each numeric run is auto-detected. Pass a
    :class:`NumberType` to force every digit-bearing token to that type instead
    (each whitespace-delimited token is converted with :func:`number_to_words`,
    leading/trailing punctuation preserved).

    Args:
        text: The free text to scan.
        kind: ``None`` to auto-detect each run, or a :class:`NumberType` to
            force every digit-bearing token to that type.

    Returns:
        *text* with numeric runs replaced by words; tokens with no digits are
        left untouched.

    Raises:
        TypeError: If *text* is not a ``str``, or *kind* is neither a
            :class:`NumberType` nor ``None``.
    """
    ensure_str(text, "text")
    if kind is not None:
        if not isinstance(kind, NumberType):
            raise TypeError(
                "kind must be a NumberType or None, got %r" % (kind,)
            )
        return re.sub(
            r"\S+", lambda match: _force_token(match.group(0), kind), text
        )

    text = _CURRENCY_RE.sub(_currency_repl, text)
    text = _UNIT_RE.sub(_unit_repl, text)
    text = _PHONE_RE.sub(_phone_repl, text)
    text = _ZIP_RE.sub(_zip_repl, text)
    text = _STREET_AFTER_RE.sub(_street_after_repl, text)
    text = _DECIMAL_RE.sub(_decimal_repl, text)
    text = _ALPHANUM_RE.sub(_alphanum_repl, text)
    text = _INTEGER_RE.sub(_integer_repl, text)
    return text
