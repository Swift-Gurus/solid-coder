---
name: dry
displayName: Don't Repeat Yourself
category: practice
description: Reuse miss detection, inlined duplication analysis, and missing abstractions identification with direct severity scoring
bands:
  DRY-1:
    reuse_misses:
      severe:
        greater_than_or_equal: 1
  DRY-2:
    duplicate_sites:
      severe:
        greater_than_or_equal: 2
  DRY-3:
    missing_abstractions:
      severe:
        greater_than_or_equal: 1
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

Detect when new code was created for a responsibility that an existing type, function, view, extension, or convenience wrapper already covers.

<definition id="DRY-1" name="Reuse Miss">
A "reuse miss" occurs when a developer creates a new type, function, private view, computed property, or inline expression that duplicates the purpose of an existing abstraction in the codebase. The existing code may have a different name, live in a different module, or use slightly different naming conventions — but it serves the same role. This applies at every granularity — not just top-level types but also private helpers, view builders, and convenience extensions.

**Scope:** Every piece of new or modified code triggers a reuse check — types, functions (including private/internal), views, view builders, computed properties, extensions, inline expressions. Any granularity. If the code does something, search whether something in the codebase already does it.
</definition>

<detection id="DRY-1" name="Reuse Miss">
1. **Identify the responsibility** of each new or modified code unit — what does it do? What problem does it solve? This includes:
   - A new type or function (any access level)
   - A private view or view builder that composes a layout
   - A computed property that transforms or formats data
   - An inline expression that could be wrapped by an existing convenience
   - An object that provides functionality another object already provides
2. **Search the codebase** for existing code that serves the same responsibility:
   - Generate synonyms for the name and its responsibility (3 per keyword)
   - Search by name variants, method signatures, protocol conformances, variable types, and relationships
   - Search extensions on types being used — convenience wrappers are commonly missed
   - Search shared/common directories and design system modules for equivalent components, views, or layouts
3. **Classify matches:**
   - EXACT — existing code covers 100% of the need, could be used directly
   - EXTENSIBLE — existing code covers the core need, could be extended (via protocol extension, overload, or configuration) to cover the rest
   - PARTIAL — existing code covers some overlap but serves a genuinely different purpose
4. **Count** EXACT and EXTENSIBLE matches that were not reused = reuse misses
</detection>

### DRY-2: Inlined Duplication

Detect similar functions, algorithms, or logic sequences appearing in multiple locations that should be a single shared abstraction.

<definition id="DRY-2" name="Inlined Duplication">
When two or more locations contain the same logical sequence — same operations in the same order, same branching structure, same transform pipeline — the logic should be extracted into a shared function, type, or extension. The duplication may use different variable names or types but follows the same algorithm.
</definition>

<detection id="DRY-2" name="Inlined Duplication">
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
</detection>

### DRY-3: Missing Abstraction

Detect generic patterns buried inside domain-specific code instead of extracted as standalone reusable abstractions.

<definition id="DRY-3" name="Missing Abstraction">
When a type contains a pattern that is not specific to its domain, that pattern should be extracted as a standalone reusable type, function, or view component. The domain type should delegate to the abstraction, not implement it inline. The key signal is: could another part of the codebase need this exact same behavior, layout, or creation logic?
</definition>

<detection id="DRY-3" name="Missing Abstraction">
1. **Identify the domain** of the type under review — what business concept does it represent?
2. **Identify generic patterns** within the type — behavior, layout, or creation logic that is not specific to the domain:
   - Behavioral patterns (retry, queue, cache, observe, poll — any reusable flow)
   - Object creation patterns (similar initialization sequences, builder logic, factory patterns repeated across types)
   - UI composition patterns (recurring view structures, repeated styling + layout combinations, common interactive elements with shared behavior)
   - Data flow patterns (transform pipelines, validation chains, mapping sequences)
3. **Assess reuse potential** — could another part of the codebase need this same pattern?
   - If YES → missing abstraction
   - If NO (the pattern is inherently domain-specific) → not a violation
4. **Count** missing abstractions
</detection>

<exceptions>
1. **Intentionally specialized** — same shape but genuinely different domain semantics (e.g., two validation functions that happen to have similar structure but validate different business rules)
2. **Configuration/constants** — repeated literal values that are intentionally independent (changing one should NOT change the other)
3. **Protocol default implementations** — providing defaults for convenience is not duplication even if the body resembles another conformer
</exceptions>

<severity-bands id="DRY-1">
<band severity="SEVERE"><condition>reuse_misses >= 1</condition></band>
<band severity="COMPLIANT"><condition>reuse_misses == 0</condition></band>
</severity-bands>

<severity-bands id="DRY-2">
<band severity="SEVERE"><condition>duplicate_sites >= 2</condition></band>
<band severity="COMPLIANT"><condition>duplicate_sites == 0 or duplicate_sites == 1</condition></band>
</severity-bands>

<severity-bands id="DRY-3">
<band severity="SEVERE"><condition>missing_abstractions >= 1</condition></band>
<band severity="COMPLIANT"><condition>missing_abstractions == 0</condition></band>
</severity-bands>

---

## Quantitative Metrics Summary
| ID    | Metric              | Threshold                                    | Severity  |
|-------|---------------------|----------------------------------------------|-----------|
| DRY-0 | Exception           | Falls into exception category                | COMPLIANT |
| DRY-1 | Reuse miss          | 0 reuse misses                               | COMPLIANT |
| DRY-2 | Inlined duplication | 0 inlined duplications                       | COMPLIANT |
| DRY-3 | Missing abstraction | 0 missing abstractions                       | COMPLIANT |
| DRY-1 | Reuse miss          | 1+ existing code not reused                  | SEVERE    |
| DRY-2 | Inlined duplication | 1+ duplicated logic across locations          | SEVERE    |
| DRY-3 | Missing abstraction | 1+ generic pattern not extracted for reuse   | SEVERE    |
---
