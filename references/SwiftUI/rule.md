---
name: swiftui
displayName: SwiftUI Best Practices
category: framework
description: View body complexity, view purity, and modifier chain length analysis with direct severity scoring
tags:
  - swiftui
examples:
  - Examples/
---

# SwiftUI Best Practices

> A View should be a function of its state — nothing more. — SwiftUI design philosophy
---

## The SwiftUI Metrics Framework

This framework provides objective scoring for SwiftUI view compliance. The primary
metrics are body complexity and view purity — both directly observable from code.

State proliferation is handled by SRP (cohesion groups, verb count). Sealed dependencies are handled by OCP (sealed points, testability).

## Metrics:

### SUI-1: Body Complexity

Measure nesting depth and view expression count across `body` AND all view-returning computed properties/methods (any property or method that returns `some View`).

**Definition:** A deeply nested or sprawling view hierarchy indicates a view that should be decomposed into extracted subviews. Complexity doesn't disappear when moved from `body` into helper `var`s — each view-returning property is measured independently.

**Detection:**

1. **Identify all view-returning properties** — `body` plus any `var`/`func` that returns `some View`
2. **For each view-returning property, measure:**
   - Max nesting depth of view builder expressions (each View/container that takes a `@ViewBuilder` closure adds one level)
   - Count of distinct view expressions (`Text`, `Image`, `Button`, `HStack`, `VStack`, `List`, custom view calls, etc.)
3. **Exclude modifiers** — `.padding()`, `.font()`, `.background()` do NOT add nesting or count as separate expressions
4. **Score per property** — if ANY view-returning property exceeds thresholds, it triggers a finding

**Result:**

| Property | Nesting Depth | Expression Count | Severity |
|----------|--------------|------------------|----------|
| body | ___ | ___ | ___ |
| ___ | ___ | ___ | ___ |

### SUI-2: View Purity

Detect business logic embedded in the view struct. A SwiftUI view must be dumb — it represents state, nothing more.

**Definition:** A view's only job is to declare UI as a function of state. Methods that fetch data, sort/filter collections, validate input, format values, or perform computation belong in a ViewModel or domain layer. This is a role-based constraint: it's not about *how many* verbs (that's SRP), it's about whether *any* verb is something a View should never do.

**Detection:**

1. **List every method and computed property** in the view struct (excluding `body`)
2. **Classify each as:**
   - PURE_VIEW — returns `some View`, configures view appearance, or toggles simple UI state (`showSheet = true`, `isExpanded.toggle()`)
   - IMPURE — any of the following:
     - DATA_FETCH — network calls, database reads, file I/O
     - TRANSFORM — sorting, filtering, mapping, grouping collections with business logic
     - FORMAT — string formatting, date formatting, number formatting (beyond inline `Text(value, format:)`)
     - VALIDATE — input validation, business rule checking
     - COMPUTE — calculations, state machine transitions, derived business state
3. **Count IMPURE methods/properties**

**Result:**

| Method/Property | Classification | Reason |
|-----------------|---------------|--------|
| | | |

| Category | Count |
|----------|-------|
| PURE_VIEW | ___ |
| IMPURE | ___ |

### SUI-3: Modifier Chain Length

Detect inline views nested inside `@ViewBuilder` closures that accumulate too many modifiers. Long modifier chains on nested views hurt readability — extract them into named computed properties.

**Definition:** When a view expression inside a `@ViewBuilder` closure (inside `body` or any view-returning property) has more than 2 chained modifiers, it should be extracted into a named `var` or separate subview. This keeps each closure body scannable at a glance.

**Scope:** Only counts modifiers on **nested child views** inside a closure — NOT on the top-level return value of `body` or a computed property. The top-level view's own modifiers are part of its external API and don't hurt readability.

**Detection:**

1. **For each `@ViewBuilder` closure** in `body` and view-returning properties
2. **For each child view expression** inside that closure (not the outermost container)
3. **Count chained modifiers** (`.font()`, `.padding()`, `.background()`, `.foregroundColor()`, `.frame()`, `.overlay()`, `.clipShape()`, etc.)
4. **Flag** if modifier count > 2

**Result:**

| View Expression | Location | Modifier Count | Severity |
|----------------|----------|---------------|----------|
| | | | |

### Exceptions (NOT violations):
1. **App entry point** — `@main` struct with `WindowGroup`/`Scene` composition. High nesting is expected at the app root.
2. **Preview providers** — `#Preview` blocks and `PreviewProvider` structs are not production code.
3. **Inline format specifiers** — `Text(price, format: .currency(code: "USD"))` and similar SwiftUI-native format APIs used directly in `body` are idiomatic, not impurity.
4. **Simple action forwarding** — A method that only calls one ViewModel method with no additional logic (e.g., `func retry() { viewModel.retry() }`) is PURE_VIEW.
5. **Top-level modifier chains** — Modifiers on the outermost view expression returned by `body` or a computed property are not flagged by SUI-3. Only nested child views inside closures are scoped.

### Severity Bands:
- COMPLIANT (nesting < 3 AND expressions < 5 AND impure == 0 AND max nested modifier chain <= 2)
- SEVERE (any of the following):
    - Nesting depth >= 3
    - View expressions > 5
    - 1+ impure methods
    - Any nested child view with 3+ modifiers
---

## Quantitative Metrics Summary
| ID    | Metric                  | Threshold                                         | Severity   |
|-------|-------------------------|---------------------------------------------------|------------|
| SUI-0 | Exception              | Falls into exception category                     | COMPLIANT  |
| SUI-1 | Body complexity        | Nesting < 3, expressions < 5                      | COMPLIANT  |
| SUI-2 | View purity            | 0 impure methods                                  | COMPLIANT  |
| SUI-3 | Modifier chain length  | All nested child modifiers <= 2                   | COMPLIANT  |
| SUI-1 | Body complexity        | Nesting >= 3 OR expressions >= 5                  | SEVERE     |
| SUI-2 | View purity            | 1+ impure methods                                 | SEVERE     |
| SUI-3 | Modifier chain length  | Any nested child view with 3+ modifiers           | SEVERE     |
---
