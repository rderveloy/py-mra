# py-mra

Python implementation of the **Match Rating Approach** (MRA) algorithm — a
phonetic algorithm developed by Western Airlines in 1977 for indexing and
comparing homophonous names.

MRA has two parts: an **encoder** that reduces a single word to a short
*codex*, and a **comparison** that decides whether two words match by
reducing their codices and testing the result against a length-based
minimum-rating table.

## Install

```bash
pip install -e .          # from a checkout
pip install -e ".[test]"  # with the test dependencies
```

Requires Python 3.8+. No runtime dependencies.

## Quick start

**One-shot use** — encode and compare two words directly:

```python
from py_mra import (
    match_rating_codex,
    match_rating,
    match_rating_comparison,
)

match_rating_codex("Smith")                 # Codex('SMTH')
match_rating("Smith", "Smyth")              # 5  (MRA-native similarity)
match_rating_comparison("Smith", "Smyth")   # True
match_rating_comparison("Catherine", "Kathryn")  # True
match_rating_comparison("Smith", "Johnson") # False
match_rating_comparison("Al", "Alexandria") # None  (incomparable lengths)
```

**Batch use** — encode each word once, compare codices many times:

```python
from py_mra import (
    match_rating_codex,
    rating_from_codices,
    comparison_from_codices,
)

codices = [match_rating_codex(word) for word in many_words]

# Within a loop or vectorized comparison:
rating_from_codices(codices[0], codices[1])
comparison_from_codices(codices[0], codices[1])
```

`match_rating` is the numeric similarity score in the MRA range 0–6
(higher = more similar). `match_rating_comparison` adds the
threshold-aware boolean. The codex-taking versions
(`rating_from_codices`, `comparison_from_codices`) skip the per-call
encoding and are the right path for any non-trivial workload.

## API

| Function | Returns | Notes |
|----------|---------|-------|
| `match_rating_codex(word)` | `Codex` | Encode a single word. |
| `match_rating(name1, name2)` | `int` or `None` | Encode + compare. `None` if incomparable. |
| `match_rating_comparison(name1, name2)` | `bool` or `None` | Encode + compare against the minimum-rating table. |
| `rating_from_codices(codex1, codex2)` | `int` or `None` | Skip re-encoding; compare two `Codex` directly. |
| `comparison_from_codices(codex1, codex2)` | `bool` or `None` | Threshold-aware variant of the above. |
| `tokenize(text)` | `list[str]` | Split text for per-token MRA encoding. |
| `numbers_to_words(text, kind=None)` | `str` | Expand numeric runs in free text (see below). |
| `number_to_words(value, kind=None)` | `str` | Expand a single field value. |
| `classify(value)` | `NumberType` | Best-guess the type of a single field value. |
| `int_to_cardinal(n)` | `str` | A non-negative `int` as cardinal words. |

Types: `Codex` (str subclass for MRA codices), `NumberType` enum
(`CARDINAL`, `DECIMAL`, `CURRENCY`, `PHONE`, `ZIP`, `UNIT`).

Exceptions / warnings: `NumericInputError`, `MultiWordInputError`,
`SpecialCharacterWarning`.

Inputs are validated, not silently coerced. All functions raise
`TypeError` for wrong argument types; `match_rating_codex` raises
`NumericInputError` if the input contains a digit and
`MultiWordInputError` if it contains internal whitespace; `classify`
and `number_to_words` raise `ValueError` when given a value with no
ASCII digit. Each function's exact `Raises:` contract is in its
docstring.

### Encoding rules

1. Reject any input containing numeric characters (raises
   `NumericInputError`).
2. Reject any input containing internal whitespace (raises
   `MultiWordInputError`); leading and trailing whitespace is stripped
   silently as a convenience.
3. Transliterate accented letters to ASCII — `match_rating_codex("José")`
   equals `match_rating_codex("Jose")`.
4. Strip remaining non-letters. Punctuation and symbols are removed
   with a `SpecialCharacterWarning`.
5. Uppercase, keep the first letter, delete subsequent vowels, and
   collapse adjacent duplicate letters.
6. If the result exceeds six letters, keep the first three and the
   last three.

### Comparison rules

1. Encode both words.
2. If the codex lengths differ by 3 or more, the words are incomparable
   (`None`).
