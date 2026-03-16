---
number: SPEC-005
feature: DRY principle
status: draft
blocked-by: []
blocking: []
---

# DRY Principle — Don't Repeat Yourself

## Description

A new principle in `references/DRY/` that detects and scores code duplication. DRY is critical for both the **review pipeline** (finding duplication in existing code) and the **validate-plan pipeline** (detecting when an architect proposes a component that duplicates existing functionality).

> Every piece of knowledge must have a single, unambiguous, authoritative representation within a system. — Hunt & Thomas, The Pragmatic Programmer

## Scope

DRY applies at multiple levels in Swift:

1. **Structural duplication** — identical or near-identical code blocks (copy-paste)
2. **Knowledge duplication** — same business rule expressed in multiple places
3. **Data duplication** — same constant, configuration, or mapping defined in multiple locations
4. **Type duplication** — types with overlapping responsibilities that should be unified or share a protocol

Level 4 (type duplication) is especially important for `validate-plan` — when the validator searches the codebase for existing types matching an architect's proposed components, DRY rules determine whether a "similar but not identical" match is a reuse candidate or a duplication risk.

## Metrics Framework

### DRY-1: Structural Similarity

**Detection:**

1. For each function/method body, extract the normalized structure (strip variable names, keep control flow shape)
2. Compare against all other function/method bodies in the same module/target
3. Flag pairs with >70% structural similarity

**Granularity:**
- **Exact clones** — identical after whitespace normalization
- **Parameterized clones** — identical structure, different variable names/literals
- **Structural clones** — same control flow shape, different operations

**Result:** List of clone pairs with similarity score and clone type.

### DRY-2: Knowledge Duplication

**Detection:**

1. Identify business rules — conditionals, validations, transformations, calculations
2. For each rule, search for the same logical condition/formula expressed elsewhere
3. Flag when the same rule appears in 2+ locations without sharing a single source of truth

**Signals:**
- Same magic numbers/strings in multiple files
- Same validation logic (e.g., `email.contains("@") && email.count > 3`) in multiple places
- Same mapping/transformation applied in multiple call sites

**Result:** List of duplicated knowledge items with all locations.

### DRY-3: Type Responsibility Overlap

**Detection:**

1. For each type, extract its responsibility (from solid-description if present, otherwise infer from methods/properties)
2. Compare responsibilities across types in the same module
3. Flag types with >60% responsibility overlap

**Signals:**
- Two types with similar method signatures operating on similar data
- Protocol conformances that overlap significantly
- Types that could be unified behind a shared protocol

**Result:** List of overlapping type pairs with overlap description.

## Severity Bands

| ID    | Metric                    | Threshold                              | Severity  |
|-------|---------------------------|----------------------------------------|-----------|
| DRY-0 | Exception                 | Intentional duplication (documented)   | COMPLIANT |
| DRY-1 | Structural similarity     | 1 clone pair, parameterized            | MINOR     |
| DRY-1 | Structural similarity     | 2+ clone pairs OR exact clones         | SEVERE    |
| DRY-2 | Knowledge duplication     | Same rule in 2 locations               | MINOR     |
| DRY-2 | Knowledge duplication     | Same rule in 3+ locations              | SEVERE    |
| DRY-3 | Type responsibility overlap | >60% overlap, 1 pair                 | MINOR     |
| DRY-3 | Type responsibility overlap | >60% overlap, 2+ pairs OR >80% single | SEVERE  |

## Exceptions (NOT violations)

1. **Test code** — Test files may intentionally duplicate setup/assertions for readability. Flag only if a shared test helper would clearly simplify.
2. **Protocol default implementations** — A default implementation that mirrors a concrete type is not duplication if the concrete type can be removed.
3. **Cross-module boundaries** — Duplication across module boundaries may be intentional to avoid coupling. Flag as MINOR with note, not SEVERE.
4. **Documented intentional duplication** — If a comment explicitly explains why duplication exists (e.g., performance, module isolation), mark as COMPLIANT.

## Interaction with Other Principles

- **SRP**: Extracting duplicated code often creates a new type → SRP must verify the extraction has a single responsibility
- **OCP**: Shared abstractions extracted from duplicates should be open for extension
- **ISP**: Extracted protocols should not force consumers to depend on methods they don't use
- **validate-plan**: DRY-3 (type overlap) is the primary signal for classifying components as `reuse` vs `create` vs `adjust`

## File Structure (when implemented)

```
references/DRY/
  rule.md                    — this spec's metrics + severity bands
  review/
    instructions.md          — detection phases for apply-principle-review
    output.schema.json       — review findings schema
  fix/
    instructions.md          — refactoring patterns (extract method, extract type, introduce protocol)
    output.schema.json       — fix suggestion schema
  refactoring.md             — step-by-step refactoring examples
  Examples/
    duplicate-validation-violation.swift
    duplicate-validation-compliant.swift
    type-overlap-violation.swift
    type-overlap-compliant.swift
```

## Definition of Done

- [ ] `references/DRY/rule.md` exists with metrics DRY-1, DRY-2, DRY-3 and severity bands
- [ ] `references/DRY/review/instructions.md` with detection phases following SRP pattern
- [ ] `references/DRY/review/output.schema.json` for review findings
- [ ] `references/DRY/fix/instructions.md` with refactoring patterns
- [ ] `references/DRY/fix/output.schema.json` for fix suggestions
- [ ] `references/DRY/refactoring.md` with worked examples
- [ ] `references/DRY/Examples/` with at least 2 violation/compliant pairs
- [ ] Principle auto-discovered by `discover-principles` skill (follows folder convention)
- [ ] DRY-3 metrics usable by `validate-plan` for type overlap detection
- [ ] Root spec updated to include DRY in principles table
