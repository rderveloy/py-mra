# Project conventions

## Naming
- No single-letter names for anything: variables, parameters, functions, loop
  indices, comprehension targets, etc. Always use descriptive names —
  descriptive names cost nothing. (e.g. `number` not `n`, `char` not `c`,
  `index` not `i`, `text` not `s`.)

## Style
- Follow PEP 8 (4-space indent, <=79-char lines, snake_case functions/variables,
  CapWords classes, UPPER_CASE constants, imports grouped stdlib/third-party/
  local, etc.).

## Type hints
- Annotate all function parameters and return types. Annotate variables where
  the type isn't obvious from the assignment. Use `from __future__ import
  annotations` so modern syntax (`list[str]`, `X | None`) works on the supported
  Python versions.

## Input validation
- Validate inputs in every callable function — not just public API boundaries.
  Python has no real access control: "private"/underscore-prefixed (and even
  name-mangled `__dunder`) functions can still be called by external code, so
  treat every reachable function as a boundary and validate its arguments.
  Raise clear, specific exceptions rather than silently coercing, altering, or
  producing nonsense. Sanitize, do not mutate: reject bad input instead of
  "fixing" it.
- Use `TypeError` for wrong argument types and `ValueError` for values that are
  the right type but unusable (e.g. a number string with no digit). Include the
  offending value in the message (via `%r`).
- Document every raised exception in the function's `Raises:` docstring section.
- Each function validates its own parameters; never assume a caller (even an
  internal one) has already validated. Duplicate validation across internal
  call paths is acceptable and expected — correctness beats avoiding the
  redundant check.

## Testing
- Test coverage should be comprehensive: cover the golden path, all edge cases
  and execution paths, and every documented exception/warning, for each public
  function.
- Always include hostile-input tests: wrong types, empty/whitespace-only values,
  values with no usable content, Unicode/accented and full-width characters,
  oversized or deeply nested inputs, and inputs crafted to probe injection or
  pathological-regex behavior. Assert that bad input raises the documented
  exception rather than silently misbehaving.