3. Derive the minimum rating from the sum of the lengths:

   | Length sum | Minimum rating |
   |-----------:|---------------:|
   | 1–4 | 5 |
   | 5–7 | 4 |
   | 8–11 | 3 |
   | 12 | 2 |

4. Remove characters that match position-for-position from the left,
   then from the right. The rating is `6 - max_unmatched`; the words
   match when the rating meets or exceeds the minimum.

## Multi-word inputs

MRA encodes one word. Multi-word inputs to `match_rating_codex` raise
`MultiWordInputError`, so the documented pipeline is to **tokenize
first** and encode each token separately:

```python
from py_mra import match_rating_codex, tokenize

codices = [match_rating_codex(token) for token in tokenize("Mary Ann")]
```

How to combine per-token comparison results into a single answer is the
caller's choice — there is no universal correct rule. The `tokenize`
docstring walks through common patterns (pairwise positional, set-based,
optimal assignment, skip-tokens). For inputs that also contain numbers,
use `numbers_to_words` first, then tokenize:

```python
from py_mra import numbers_to_words, tokenize, match_rating_codex

tokens = tokenize(numbers_to_words("221B Baker St"))
codices = [match_rating_codex(token) for token in tokens]
```

## Numbers and address fields

The encoder is strict and refuses any numeric input, so the
`numbers_to_words` utility expands numbers into spoken words first.

### Default reading rules

The scanner walks through each numeric run and picks a verbalization
based on the run's shape and surrounding context. Defaults are designed
to match how people actually say each kind of number, with overrides
available for callers who disagree.

| Input shape | Example input | Default output |
|------------|---------------|----------------|
| Currency | `$19.99` | `nineteen dollars and ninety nine cents` |
| Designator-before + identifier | `Apt 4B`, `Box 88`, `Route 66` | `Apt four B`, `Box eight eight`, `Route six six` |
| Phone | `(555) 123-4567` | `five five five one two three four five six seven` |
| Zip code (5 digits, or zip+4) | `90210-1234` | `nine zero two one zero one two three four` |
| House number + street designator | `221 Baker St` | `two two one Baker St` |
| Decimal | `3.14` | `three point one four` |
| Alphanumeric token (digits and letters adjacent) | `221B`, `4G` | `two two one B`, `four G` |
| Bare integer (quantity) | `66 pages` | `sixty six pages` |

The "designator-before" list includes `Apt`, `Apartment`, `Unit`,
`Suite`, `Ste`, `Bldg`, `Floor`, `Fl`, `Room`, `Rm`, `Lot`, `Space`,
`Dept`, `Box`, `No`, `#`, `Route`, `Hwy`, `Highway`, and `Interstate`.
The "street designator" list (matched *after* a number) includes `St`,
`Street`, `Ave`, `Avenue`, `Rd`, `Road`, `Blvd`, `Boulevard`, `Ln`,
`Lane`, `Way`, `Ct`, `Court`, `Pl`, `Place`, `Dr`, `Drive`, `Cir`,
`Circle`, `Pkwy`, `Parkway`, `Hwy`, `Highway`, `Trl`, `Trail`, `Aly`,
`Alley`, `Sq`, `Square`, `Ter`, `Terrace`, `Fwy`, `Freeway`, `Tpke`,
`Turnpike`. The full lists are documented in `src/py_mra/numbers.py`
and can be tuned for a dataset.

### Overriding the defaults

When you already know a field's type — say you're processing a
zip-code column — skip the heuristics and convert the value explicitly:

```python
from py_mra import number_to_words, NumberType

number_to_words("90210", NumberType.ZIP)        # 'nine zero two one zero'
number_to_words("12", NumberType.UNIT)          # 'one two'  (identifier)
number_to_words("12", NumberType.CARDINAL)      # 'twelve'   (quantity)
number_to_words("90210")                        # auto-classify -> ZIP
```

`classify` returns the heuristic's best guess so you can introspect it
without converting:

```python
from py_mra import classify
classify("4B")        # NumberType.UNIT
classify("$19.99")    # NumberType.CURRENCY
```

To force the same type for every digit-bearing token in a free-text
string, pass `kind=` to the scanner:

