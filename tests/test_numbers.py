import pytest

from py_mra import (
    NumberType,
    classify,
    int_to_cardinal,
    number_to_words,
    numbers_to_words,
)
from py_mra.numbers import (
    _CURRENCY,
    _CONVERTERS,
    _DIGIT_WORDS,
    _SCALES,
    _currency_words,
    _force_token,
    _words_under_1000,
)


@pytest.mark.parametrize(
    "number, expected",
    [
        (0, "zero"),
        (7, "seven"),
        (13, "thirteen"),
        (20, "twenty"),
        (21, "twenty one"),
        (100, "one hundred"),
        (221, "two hundred twenty one"),
        (1000, "one thousand"),
        (1000000, "one million"),
        (
            1234567,
            "one million two hundred thirty four thousand "
            "five hundred sixty seven",
        ),
    ],
)
def test_int_to_cardinal(number, expected):
    assert int_to_cardinal(number) == expected


def test_plain_integer_is_cardinal():
    assert numbers_to_words("Route 66") == "Route sixty six"


def test_thousands_separator():
    assert numbers_to_words("pop 1,000,000") == "pop one million"


def test_decimal():
    assert numbers_to_words("pi is 3.14") == "pi is three point one four"


def test_currency_dollars_and_cents():
    assert numbers_to_words("$19.99") == (
        "nineteen dollars and ninety nine cents"
    )


def test_currency_singular():
    assert numbers_to_words("$1") == "one dollar"


def test_currency_cents_only():
    assert numbers_to_words("$0.50") == "fifty cents"


def test_currency_pounds():
    assert numbers_to_words("£5") == "five pounds"


@pytest.mark.parametrize(
    "phone, expected",
    [
        ("555-1234", "five five five one two three four"),
        ("(555) 123-4567", "five five five one two three four five six seven"),
    ],
)
def test_phone_digit_by_digit(phone, expected):
    assert numbers_to_words(phone) == expected


def test_international_phone_prefixes_plus():
    spoken = numbers_to_words("+1 555 123 4567")
    assert spoken.startswith("plus one five five five")


def test_letters_preserved_around_numbers():
    assert numbers_to_words("221B") == "two hundred twenty one B"


def test_no_numbers_passthrough():
    assert numbers_to_words("Hello World") == "Hello World"


@pytest.mark.parametrize(
    "address, expected",
    [
        ("90210", "nine zero two one zero"),
        ("90210-1234", "nine zero two one zero one two three four"),
        ("Springfield IL 62704", "Springfield IL six two seven zero four"),
    ],
)
def test_zip_codes_digit_by_digit(address, expected):
    assert numbers_to_words(address) == expected


@pytest.mark.parametrize(
    "field, expected",
    [
        ("Apt 4B", "Apt four B"),
        ("Apartment 12", "Apartment one two"),
        ("Unit 200", "Unit two zero zero"),
        ("Suite 100", "Suite one zero zero"),
        ("Ste 5", "Ste five"),
        ("Floor 3", "Floor three"),
        ("Bldg 7C", "Bldg seven C"),
        ("PO Box 88", "PO Box eight eight"),
        ("# 3", "# three"),
    ],
)
def test_unit_designators_digit_by_digit(field, expected):
    assert numbers_to_words(field) == expected


def test_house_number_stays_cardinal():
    # Without a designator label, the leading number is a quantity (house
    # number), not an identifier; cardinal preserves that distinction.
    assert numbers_to_words("221 Baker Street") == (
        "two hundred twenty one Baker Street"
    )


def test_full_address_line():
    # Real address lines mix several conventions in one string; the scanner
    # must apply the right rule to each run rather than blanket-converting.
    address = "221B Baker St Apt 5, London SW1A 1AA"
    spoken = numbers_to_words(address)
    assert "two hundred twenty one B" in spoken
    assert "Apt five" in spoken
    # Digit-free output is the whole point — it's the encoder's prerequisite.
    assert not any(char.isdigit() for char in spoken)


def test_designator_requires_a_number():
    # "no" appears in plain English; matching it as a designator without a
    # following identifier would mangle ordinary text.
    assert numbers_to_words("no thanks") == "no thanks"


