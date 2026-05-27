import pytest

from py_mra import (
    NumberType,
    classify,
    int_to_cardinal,
    number_to_words,
    numbers_to_words,
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
        (1234567, "one million two hundred thirty four thousand five hundred sixty seven"),
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
    assert numbers_to_words("$19.99") == "nineteen dollars and ninety nine cents"


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
    assert numbers_to_words("+1 555 123 4567").startswith("plus one five five five")


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
    # An unlabeled leading number is a quantity, read as a cardinal.
    assert numbers_to_words("221 Baker Street") == "two hundred twenty one Baker Street"


def test_full_address_line():
    addr = "221B Baker St Apt 5, London SW1A 1AA"
    out = numbers_to_words(addr)
    assert "two hundred twenty one B" in out  # house number (cardinal) + unit letter
    assert "Apt five" in out  # apartment identifier digit-by-digit
    assert not any(ch.isdigit() for ch in out)  # safe to encode


def test_designator_requires_a_number():
    # "no" without a following number must not be treated as a designator.
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
        ("12345", NumberType.CARDINAL, "twelve thousand three hundred forty five"),
        ("12", NumberType.UNIT, "one two"),
        ("5", NumberType.CURRENCY, "five dollars"),  # symbol-less defaults to dollars
        ("3.5", NumberType.CURRENCY, "three dollars and fifty cents"),
        ("66", NumberType.DECIMAL, "sixty six"),  # no dot -> falls back to cardinal
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
    # Both numbers forced to zip-style digit-by-digit.
    assert numbers_to_words("code 90210 ref 77", NumberType.ZIP) == (
        "code nine zero two one zero ref seven seven"
    )


def test_scanner_kind_override_preserves_punctuation():
    assert numbers_to_words("66.", NumberType.CARDINAL) == "sixty six."


def test_scanner_kind_override_skips_non_numeric_tokens():
    assert numbers_to_words("Lucky 7 today", NumberType.CARDINAL) == "Lucky seven today"


def test_scanner_rejects_bad_kind():
    with pytest.raises(TypeError):
        numbers_to_words("5", "cardinal")


# --- input validation --------------------------------------------------------

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
    # An explicit kind still must not be handed a value with no digit.
    with pytest.raises(ValueError):
        number_to_words("abc", NumberType.CURRENCY)