```python
from py_mra import numbers_to_words, NumberType

numbers_to_words("ids 90210 and 77", NumberType.ZIP)
# 'ids nine zero two one zero and seven seven'
```

## Pairing with other libraries

py-mra is, by design, a **strict MRA implementation** — not a general
phonetic-distance toolkit. For continuous-distance scoring,
edit-distance metrics, or alternative phonetic algorithms, pair py-mra
with libraries that specialize in those areas:

* **[rapidfuzz](https://github.com/rapidfuzz/RapidFuzz)** — fast,
  Rust-backed string-distance and ratio scoring. Useful when you want
  a continuous 0–100 similarity score on the MRA codices rather than
  the MRA-native 0–6 rating:

  ```python
  from py_mra import match_rating_codex
  from rapidfuzz.distance import Levenshtein

  codex1 = match_rating_codex("Smith")
  codex2 = match_rating_codex("Smyth")
  distance = Levenshtein.distance(codex1, codex2)
  ```

* **[jellyfish](https://github.com/jamesturk/jellyfish)** — C-backed
  implementations of Soundex, Metaphone, NYSIIS, Match Rating Codex,
  Jaro-Winkler, and Damerau-Levenshtein. Use when you want to compare
  MRA results against another phonetic algorithm, or when you want
  Jaro-Winkler on the codices.

py-mra deliberately doesn't reimplement what these libraries already
do well; the `Codex` type is interoperable with their distance
functions because it's a `str` subclass.

## Tests

```bash
pytest
```

The suite holds 100% statement and branch coverage on every release.

---

## Do I need a commercial license?

Probably not. AGPL covers most use cases without any action on your
part. Here's how to tell:

### Who can use this for free?

py-mra is available under **AGPL-3.0-or-later** at no cost for, among
others:

- **PhD students, researchers, and academic users** running py-mra
  locally for analysis or writing papers about results that use it.
- **Hobbyists and personal-project authors** — anything you're doing on
  your own machine for your own purposes.
- **Open-source projects** distributing software under AGPL-3.0 or a
  compatible license (including GPL-3.0).
- **Internal company use** for analysis, evaluation, or proofs-of-
  concept that don't ship to outside users.
- **Public services that are willing to release their stack** under
  AGPL-3.0 (per §13 of the license).

If you're in one of those buckets, you don't need to do anything
special — just follow the license terms, which for most of these cases
means "carry forward attribution and keep the code AGPL-licensed."

### When do I need a commercial license?

The commercial license is appropriate when AGPL's terms aren't
compatible with what you need to do, including:

- **Shipping a closed-source product** that embeds or builds on
  py-mra.
- **Running a hosted service** built on a modified py-mra without
  releasing the modifications and your service's source code.
- **Distributing py-mra inside a commercial software bundle** under
  proprietary terms.
- **Needing maintainer-provided support, indemnification, or a written
  commercial agreement** — even if AGPL would technically cover your
  use, those are reasons to take the commercial track.

For commercial licensing, contact
[**pymra.step200@aleeas.com**](mailto:pymra.step200@aleeas.com). The
commercial license bundles maintainer support, indemnification, access
to future versions, and use of the project name — things a clean-room
or AI-assisted reimplementation cannot provide.

---

> *The above is a plain-language summary of intent. The
> [LICENSE](./LICENSE) file is the legally controlling document. If
> your situation is unusual, see [LICENSE_FAQ.md](./LICENSE_FAQ.md) for
> edge cases, or email
> [pymra.step200@aleeas.com](mailto:pymra.step200@aleeas.com) and we'll
> give you a written answer.*

---

## License

[![License: AGPL v3+][agpl-shield]][agpl-license]

Copyright (C) 2026 Robert Derveloy.

py-mra is free software: you can redistribute it and/or modify it
under the terms of the [GNU Affero General Public License][agpl-license]
as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Affero General Public License for more details. You should have
received a copy of the license along with this program; if not, see
<https://www.gnu.org/licenses/>.

See [AI_USAGE.md](./AI_USAGE.md) for the project's position on
AI-assisted reimplementation.

[agpl-license]: https://www.gnu.org/licenses/agpl-3.0.html
[agpl-shield]: https://img.shields.io/badge/License-AGPL%20v3%2B-blue.svg
