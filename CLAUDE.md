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