@pytest.mark.parametrize(
    "value, kind",
    [
        ("66", NumberType.CARDINAL),
        ("1,000", NumberType.CARDINAL),
        ("3.14", NumberType.DECIMAL),
        ("$19.99", NumberType.CURRENCY),
        ("€5", NumberType.CURRENCY),
        ("555-1234", NumberType.PHONE),
        ("(555) 123-4567", NumberType.PHONE),
        ("+1 555 123 4567", NumberType.PHONE),
        ("90210", NumberType.ZIP),
        ("90210-1234", NumberType.ZIP),
        ("4B", NumberType.UNIT),
        ("Apt 4B", NumberType.UNIT),
    ],
)
def test_classify(value, kind):
    assert classify(value) is kind


def test_number_to_words_uses_classify_when_no_kind():
    assert number_to_words("90210") == "nine zero two one zero"
    assert number_to_words("66") == "sixty six"


@pytest.mark.parametrize(
    "value, kind, expected",
    [
        ("12345", NumberType.ZIP, "one two three four five"),
        (
            "12345",
            NumberType.CARDINAL,
            "twelve thousand three hundred forty five",
        ),
        ("12", NumberType.UNIT, "one two"),
        # Pins the documented default: an unmarked currency value is dollars,
        # which is the only sensible choice without locale context.
        ("5", NumberType.CURRENCY, "five dollars"),
        ("3.5", NumberType.CURRENCY, "three dollars and fifty cents"),
        # Forced DECIMAL with no decimal point falls back to cardinal so
        # mis-classified inputs still produce a sensible reading.
        ("66", NumberType.DECIMAL, "sixty six"),
    ],
)
def test_number_to_words_explicit_kind(value, kind, expected):
    assert number_to_words(value, kind) == expected


def test_number_to_words_rejects_bad_kind():
    with pytest.raises(TypeError):
        number_to_words("5", "zip")


def test_classify_rejects_non_string():
    with pytest.raises(TypeError):
        classify(5)


def test_scanner_kind_override_forces_type():
    # An explicit kind must override the heuristic for *every* digit token —
    # the second number would otherwise be auto-detected as a cardinal.
    assert numbers_to_words("code 90210 ref 77", NumberType.ZIP) == (
        "code nine zero two one zero ref seven seven"
    )


def test_scanner_kind_override_preserves_punctuation():
    assert numbers_to_words("66.", NumberType.CARDINAL) == "sixty six."


def test_scanner_kind_override_skips_non_numeric_tokens():
    assert numbers_to_words("Lucky 7 today", NumberType.CARDINAL) == (
        "Lucky seven today"
    )


def test_scanner_rejects_bad_kind():
    with pytest.raises(TypeError):
        numbers_to_words("5", "cardinal")


@pytest.mark.parametrize("bad", ["5", None, b"5", 3.0])
def test_int_to_cardinal_rejects_non_int(bad):
    with pytest.raises(TypeError):
        int_to_cardinal(bad)


def test_int_to_cardinal_rejects_bool():
    with pytest.raises(TypeError):
        int_to_cardinal(True)


def test_numbers_to_words_rejects_non_string():
    with pytest.raises(TypeError):
        numbers_to_words(123)


@pytest.mark.parametrize("bad", [123, None, ["5"]])
def test_classify_rejects_non_string_types(bad):
    with pytest.raises(TypeError):
        classify(bad)


@pytest.mark.parametrize("value", ["", "abc", "   ", "no digits here"])
def test_classify_requires_a_digit(value):
    with pytest.raises(ValueError):
        classify(value)


def test_number_to_words_rejects_non_string():
    with pytest.raises(TypeError):
        number_to_words(90210)


def test_number_to_words_requires_a_digit_when_classifying():
    with pytest.raises(ValueError):
        number_to_words("abc")


def test_number_to_words_requires_a_digit_with_explicit_kind():
    # Supplying a kind doesn't bypass usability — without a digit there is
    # nothing to convert and the helper would silently emit nonsense.
    with pytest.raises(ValueError):
        number_to_words("abc", NumberType.CURRENCY)


