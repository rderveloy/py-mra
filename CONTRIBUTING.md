# Contributing to py-mra

Thanks for your interest. A few things to know before you open a PR.

## License and dual-licensing model

py-mra is published under the **GNU Affero General Public License v3 or
later** (AGPL-3.0-or-later), and is also available under a separate
commercial license for users who can't or don't want to comply with AGPL's
terms.

Both tracks exist together: AGPL for the open-source community, commercial
for downstream products that need to ship closed-source. The maintainer
needs the right to license your contribution under **both**, which is what
the Contributor License Agreement (CLA) below is for.

## Contributor License Agreement (CLA)

To make the dual-licensing model work, the maintainer needs broad
relicensing rights for every contribution. The agreements that grant
those rights live in [`cla/`](./cla/):

- **[Individual CLA](./cla/individual.md)** — for contributions you
  make on your own behalf.
- **[Corporate CLA](./cla/corporate.md)** — for contributions made on
  behalf of an employer or other entity. The entity signs once and lists
  its authorized contributors.

[`cla/README.md`](./cla/README.md) explains which one applies and gives
a plain-English summary of what you are agreeing to. Skim that first;
read the actual agreement before signing.

### How to sign

Once the CLA-tracking bot is installed on the repository, it will
prompt new contributors to confirm agreement on their first pull
request and block the merge until they do. The bot's signature record
is authoritative once it is in place.

Until then, please include a line in your pull request description
along the lines of:

> I have read [`cla/individual.md`](./cla/individual.md) (or
> [`cla/corporate.md`](./cla/corporate.md)) and agree to its terms.

That keeps pre-bot contributions on the record as license-compatible.

## Code conventions

This project follows the conventions captured in [`CLAUDE.md`](./CLAUDE.md).
Non-exhaustive highlights:

- PEP 8 with a 79-column line limit; descriptive names (no single-letter
  identifiers); modern type hints with `from __future__ import annotations`.
- Validate inputs in every callable, raise `TypeError` / `ValueError` with
  clear, value-bearing messages, and document each raised exception in the
  function's `Raises:` docstring section.
- Tests must cover the golden path, every edge case and execution path,
  and every documented exception/warning, including hostile-input
  categories such as wrong types and oversized inputs.

## Running the tests

```bash
pip install -e ".[test]"
pytest
```

The suite is expected to remain at 100% statement and branch coverage:

```bash
pytest --cov=py_mra --cov-branch --cov-report=term-missing
```

PEP 8 compliance is checked with `pycodestyle --max-line-length=79`.
