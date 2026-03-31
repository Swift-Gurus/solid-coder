---
name: dry
displayName: Don't Repeat Yourself
category: practice
description: Reuse miss detection, inlined duplication analysis, and missing abstractions identification with direct severity scoring
---

# Don't Repeat Yourself (DRY)

> Every piece of knowledge must have a single, unambiguous, authoritative representation within a system. — Andy Hunt & Dave Thomas
---

## The DRY Metrics Framework

This framework provides objective scoring for DRY compliance. The primary
metrics are reuse miss detection, inlined duplication analysis, and missing
abstraction identification — all directly observable from code.

## Metrics:

### DRY-1: Reuse Miss

Detect when new code was created for a responsibility that an existing type, protocol, or extension already covers.

**Definition:** A "reuse miss" occurs when a developer creates a new type or function that duplicates the purpose of an existing abstraction in the codebase. The existing type may have a different name, live in a different module, or use slightly different naming conventions — but it serves the same role.

**Detection:**

1. **Identify the responsibility** of each new or modified type — what does it do? What problem does it solve?
2. **Search the codebase** for existing types that serve the same responsibility:
   - Generate synonyms for the type name and its responsibility
   - Search by name variants (e.g., a new `ProductList` when `ItemCatalog` already exists)
   - Search by method signatures and protocol conformances
   - Search by variable types and relationships
3. **Classify matches:**
   - EXACT — existing type covers 100% of the need, could be used directly
   - EXTENSIBLE — existing type covers the core need, could be extended (via protocol extension, subclass, or configuration) to cover the rest
   - PARTIAL — existing type covers some overlap but serves a genuinely different purpose
4. **Count** EXACT and EXTENSIBLE matches that were not reused = reuse misses

### DRY-2: Inlined Duplication

Detect similar functions, algorithms, or logic sequences appearing in multiple locations that should be a single shared abstraction.

**Definition:** When two or more locations contain the same logical sequence — same operations in the same order, same branching structure, same transform pipeline — the logic should be extracted into a shared function, type, or extension. The duplication may use different variable names or types but follows the same algorithm.

**Detection:**

1. **For each function or method** in the unit under review, identify its logical sequence — what operations does it perform, in what order?
2. **Search other units in the same module/target** for methods with the same logical sequence:
   - Same control flow structure (if/else, guard, switch patterns)
   - Same operation ordering (fetch → validate → transform → persist)
   - Same algorithm with different concrete types
3. **Classify matches:**
   - IDENTICAL — same logic, same types, different names only
   - STRUCTURAL — same algorithm, different types (candidate for generics)
   - SIMILAR — overlapping logic with meaningful differences (not a violation)
4. **Count** IDENTICAL and STRUCTURAL matches = inlined duplications

### DRY-3: Missing Abstraction

Detect generic patterns buried inside domain-specific code instead of extracted as standalone reusable abstractions.

**Definition:** When a type contains a pattern that is not specific to its domain, that pattern should be extracted as a standalone reusable type, function, or view component. The domain type should delegate to the abstraction, not implement it inline. The key signal is: could another part of the codebase need this exact same behavior, layout, or creation logic?

**Detection:**

1. **Identify the domain** of the type under review — what business concept does it represent?
2. **Identify generic patterns** within the type — behavior, layout, or creation logic that is not specific to the domain:
   - Behavioral patterns (retry, queue, cache, observe, poll — any reusable flow)
   - Object creation patterns (similar initialization sequences, builder logic, factory patterns repeated across types)
   - UI composition patterns (recurring view structures, repeated styling + layout combinations, common interactive elements with shared behavior)
   - Data flow patterns (transform pipelines, validation chains, mapping sequences)
3. **Assess reuse potential** — could another part of the codebase need this same pattern?
   - If YES and the pattern is non-trivial (more than a few lines) → missing abstraction
   - If NO (the pattern is inherently domain-specific) → not a violation
4. **Count** missing abstractions

### Exceptions (NOT violations):
1. **Trivial code** — duplicated logic under 3 lines (too small to justify abstraction overhead)
2. **Intentionally specialized** — same shape but genuinely different domain semantics (e.g., two validation functions that happen to have similar structure but validate different business rules)
3. **Test code** — test helpers, fixtures, and setup code are governed by testing conventions, not DRY
4. **Configuration/constants** — repeated literal values that are intentionally independent (changing one should NOT change the other)
5. **Protocol default implementations** — providing defaults for convenience is not duplication even if the body resembles another conformer

### Severity Bands:
- COMPLIANT (0 reuse misses AND 0 inlined duplications AND 0 missing abstractions)
- SEVERE (any of the following):
    - 1+ reuse miss (existing type covers the need, was not used)
    - 1+ inlined duplication (same logic in 2+ locations)
    - 1+ missing abstraction (generic pattern not extracted for reuse)
---

## Quantitative Metrics Summary
| ID    | Metric              | Threshold                                    | Severity  |
|-------|---------------------|----------------------------------------------|-----------|
| DRY-0 | Exception           | Falls into exception category                | COMPLIANT |
| DRY-1 | Reuse miss          | 0 reuse misses                               | COMPLIANT |
| DRY-2 | Inlined duplication | 0 inlined duplications                       | COMPLIANT |
| DRY-3 | Missing abstraction | 0 missing abstractions                       | COMPLIANT |
| DRY-1 | Reuse miss          | 1+ existing type not reused                  | SEVERE    |
| DRY-2 | Inlined duplication | 1+ duplicated logic across locations          | SEVERE    |
| DRY-3 | Missing abstraction | 1+ generic pattern not extracted for reuse   | SEVERE    |
---
