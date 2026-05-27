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
from collections.abc import Callable
from enum import Enum


class NumberType(Enum):
    """The kind of number a value represents, used to pick a verbalization."""

    CARDINAL = "cardinal"   # a quantity: "66" -> "sixty six"
    DECIMAL = "decimal"     # "3.14" -> "three point one four"
    CURRENCY = "currency"   # "$19.99" -> "nineteen dollars and ..."
    PHONE = "phone"         # "555-1234" -> "five five five one two three four"
    ZIP = "zip"             # "90210" -> "nine zero two one zero"
    UNIT = "unit"           # an identifier: "4B" -> "four B"


_ONES = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen",
]
_TENS = [
    "", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
    "eighty", "ninety",
]
_SCALES = [
    "", "thousand", "million", "billion", "trillion", "quadrillion",
    "quintillion",
]

_DIGIT_WORDS = {str(digit): _ONES[digit] for digit in range(10)}

# Currency symbol -> (major unit singular/plural, minor unit singular/plural).
_CURRENCY = {
    "$": (("dollar", "dollars"), ("cent", "cents")),
    "£": (("pound", "pounds"), ("penny", "pence")),  # GBP
    "€": (("euro", "euros"), ("cent", "cents")),     # EUR
}


def _words_under_1000(number: int) -> list[str]:
    """Return the word tokens for an integer in 1..999.

    Args:
        number: An integer strictly between 0 and 1000.

    Returns:
        A list of word tokens, e.g. ``221`` -> ``["two", "hundred", "twenty",
        "one"]``.
    """
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
        ``"negative five"``.

    Raises:
        TypeError: If *number* is not an ``int`` (``bool`` is rejected).
    """
    if isinstance(number, bool) or not isinstance(number, int):
        raise TypeError(
            "number must be an int, got %r" % type(number).__name__
        )
    if number < 0:
        return "negative " + int_to_cardinal(-number)
    if number == 0:
        return "zero"

    chunks = []
    while number > 0:
        chunks.append(number % 1000)
        number //= 1000

    if len(chunks) > len(_SCALES):
        # Absurdly large; fall back to reading the digits one by one.
        return " ".join(_DIGIT_WORDS[digit] for digit in str(number))

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
    """
    return " ".join(_DIGIT_WORDS[digit] for digit in digits)


def _spell_identifier(ident: str) -> str:
    """Read an alphanumeric identifier: digits spoken singly, letters kept.

    Args:
        ident: An identifier that may mix digits and letters (and other
            characters, which are dropped), e.g. ``"4B"`` or ``"Apt 4B"``.

    Returns:
        The identifier read out, e.g. ``"4B"`` -> ``"four B"``, ``"200"`` ->
        ``"two zero zero"``.
    """
    tokens = []
    for part in re.findall(r"\d+|[A-Za-z]+", ident):
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
    """
    source = match.string
    if match.start() > 0 and source[match.start() - 1].isalpha():
        words = " " + words
    if match.end() < len(source) and source[match.end()].isalpha():
        words = words + " "
    return words


# --- value-level converters: operate on a single numeric string -------------

def _say_cardinal(value: str) -> str:
    """Convert a (comma-grouped) integer string to cardinal words.

    Args:
        value: An integer as text, optionally with thousands separators, e.g.
            ``"1,000"``.

    Returns:
        The cardinal reading, e.g. ``"1,000"`` -> ``"one thousand"``.
    """
    return int_to_cardinal(int(value.replace(",", "")))


def _say_decimal(value: str) -> str:
    """Convert a decimal string to words, the fraction read digit by digit.

    Args:
        value: A number as text. With no decimal point it falls back to a
            cardinal reading.

    Returns:
        The reading, e.g. ``"3.14"`` -> ``"three point one four"``.
    """
    if "." not in value:
        return _say_cardinal(value)
    whole, fraction = value.split(".", 1)
    whole_words = int_to_cardinal(int(whole.replace(",", "") or "0"))
    fraction_words = _digits_to_words(re.sub(r"\D", "", fraction))
    return "%s point %s" % (whole_words, fraction_words)


def _say_currency(value: str) -> str:
    """Convert a currency value to words.

    Args:
        value: An amount, optionally led by a supported symbol (``$``, ``£``,
            ``€``); a symbol-less amount is treated as dollars.

    Returns:
        The money reading, e.g. ``"$19.99"`` -> ``"nineteen dollars and ninety
        nine cents"``.
    """
    value = value.strip()
    symbol = "$"
    if value[:1] in _CURRENCY:
        symbol = value[0]
        value = value[1:].strip()
    if "." in value:
        major, minor = value.split(".", 1)
    else:
        major, minor = value, ""
    major = re.sub(r"\D", "", major) or "0"
    minor = re.sub(r"\D", "", minor) if minor else None
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
    """
    dollars = int(major_str.replace(",", ""))
    (major_sing, major_plur), (minor_sing, minor_plur) = _CURRENCY[symbol]

    parts = []
    if dollars or not minor_str:
        unit = major_sing if dollars == 1 else major_plur
        parts.append("%s %s" % (int_to_cardinal(dollars), unit))

    if minor_str:
        cents = int(minor_str.ljust(2, "0")[:2])  # ".5" -> 50, ".05" -> 5
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
    """
    words = _digits_to_words(re.sub(r"\D", "", value))
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
    """
    return _digits_to_words(re.sub(r"\D", "", value))


def _say_unit(value: str) -> str:
    """Read a secondary-address identifier (apartment, suite, box, ...).

    Args:
        value: An identifier, possibly alphanumeric and possibly including a
            designator label, e.g. ``"4B"`` or ``"Apt 4B"``.

    Returns:
        The identifier read out with digits spoken singly and letters kept,
        e.g. ``"Apt 4B"`` -> ``"Apt four B"``.
    """
    return _spell_identifier(value)


