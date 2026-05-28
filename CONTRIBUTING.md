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

By submitting a pull request, you agree that:

1. You keep the copyright to your contribution.
2. You grant the project maintainer, Robert Derveloy, a perpetual,
   worldwide, non-exclusive, royalty-free, irrevocable license to
   reproduce, prepare derivative works of, publicly display, publicly
   perform, sublicense, and distribute your contribution — and works
   derived from it — under **any license terms**, including AGPL-3.0,
   any successor open-source license, and proprietary / commercial
   licenses.
3. To the extent any patents you own read on your contribution, you grant
   the maintainer and downstream users of the project the same perpetual,
   worldwide, royalty-free license under those patents.
4. Your contribution is your original work, or you have the right to
   submit it under these terms, and you are not aware of any third-party
   claims, liens, or agreements that conflict.
5. If you contribute on behalf of an employer, your employer has either
   waived rights in your contribution or authorized you to submit it.

This is a condensed summary of the
[Harmony Individual Contributor License Agreement](https://harmonyagreements.org/),
"any license" option. Once GitHub's CLA-tracking app is set up on the
repository, you will be asked to confirm this agreement on your first PR;
until then, please include a line like the following in your PR description
so the agreement is on the record:

> I have read and agree to the CLA in CONTRIBUTING.md.

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
