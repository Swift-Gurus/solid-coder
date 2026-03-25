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


### SUI-4: ViewModel Injection

Detect views that depend on a concrete ViewModel type for logic or data access.

**Definition:** When a view delegates logic or data access to a ViewModel,                                                                                                                                                            
that dependency must be injected via protocol interfaces — a State protocol                                                                                                                                                         
(what the view reads) and an Actions protocol (what the view triggers).                                                                                                                                                               
A view referencing a concrete ViewModel class is sealed to that implementation.

**Detection:**

1. **Identify the ViewModel property** — the stored property that serves as
   the view's logic/data source (typically @Observable class, ObservableObject,
   or any type providing business state + actions)
2. **Check injection style:**
    - Concrete class type → VIOLATION
    - Protocol that extends `Observable` → must use generic constraint
      (SwiftUI's observation tracking needs the concrete type at compile time).
      Generic constrained to protocol(s) → COMPLIANT.
      Plain protocol property → VIOLATION (observation won't work)
    - Protocol that does NOT extend `Observable` → plain protocol-typed
      property is COMPLIANT. No generic needed.
3. **Not in scope:** plain value properties (String, Bool, structs),
   closures/actions, nested child views, style/configuration types

**Result:**

| Property | Type | Concrete/Protocol | Severity |                                                                                                                                                                                    
|----------|------|-------------------|----------|     
| | | | |                                                                                                                                                                                                                             

### SUI-5: Preview-Only View Containment

Detect views that exist solely for Xcode Previews but are declared at file scope, causing them to ship in the production binary.

**Definition:** A view whose only purpose is visual validation in Xcode Previews (design token galleries, component showcases, layout experiments) must be defined entirely inside a `#Preview` block or `PreviewProvider` struct. The compiler strips `#Preview` blocks and `PreviewProvider` types from release builds, so code inside them never ships. Views and helper types declared at file scope — even if only referenced from `#Preview` — are included in the binary as dead code.

**Detection:**

1. **Identify file-scope view structs** — list every `struct` conforming to `View` declared at file scope (not nested inside `#Preview`, `PreviewProvider`, or another type)
2. **Identify file-scope helper types** — list every `struct`, `class`, or `enum` at file scope that does NOT conform to `View` but is only referenced by a preview-only view (support models, mock data, factory types)
3. **For each file-scope view, check caller sites:**
   - Search the file and codebase for references to this view outside of `#Preview` blocks and `PreviewProvider` structs
   - If the view is referenced ONLY inside `#Preview` or `PreviewProvider` → mark as **PREVIEW_ONLY**
   - If the view is referenced in production code (other views, app entry point, navigation) → mark as **PRODUCTION** — not a violation
   - If the view has ZERO references anywhere (orphan) → mark as **PREVIEW_ONLY** (dead code)
4. **For each PREVIEW_ONLY view**, also flag its helper types (step 2) as PREVIEW_ONLY
5. **Score:**
   - All file-scope views are PRODUCTION → COMPLIANT
   - Any file-scope view is PREVIEW_ONLY → SEVERE

**Result:**

| Type | Name | Location | References | Classification |
|------|------|----------|------------|----------------|
| | | | | |

### SUI-6: Preview Coverage

Detect View structs that have no preview anywhere in the codebase.

**Definition:** Every View struct declared at file scope must be instantiated in at least one `#Preview` block or `PreviewProvider` struct — either in the same file or in a separate preview file. Views without previews cannot be visually validated during development.

**Detection:**

1. **Identify file-scope View structs** — list every `struct` conforming to `View` declared at file scope
2. **Search for preview instantiation** — for each View struct, search:
   - The same file for `#Preview` blocks or `PreviewProvider` structs that instantiate it
   - Other files in the module for `#Preview` blocks or `PreviewProvider` structs that instantiate it (e.g., dedicated preview files)
3. **Score:**
   - View is instantiated in at least one preview → COMPLIANT
   - View has no preview instantiation anywhere → SEVERE

**Result:**

| View | File | Has Preview | Preview Location | Severity |
|------|------|-------------|-----------------|----------|
| | | | | |

### Exceptions (NOT violations):
1. **App entry point** — `@main` struct with `WindowGroup`/`Scene` composition. High nesting is expected at the app root.
2. **Preview providers** — `#Preview` blocks and `PreviewProvider` structs are not production code.
3. **Inline format specifiers** — `Text(price, format: .currency(code: "USD"))` and similar SwiftUI-native format APIs used directly in `body` are idiomatic, not impurity.
4. **Simple action forwarding** — A method that only calls one ViewModel method with no additional logic (e.g., `func retry() { viewModel.retry() }`) is PURE_VIEW.
5. **Top-level modifier chains** — Modifiers on the outermost view expression returned by `body` or a computed property are not flagged by SUI-3. Only nested child views inside closures are scoped.

### Severity Bands:
- COMPLIANT (nesting < 3 AND expressions < 5 AND impure == 0 AND max nested modifier chain <= 2 AND VM injected via protocol AND all file-scope views have production callers AND all file-scope views have preview coverage)
- SEVERE (any of the following):
    - Nesting depth >= 3
    - View expressions > 5
    - 1+ impure methods
    - Any nested child view with 3+ modifiers
    - Concrete VM injection
    - File-scope view only referenced from #Preview/PreviewProvider (preview-only)
    - File-scope view with no #Preview or PreviewProvider instantiation anywhere
---

## Quantitative Metrics Summary
| ID    | Metric                | Threshold                                                          | Severity  |
|-------|-----------------------|--------------------------------------------------------------------|-----------|
| SUI-0 | Exception             | Falls into exception category                                      | COMPLIANT |
| SUI-1 | Body complexity       | Nesting < 3, expressions < 5                                       | COMPLIANT |
| SUI-2 | View purity           | 0 impure methods                                                   | COMPLIANT |
| SUI-3 | Modifier chain length | All nested child modifiers <= 2                                    | COMPLIANT |
| SUI-4 | VM injection          | VM injected as an interface, view has generic signature            | COMPLIANT |
| SUI-5 | Preview containment   | All file-scope views have production callers                       | COMPLIANT |
| SUI-6 | Preview coverage      | All file-scope views instantiated in a preview                     | COMPLIANT |
| SUI-1 | Body complexity       | Nesting >= 3 OR expressions >= 5                                   | SEVERE    |
| SUI-2 | View purity           | 1+ impure methods                                                  | SEVERE    |
| SUI-3 | Modifier chain length | Any nested child view with 3+ modifiers                            | SEVERE    |
| SUI-4 | VM injection          | VM injected as a concrete implementation                           | SEVERE    |    
| SUI-5 | Preview containment   | Any file-scope view only referenced from #Preview/PreviewProvider  | SEVERE    |
| SUI-6 | Preview coverage      | Any file-scope view with no preview instantiation                  | SEVERE    |
---