@pytest.mark.parametrize(
    "number, expected",
    [
        (-5, "negative five"),
        (-1000, "negative one thousand"),
    ],
)
def test_int_to_cardinal_negative(number, expected):
    assert int_to_cardinal(number) == expected


def test_int_to_cardinal_beyond_largest_scale_reads_digits():
    # No name exists past "quintillion", so the fallback path reads digits
    # one by one; this exercises that branch (originally buggy).
    assert int_to_cardinal(10 ** 24) == " ".join(["one"] + ["zero"] * 24)


def test_oversized_token_reads_digit_by_digit_without_raising():
    # CPython caps int<->str at 4300 digits; oversized tokens used to leak
    # that raw ValueError, so this pins the safe digit-by-digit fallback.
    token = "9" * 4400
    assert numbers_to_words(token) == " ".join(["nine"] * 4400)


def test_oversized_value_with_explicit_cardinal_kind():
    token = "9" * 4400
    assert number_to_words(token, NumberType.CARDINAL) == (
        " ".join(["nine"] * 4400)
    )


def test_oversized_currency_reads_amount_digit_by_digit():
    spoken = numbers_to_words("$" + "9" * 25)
    assert spoken == " ".join(["nine"] * 25) + " dollars"


@pytest.mark.parametrize(
    "value, expected",
    [
        ("$1234", "one thousand two hundred thirty four dollars"),
        ("$50000", "fifty thousand dollars"),
        (
            "$1,234,567",
            "one million two hundred thirty four thousand "
            "five hundred sixty seven dollars",
        ),
        (
            "$1234.56",
            "one thousand two hundred thirty four dollars "
            "and fifty six cents",
        ),
    ],
)
def test_currency_multi_digit_amounts(value, expected):
    assert numbers_to_words(value) == expected


def test_currency_zero_cents_drops_the_cents():
    assert numbers_to_words("$5.00") == "five dollars"


def test_currency_zero_dollars_and_zero_cents():
    assert numbers_to_words("$0.00") == "zero dollars"


@pytest.mark.parametrize(
    "value, expected",
    [
        ("$5", "five dollars"),
        ("€5", "five euros"),
        ("£5", "five pounds"),
    ],
)
def test_number_to_words_currency_strips_symbol(value, expected):
    assert number_to_words(value, NumberType.CURRENCY) == expected


def test_fullwidth_digits_are_treated_as_non_numeric():
    # Limiting "digit" to ASCII keeps the digit-by-digit map consistent and
    # prevents Unicode digits from reaching it (which would crash); the
    # tradeoff is that they pass through as plain text.
    with pytest.raises(ValueError):
        classify("９０２１０")
    assert numbers_to_words("Apt ９") == "Apt ９"


def test_injection_like_text_without_digits_passes_through():
    # The scanner does pattern replacement, not interpretation, so an
    # injection-shaped payload without digits must be returned untouched —
    # no execution, no escaping, no mutation.
    payload = "'; DROP TABLE users; --"
    assert numbers_to_words(payload) == payload


@pytest.mark.parametrize("bad", [0, 1000, -1])
def test_words_under_1000_rejects_out_of_range(bad):
    with pytest.raises(ValueError):
        _words_under_1000(bad)


def test_currency_words_rejects_unknown_symbol():
    with pytest.raises(ValueError):
        _currency_words("¥", "5", None)


def test_force_token_rejects_non_number_type_kind():
    with pytest.raises(TypeError):
        _force_token("5", "cardinal")


@pytest.mark.parametrize("table", [_CURRENCY, _CONVERTERS, _DIGIT_WORDS])
def test_mapping_lookup_tables_are_read_only(table):
    # A caller reaching into module internals must not be able to corrupt the
    # shared lookup tables — every subsequent conversion would silently use
    # the poisoned entry. MappingProxyType makes that impossible at the
    # boundary rather than relying on convention.
    with pytest.raises(TypeError):
        table["nope"] = "anything"


def test_scale_table_is_immutable():
    # Tuple semantics rule out resize/replace-by-index mistakes that a list
    # would silently allow.
    with pytest.raises(TypeError):
        _SCALES[0] = "broken"