_CONVERTERS: dict[NumberType, Callable[[str], str]] = {
    NumberType.CARDINAL: _say_cardinal,
    NumberType.DECIMAL: _say_decimal,
    NumberType.CURRENCY: _say_currency,
    NumberType.PHONE: _say_phone,
    NumberType.ZIP: _say_zip,
    NumberType.UNIT: _say_unit,
}


# --- scanner replacement callbacks (auto-detect path) ------------------------
# Each takes a regex match for a numeric run and returns the padded reading.

def _currency_repl(match: re.Match) -> str:
    """Replace a matched currency run (groups ``sym``/``major``/``minor``)."""
    return _pad(match, _currency_words(
        match.group("sym"), match.group("major"), match.group("minor")))


def _unit_repl(match: re.Match) -> str:
    """Replace a matched unit run (groups ``desig`` and ``id``)."""
    designator = match.group("desig").rstrip()
    identifier = _spell_identifier(match.group("id"))
    return _pad(match, "%s %s" % (designator, identifier))


def _zip_repl(match: re.Match) -> str:
    """Replace a matched zip-code run."""
    return _pad(match, _say_zip(match.group(0)))


def _phone_repl(match: re.Match) -> str:
    """Replace a matched phone-number run."""
    return _pad(match, _say_phone(match.group(0)))


def _decimal_repl(match: re.Match) -> str:
    """Replace a matched decimal run."""
    return _pad(match, _say_decimal(match.group(0)))


def _integer_repl(match: re.Match) -> str:
    """Replace a matched integer run."""
    return _pad(match, _say_cardinal(match.group(0)))


# Currency: a supported symbol, optional space, a (comma-grouped) amount, and
# an optional fractional part.
_CURRENCY_RE = re.compile(
    r"(?P<sym>[$£€])\s?"
    r"(?P<major>\d{1,3}(?:,\d{3})*|\d+)"
    r"(?:\.(?P<minor>\d{1,2}))?"
)

# Secondary-address designators (apartment, unit, suite, box, "#", ...)
# followed by an identifier with at least one digit. The identifier is read
# digit by digit so alphanumerics like "4B" decompose cleanly.
_UNIT_RE = re.compile(
    r"(?P<desig>#|\b(?:apartment|apt|unit|suite|ste|building|bldg|floor|fl|"
    r"room|rm|lot|space|spc|dept|trailer|trlr|box|number|no)\b\.?)\s*"
    r"(?P<id>[0-9A-Za-z]*[0-9][0-9A-Za-z]*)",
    re.IGNORECASE,
)

# US zip code: an isolated run of exactly five digits, optionally + four.
# Read digit by digit, as zip codes are always spoken.
_ZIP_RE = re.compile(r"(?<!\d)\d{5}(?:-\d{4})?(?!\d)")

# Phone numbers, detected by shape rather than digit count so that genuine
# large integers (e.g. 1000000) are still read as cardinals.
_PHONE_RE = re.compile(
    r"""
    (?<![\w])(?:
        \+\d[\d\s().\-]{5,}\d                  # international: + then digits
      | \(?\d{3}\)?[\s.\-]\d{3}[\s.\-]\d{4}    # 10-digit (555) 123-4567
      | (?<!\d)\d{3}[\s.\-]\d{4}(?!\d)         # 7-digit local 555-1234
    )(?![\w])
    """,
    re.VERBOSE,
)

_DECIMAL_RE = re.compile(r"(?<!\d)(\d+)\.(\d+)(?!\d)")
_INTEGER_RE = re.compile(r"\d[\d,]*\d|\d")


# --- classification of a single field value ----------------------------------

_VALUE_ZIP_RE = re.compile(r"\d{5}(?:-\d{4})?")
_VALUE_DECIMAL_RE = re.compile(r"\d+\.\d+")
_VALUE_PHONE_RE = re.compile(r"\+?[\d().\-\s]*\d[\d().\-\s]*")


def _looks_like_phone(value: str) -> bool:
    """Report whether a value has the shape of a phone number.

    Args:
        value: The candidate field value.

    Returns:
        ``True`` if *value* is digits and phone separators only, has at least
        seven digits, and carries a separator or leading ``+``.
    """
    if not _VALUE_PHONE_RE.fullmatch(value):
        return False
    digits = re.sub(r"\D", "", value)
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
        ValueError: If *value* contains no digit, so there is nothing to
            classify.
    """
    if not isinstance(value, str):
        raise TypeError("value must be a str, got %r" % type(value).__name__)

    stripped = value.strip()
    if not any(char.isdigit() for char in stripped):
        raise ValueError("value contains no digit to classify: %r" % value)
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
    if not isinstance(value, str):
        raise TypeError("value must be a str, got %r" % type(value).__name__)
    if kind is None:
        kind = classify(value)  # raises ValueError when there is no digit
    else:
        if not isinstance(kind, NumberType):
            raise TypeError(
                "kind must be a NumberType or None, got %r" % (kind,)
            )
        if not any(char.isdigit() for char in value):
            raise ValueError("value contains no digit to convert: %r" % value)
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
    """
    prefix, core, suffix = _TOKEN_EDGE_RE.match(token).groups()
    if not any(char.isdigit() for char in core):
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
    if not isinstance(text, str):
        raise TypeError("text must be a str, got %r" % type(text).__name__)
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
    text = _DECIMAL_RE.sub(_decimal_repl, text)
    text = _INTEGER_RE.sub(_integer_repl, text)
    return text
