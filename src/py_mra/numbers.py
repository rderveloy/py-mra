"""Convert numeric runs in text into spoken words.

The Match Rating Approach encoder refuses numeric input. This module is the
explicit opt-in path for callers who want numbers expanded into words before
encoding. :func:`numbers_to_words` scans a string and replaces each numeric run
with words, choosing a style based on context:

* currency  -- ``"$19.99"`` -> ``"nineteen dollars and ninety nine cents"``
* phone     -- ``"555-1234"`` -> ``"five five five one two three four"``
* decimal   -- ``"3.14"`` -> ``"three point one four"``
* integer   -- ``"66"`` -> ``"sixty six"`` (cardinal)

Output is space-separated with no hyphens, so it flows cleanly into the encoder.
The phone and currency heuristics are intentionally simple and documented here
so they can be tuned for a given dataset.
"""

import re

_ONES = [
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
    "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
    "sixteen", "seventeen", "eighteen", "nineteen",
]
_TENS = [
    "", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
    "eighty", "ninety",
]
_SCALES = ["", "thousand", "million", "billion", "trillion", "quadrillion", "quintillion"]

_DIGIT_WORDS = {str(i): _ONES[i] for i in range(10)}

# Currency symbol -> (major unit singular/plural, minor unit singular/plural).
_CURRENCY = {
    "$": (("dollar", "dollars"), ("cent", "cents")),
    "£": (("pound", "pounds"), ("penny", "pence")),  # GBP
    "€": (("euro", "euros"), ("cent", "cents")),     # EUR
}


def _words_under_1000(n):
    """Words for 1..999 (n must be > 0), as a list of tokens."""
    words = []
    if n >= 100:
        words.append(_ONES[n // 100])
        words.append("hundred")
        n %= 100
    if n >= 20:
        words.append(_TENS[n // 10])
        n %= 10
        if n:
            words.append(_ONES[n])
    elif n > 0:
        words.append(_ONES[n])
    return words


def int_to_cardinal(n):
    """Render a non-negative integer as cardinal words (American style, no 'and')."""
    if n < 0:
        return "negative " + int_to_cardinal(-n)
    if n == 0:
        return "zero"

    chunks = []
    while n > 0:
        chunks.append(n % 1000)
        n //= 1000

    if len(chunks) > len(_SCALES):
        # Absurdly large; fall back to reading the digits one by one.
        return " ".join(_DIGIT_WORDS[d] for d in str(n))

    parts = []
    for i in range(len(chunks) - 1, -1, -1):
        chunk = chunks[i]
        if chunk == 0:
            continue
        parts.extend(_words_under_1000(chunk))
        if i > 0:
            parts.append(_SCALES[i])
    return " ".join(parts)


def _digits_to_words(digits):
    return " ".join(_DIGIT_WORDS[d] for d in digits)


def _pad(match, words):
    """Add a separating space when the numeric run abuts a letter (``221B``)."""
    s = match.string
    if match.start() > 0 and s[match.start() - 1].isalpha():
        words = " " + words
    if match.end() < len(s) and s[match.end()].isalpha():
        words = words + " "
    return words


def _currency_repl(match):
    symbol = match.group("sym")
    dollars = int(match.group("major").replace(",", ""))
    cents_str = match.group("minor")
    (major_sing, major_plur), (minor_sing, minor_plur) = _CURRENCY[symbol]

    parts = []
    if dollars or not cents_str:
        unit = major_sing if dollars == 1 else major_plur
        parts.append("%s %s" % (int_to_cardinal(dollars), unit))

    if cents_str:
        cents = int(cents_str.ljust(2, "0")[:2])  # ".5" -> 50, ".05" -> 5
        if cents:
            unit = minor_sing if cents == 1 else minor_plur
            cents_words = "%s %s" % (int_to_cardinal(cents), unit)
            parts.append(cents_words)

    words = " and ".join(parts) if parts else "%s %s" % ("zero", major_plur)
    return _pad(match, words)


def _phone_repl(match):
    text = match.group(0)
    digits = re.sub(r"\D", "", text)
    words = _digits_to_words(digits)
    if text.lstrip().startswith("+"):
        words = "plus " + words
    return _pad(match, words)


def _decimal_repl(match):
    whole = int(match.group(1))
    frac = match.group(2)
    words = "%s point %s" % (int_to_cardinal(whole), _digits_to_words(frac))
    return _pad(match, words)


def _integer_repl(match):
    return _pad(match, int_to_cardinal(int(match.group(0).replace(",", ""))))


# Currency: a supported symbol, optional space, a (comma-grouped) amount, and
# an optional fractional part.
_CURRENCY_RE = re.compile(
    r"(?P<sym>[$£€])\s?(?P<major>\d{1,3}(?:,\d{3})*|\d+)(?:\.(?P<minor>\d{1,2}))?"
)

# Phone numbers, detected by shape rather than digit count so that genuine
# large integers (e.g. 1000000) are still read as cardinals.
_PHONE_RE = re.compile(
    r"""
    (?<![\w])(?:
        \+\d[\d\s().\-]{5,}\d                      # international: + then separated digits
      | \(?\d{3}\)?[\s.\-]\d{3}[\s.\-]\d{4}        # 10-digit, e.g. (555) 123-4567
      | (?<!\d)\d{3}[\s.\-]\d{4}(?!\d)             # 7-digit local, e.g. 555-1234
    )(?![\w])
    """,
    re.VERBOSE,
)

_DECIMAL_RE = re.compile(r"(?<!\d)(\d+)\.(\d+)(?!\d)")
_INTEGER_RE = re.compile(r"\d[\d,]*\d|\d")


def numbers_to_words(text):
    """Replace every numeric run in *text* with its spoken-word equivalent.

    Letters and other characters are left untouched, so ``"221B Baker St"``
    becomes ``"two hundred twenty one B Baker St"``. The result contains no
    digits and is therefore safe to pass to :func:`py_mra.match_rating_codex`.
    """
    text = _CURRENCY_RE.sub(_currency_repl, text)
    text = _PHONE_RE.sub(_phone_repl, text)
    text = _DECIMAL_RE.sub(_decimal_repl, text)
    text = _INTEGER_RE.sub(_integer_repl, text)
    return text
