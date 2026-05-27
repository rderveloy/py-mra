import pytest

from py_mra import int_to_cardinal, numbers_to_words


@pytest.mark.parametrize(
    "n, expected",
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
def test_int_to_cardinal(n, expected):
    assert int_to_cardinal(n) == expected


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
