# Project conventions

## Meta: examples in rules
- Any examples given within a rule must be either a complete enumeration or
  explicitly marked as non-exhaustive. Acceptable markers (non-exhaustive
  examples): "non-exhaustive examples:", "such as", "including but not
  limited to". A bare "e.g." or a trailing "etc." is not sufficient on its
  own — the non-exhaustive nature must be unambiguous to a reader who has
  not read this meta-rule.

## Naming
- No single-letter names for anything. Non-exhaustive examples of where this
  applies: variables, parameters, functions, loop indices, comprehension
  targets. Always use descriptive names — descriptive names cost nothing.
  Non-exhaustive examples: `number` not `n`, `char` not `c`, `index` not
  `i`, `text` not `s`.

## Style
- Follow PEP 8. Non-exhaustive examples of the rules it covers: 4-space
  indent, <=79-char lines, snake_case functions/variables, CapWords classes,
  UPPER_CASE constants, imports grouped stdlib/third-party/local.

## Type hints
- Annotate all function parameters and return types. Annotate variables
  where the type isn't obvious from the assignment. Use `from __future__
  import annotations` so modern syntax works on the supported Python
  versions (non-exhaustive examples of such syntax: `list[str]`,
  `X | None`).

## Input validation
- Validate inputs in every function we author that is directly callable —
  not just public API boundaries. Python has no real access control:
  "private"/underscore-prefixed (and even name-mangled `__dunder`) methods
  can still be called by external code, so validate all parameters of each
  such function, including ones that only feed error messages. Raise clear,
  specific exceptions rather than silently coercing, altering, or producing
  nonsense. Sanitize, do not mutate: reject bad input instead of "fixing"
  it.
- Scope is authorship and reachability: this applies only to functions we
  write, never to third-party code we didn't (don't wrap or re-validate it).
  Nested or anonymous functions that aren't reachable on their own — only
  invoked through a named wrapper that already validates — need no
  validation of their own.
- Use `TypeError` for wrong argument types and `ValueError` for values that
  are the right type but unusable (non-exhaustive example: a number string
  with no digit). Include the offending value in the message (via `%r`).
- Document every raised exception in the function's `Raises:` docstring
  section.
- Each function validates its own parameters; never assume a caller (even
  an internal one) has already validated. Duplicate validation across
  internal call paths is acceptable and expected — correctness beats
  avoiding the redundant check.

## Testing
- Test coverage should be comprehensive: cover the golden path, all edge
  cases and execution paths, and every documented exception/warning, for
  each public function.
- Always include hostile-input tests. Non-exhaustive examples of categories
  to cover: wrong types, empty/whitespace-only values, values with no
  usable content, Unicode/accented and full-width characters, oversized or
  deeply nested inputs, and inputs crafted to probe injection or
  pathological-regex behavior. Assert that bad input raises the documented
  exception rather than silently misbehaving.

## Documentation
- Every comment must at least explain the *why* (the rationale). The *why*
  is the floor and is never optional. Explaining the *what* in addition is
  welcome, but a comment that gives only the *what*, with no *why*, is
  insufficient.

## Accidental-mistake prevention
- Design APIs so that a caller's honest mistake cannot silently corrupt
  internal state — mutation must be possible only through sanctioned,
  validating methods. Non-exhaustive examples of techniques: return
  defensive copies of mutable data rather than internal references; expose
  read-only views of internals (such as `types.MappingProxyType`, `tuple`,
  `frozenset`); hide mutable state behind read-only properties; reject
  in-place mutation attempts at the boundary.

## Clean Code
- Follow the principles of *Clean Code* by Robert C. Martin.
  Non-exhaustive examples of those principles: small functions that do one
  thing at a single level of abstraction; meaningful, intention-revealing
  names; minimal arguments (prefer 0–3, avoid flag arguments); command-
  query separation; no hidden side effects; DRY; prefer exceptions to
  error codes; no dead code; leave code cleaner than you found it
  (boy-scout rule).

## Clean Architecture
- Follow the principles of *Clean Architecture* by Robert C. Martin.
  Non-exhaustive examples of those principles: separation of concerns
  across boundaries; the dependency rule — source dependencies point
  inward toward higher-level policy/abstractions, never toward details;
  business logic independent of frameworks, UI, DB, and IO; depend on
  abstractions via interfaces; the SOLID principles.
