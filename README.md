# py-mra

Python implementation of the **Match Rating Approach** (MRA) algorithm — a
phonetic algorithm developed by Western Airlines in 1977 for indexing and
comparing homophonous names.

MRA has two parts: an **encoder** that reduces a name to a short *codex*, and a
**comparison** that decides whether two names match by reducing their codices
and testing the result against a length-based minimum rating.

## Install

```bash
pip install -e .          # from a checkout
pip install -e ".[test]"  # with the test dependencies
```

Requires Python 3.8+. No runtime dependencies.

## Quick start

```python
from py_mra import match_rating_codex, match_rating_comparison

match_rating_codex("Smith")                 # 'SMTH'
match_rating_codex("Smyth")                 # 'SMYTH'

match_rating_comparison("Smith", "Smyth")   # True
match_rating_comparison("Catherine", "Kathryn")  # True
match_rating_comparison("Smith", "Johnson") # False
match_rating_comparison("Al", "Alexandria") # None  (incomparable lengths)
```

## API

| Function | Returns | Notes |
|----------|---------|-------|
| `match_rating_codex(name)` | `str` | The MRA codex for a name. |
| `match_rating_comparison(a, b)` | `bool` or `None` | `True`/`False` per the minimum-rating table; `None` if the codices' lengths differ by 3 or more. |
| `match_rating(a, b)` | `int` or `None` | The raw similarity rating (`6 - max_unmatched`), or `None` if incomparable. |
| `numbers_to_words(text, kind=None)` | `str` | Expands numeric runs in free text (see below). |
| `number_to_words(value, kind=None)` | `str` | Expands a single field value (see below). |
| `classify(value)` | `NumberType` | Best-guess the type of a single field value. |
| `int_to_cardinal(n)` | `str` | A non-negative `int` as cardinal words. |

Enums: `NumberType` (`CARDINAL`, `DECIMAL`, `CURRENCY`, `PHONE`, `ZIP`, `UNIT`).
Exceptions / warnings: `NumericInputError`, `SpecialCharacterWarning`.

Inputs are validated, not silently coerced. All functions raise `TypeError` for
wrong argument types (e.g. a non-`str` name, a `kind` that isn't a `NumberType`);
`classify` and `number_to_words` raise `ValueError` when given a value with no
digit; and `match_rating_codex` raises `NumericInputError` rather than dropping
digits. Each function's exact `Raises:` contract is in its docstring.

### Encoding rules

1. Reject any input containing numeric characters (raises `NumericInputError`).
2. Transliterate accented letters to ASCII — `match_rating_codex("José")` equals
   `match_rating_codex("Jose")`.
3. Strip remaining non-letters. Whitespace is removed silently; punctuation and
   symbols are removed with a `SpecialCharacterWarning`.
4. Uppercase, keep the first letter, delete subsequent vowels, and collapse
   adjacent duplicate letters.
5. If the result exceeds six letters, keep the first three and last three.

### Comparison rules

1. Encode both names.
2. If the codex lengths differ by 3 or more, the names are incomparable (`None`).
3. Derive the minimum rating from the sum of the lengths:

   | Length sum | Minimum rating |
   |-----------:|---------------:|
   | 1–4 | 5 |
   | 5–7 | 4 |
   | 8–11 | 3 |
   | 12 | 2 |

4. Remove characters that match position-for-position from the left, then from
   the right. The rating is `6 - max_unmatched`; the names match when the rating
   meets or exceeds the minimum.

## Numbers and address fields

The encoder is strict and **refuses any numeric input**, because digits have no
phonetic encoding. To handle names, addresses, or free text that contain
numbers, expand them first with `numbers_to_words`, then encode:

```python
from py_mra import numbers_to_words, match_rating_codex

text = numbers_to_words("221B Baker St, Apt 4")   # 'two hundred twenty one B Baker St, Apt four'
match_rating_codex(text)
```

`numbers_to_words` chooses a verbalization based on context. *Quantities* are
read as cardinals; *identifiers* (zip, apartment, unit, suite, box numbers) are
read digit by digit, since they are labels rather than amounts and are often
alphanumeric.

| Input | Output |
|-------|--------|
| `Route 66` | `Route sixty six` |
| `221 Baker Street` (house number) | `two hundred twenty one Baker Street` |
| `Apt 4B` / `Unit 12` / `Suite 200` | `Apt four B` / `Unit one two` / `Suite two zero zero` |
| `PO Box 88` / `# 3` | `PO Box eight eight` / `# three` |
| `90210-1234` (zip+4) | `nine zero two one zero one two three four` |
| `(555) 123-4567` (phone) | `five five five one two three four five six seven` |
| `$19.99` (currency) | `nineteen dollars and ninety nine cents` |
| `3.14` (decimal) | `three point one four` |

The phone, zip, and unit heuristics are detected by shape and by the secondary-
address designators (`Apt`, `Apartment`, `Unit`, `Ste`, `Suite`, `Bldg`,
`Floor`, `Fl`, `Room`, `Rm`, `Lot`, `Space`, `Dept`, `Box`, `No`, `#`, …). They
are intentionally simple and documented in `src/py_mra/numbers.py` so they can
be tuned for a given dataset.

### Telling the library the type

When you already know a field's type — say you're processing a zip-code column —
skip the guessing and convert a single value directly. Pass a `NumberType` to
`number_to_words`, or omit it to let `classify` guess:

```python
from py_mra import number_to_words, classify, NumberType

number_to_words("90210", NumberType.ZIP)   # 'nine zero two one zero'
number_to_words("12", NumberType.UNIT)     # 'one two'  (identifier, not "twelve")
number_to_words("12", NumberType.CARDINAL) # 'twelve'
number_to_words("90210")                   # 'nine zero two one zero'  (classify -> ZIP)

classify("4B")        # NumberType.UNIT
classify("$19.99")    # NumberType.CURRENCY
```

`classify` precedence is currency → zip → phone → decimal → unit → cardinal; a
bare digit run defaults to `CARDINAL`, an isolated five-digit run to `ZIP`, and a
mixed alphanumeric token (`"4B"`) to `UNIT`. Forcing `CURRENCY` on a symbol-less
value defaults to dollars.

`numbers_to_words` also accepts `kind` to force **every** digit-bearing token in
a string to one type (each whitespace-delimited token is converted with
`number_to_words`, surrounding punctuation preserved):

```python
numbers_to_words("ids 90210 and 77", NumberType.ZIP)
# 'ids nine zero two one zero and seven seven'
```

## Tests

```bash
pytest
```

## License

[![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg
