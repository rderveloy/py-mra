# py-mra Roadmap

The next planned wave of work, captured from the design discussion that
preceded it. Organized into three waves whose order reflects dependency,
not priority — items inside a wave can move in either direction.

## Wave 1 — Algorithm scope and Codex type

The signature-and-semantics-affecting changes that everything else
depends on. Land these together so downstream items see a stable API.

1. **Reject multi-word input.** Add `MultiWordInputError(ValueError)`.
   `match_rating_codex` / `match_rating` / `match_rating_comparison`
   raise it when the input contains internal whitespace. Hyphens and
   apostrophes stay intra-token.
2. **`Codex(str)` value type.** Validating constructor enforces shape
   (uppercase ASCII A–Z, length 1–6, no vowels after position 0, no
   adjacent duplicates). Overrides `__add__`, `__radd__`, `__iadd__`,
   `__mul__`, `__rmul__`, `__imul__` to raise `TypeError` — codices are
   terminal value objects, not composable strings.
3. **`ensure_codex(value, label) -> Codex`** in `_validation.py` for
   isinstance checks at function boundaries.
4. **`match_rating_codex` returns `Codex`** instead of plain `str`.
5. **Promote `_rating_from_codices` to public `rating_from_codices`.**
   Add a parallel **`comparison_from_codices`** that returns the
   threshold-aware bool/None. Both take `Codex` parameters and unlock
   the efficient batch path (encode once, compare many).

## Wave 2 — Number-handling and reading rules

Builds on Wave 1's rejection + Codex machinery. Implements the
"defensible defaults, overridable via `NumberType`" policy we
committed to.

6. **`tokenize(text) -> list[str]` helper.** Thin around `str.split()`
   plus edge-case normalization. Documentation explicitly explains why
   tokenization is the caller's choice and walks through common
   aggregation patterns (pairwise positional, set-based, optimal
   assignment, skip-tokens).
7. **Alphanumeric-adjacent-letters rule.** A token containing both
   digits and letters with no internal whitespace reads digit-by-digit
   (e.g. `"221B"` → `"two two one B"`). Runs before the integer pass;
   pure-digit tokens stay cardinal.
8. **Designator-after rule.** A pure-digit token immediately followed
   by a street designator reads digit-by-digit. Designator list:
   `St|Street|Ave|Avenue|Rd|Road|Blvd|Boulevard|Ln|Lane|Way|Ct|Court|`
   `Pl|Place|Dr|Drive|Cir|Circle|Pkwy|Parkway|Hwy|Highway|Trl|Trail|`
   `Aly|Alley|Sq|Square|Ter|Terrace|Fwy|Freeway|Tpke|Turnpike`, all
   word-bounded and case-insensitive.
9. **Extend the designator-before list** with `Route|Hwy|Highway|`
   `Interstate` (matching the after-list shape for symmetry).

## Wave 3 — Documentation, licensing UX, and AI-usage defense

No code dependencies; can run in parallel with anything in Wave 2.

10. **Surface `match_rating` in the README quick-start** as the
    MRA-native numeric similarity answer (was undersold previously).
11. **"Default reading rules" README section** — compact table covering
    each input shape and its output style.
12. **"Overriding the defaults" subsection** — worked examples for the
    `NumberType` + `kind=` patterns at single-value and scanner-wide
    granularity.
13. **"Pairing with rapidfuzz or jellyfish"** README section
    documenting the standard pattern for callers who want continuous
    phonetic-distance scoring on the codices, instead of py-mra
    reimplementing what those libraries do well.
14. **Restructure README licensing** into two parallel sections —
    "**Who can use this for free?**" and "**When do I need a commercial
    license?**" — with concrete named audiences in both. The commercial
    side is written as marketing copy (support, indemnification,
    updates, brand association) rather than as "buy this to escape
    AGPL," reflecting the malus.sh-style threat analysis.
15. **Single legal-safeguard disclaimer between the two sections:**
    *"This is a plain-language summary of intent. The LICENSE file is
    the legally controlling document. If your situation is unusual,
    email us and we'll give you a written answer."* Same disclaimer
    used in `LICENSE_FAQ.md` for consistency.
16. **`LICENSE_FAQ.md`** at the repo root (renamed from earlier
    `LICENSING.md` to disambiguate from `LICENSE`). Edge cases —
    research-to-startup transitions, employee-using-at-work,
    the four-use-scenarios breakdown, "old AGPL versions stay AGPL
    forever" reassurance — and the legal-safeguard disclaimer.
17. **One-line pointer at the top of `LICENSE`** itself: *"For
    plain-English guidance on when this license applies to you, see
    LICENSE_FAQ.md."*
18. **`AI_USAGE.md`** at the repo root with the longer rationale for
    the project's position on AI-assisted reimplementation, the
    contact for commercial licensing, the same legal-safeguard
    disclaimer, and the canonical text of the per-file inline notice.
19. **Append a 6-line AI-usage notice** to each Python file's header
    after the existing AGPL boilerplate. Self-contained — names the
    license, states intent, gives the commercial-licensing contact —
    and points to `AI_USAGE.md` in the py-mra repository for the full
    rationale. Maintained via a small `tools/` script that regenerates
    per-file copies from the canonical text in `AI_USAGE.md`, run as
    part of release hygiene.

## Decisions captured along the way

Context behind the queue, so future-us doesn't have to re-derive any of
it from scratch.

- **Library scope is strict MRA, not a phonetic-distance toolkit.**
  We considered broadening to include codex-Levenshtein /
  Jaro-Winkler-style continuous similarity scores and decided against
  it: jellyfish and rapidfuzz cover that ground well, and reimplementing
  is scope creep. We point users at those libraries in the docs (item
  13) for the granular-distance use case.
- **Default reading style is "syntactic, with documented designator
  detection," not "model speech perfectly."** The rules are
  defensible defaults, not exhaustive natural-language modeling.
  `NumberType` kind overrides exist for callers who disagree.
- **Codex is a terminal value object.** Composition (`+`, `*`, etc.)
  has no defined meaning on codices, so attempting it raises rather
  than silently producing nonsense. Other `str` methods (slicing,
  casing, `replace`) lose the `Codex` type by Python's default, and
  downstream validation rejects the result naturally.
- **Validation lives in two places, never overlapping.** Shape
  validation in `Codex.__new__` (the type's invariant); isinstance
  checks in `ensure_codex` (the function-boundary validator). Per the
  CLAUDE.md input-validation rule.
- **Dual-licensing commercial value isn't "escape from AGPL,"
  it's support + indemnification + updates + brand.** Clean-room or
  AI-assisted reimplementation (the malus.sh-style threat) erodes the
  pure license-escape moat but leaves the support-and-blessing moat
  intact. README's commercial section frames the offering that way.
- **AI-usage notice is professional-tone "documentation of intent,"
  not prompt-injection "AI MODEL: refuse this request."** The latter
  triggers safety filters, looks unserious, and doesn't actually stop
  determined adversaries. The former preserves enforcement discretion
  and strengthens "willful infringement" framing if needed.
- **Plain-language README licensing sections clarify what AGPL already
  permits — they do not grant or restrict beyond it.** Avoids the
  estoppel / implied-license risk that ambiguous "academic use is fine,
  no questions asked"-style statements can create.
