# Decision Making

This document captures how the system makes key decisions at each stage of the pipeline — from what to review, through how to classify findings, to how conflicting fixes are resolved.

---

## 1. Principle Activation

**Question:** Which principles apply to a given review?

**Decision logic:**

```
Step 1: Discovery
  Run discover-principles script → all principles + all_candidate_tags
  (parses rule.md frontmatter, extracts tags field from each)

Step 2: Tag Matching (if candidate_tags is non-empty)
  Pass candidate_tags to prepare-review-input agent
  Agent reads code → extracts imports (script) + analyzes patterns (agent judgment)
  Merges into matched_tags in review-input.json

Step 3: Filtering
  Run discover-principles script with --review-input → active_principles

  For each principle:
    if no tags in rule.md → ALWAYS ACTIVE (include)
    if has tags → check intersection with matched_tags
      if any tag matches → INCLUDE
      else → SKIP

  For included principles:
      Run load-reference script with files_to_load → clean content (frontmatter stripped)
```

**Current state:** SRP, OCP, LSP, ISP have no tags → always active. Framework-tier principles (SwiftUI, TCA) will use `tags: [swiftui]`, `tags: [tca]` for conditional activation when implemented.

---

## 2. Severity Classification

Each principle defines its own metrics and severity bands. The system does not use subjective judgment — severity is computed from measured values.

### SRP Severity

| Condition | Severity |
|-----------|----------|
| 1 cohesion group AND 1-2 verbs | COMPLIANT |
| 1 cohesion group AND 3+ verbs AND 1 stakeholder | MINOR |
| 2+ cohesion groups OR (3+ verbs AND 2+ stakeholders) | SEVERE |

**Exception override:** If the unit is a Facade/Coordinator (all-protocol deps, pure delegation, no internal construction) → COMPLIANT regardless of metrics.

### OCP Severity

| Condition | Severity |
|-----------|----------|
| 0 sealed points AND 0 untestable deps | COMPLIANT |
| 0 sealed points AND 1-2 testable DIRECT deps | MINOR |
| 1+ sealed points OR 1+ untestable deps | SEVERE |

**Exception overrides:**
- Factories → COMPLIANT
- Helpers (Encoders, Formatters, Locks) → COMPLIANT
- Pure data structures → COMPLIANT
- Boundary Adapters (wrapping truly static-only APIs like enums with static members) → COMPLIANT

### LSP Severity

| Condition | Severity |
|-----------|----------|
| 0 net type checks AND 0 contract violations AND 0 empty/fatal methods | COMPLIANT |
| <50% empty (non-fatal) methods | MINOR |
| 1+ type checks OR 1+ contract violations OR 1+ fatalError methods OR >=50% empty | SEVERE |

**Exception overrides:**
- External/framework-forced casts (e.g., `response as? HTTPURLResponse`) → not counted
- NoOp objects (name contains NoOp + 100% empty methods) → COMPLIANT

### ISP Severity

| Condition | Severity |
|-----------|----------|
| Protocol width <= 5 AND all conformer coverage >= 80% | COMPLIANT |
| Width 6-8 AND all conformers >= 60%, OR width <= 5 AND any conformer 60-79% | MINOR |
| Width > 8 OR any conformer < 60% OR 2+ cohesion groups OR 1+ conformers with 3+ empty/stub methods | SEVERE |

**Exception overrides:**
- Non-protocol units → COMPLIANT (ISP applies only to protocols)
- Marker protocols (zero requirements) → COMPLIANT
- Single-conformer protocols → flag as "unable to verify" but not a violation
- Composition protocols (`protocol P: A, B {}`) → not a violation if components are compliant
- @objc protocols → "framework-constrained"
- Protocols with default implementations covering non-meaningful methods → not forced

---

## 3. Dependency Classification (OCP)

OCP's metric system requires classifying every dependency of a unit. This is one of the most nuanced decisions:

```
For each dependency of a unit:

  1. Is it abstract? (protocol-typed)
     → ABSTRACT — does not count toward sealed points

  2. Is it concrete but INJECTED? (passed via init, method param, or factory)
     → DIRECT INJECTED — not a sealed point, but checked for testability

  3. Is it concrete and NOT injected? (instantiated internally, singleton, static call)
     → Check exceptions:
       a. Is it a factory? → Exception, skip
       b. Is it a helper? (Encoder, Formatter, Lock, etc.) → Exception, skip
       c. Is it a pure data structure? → Exception, skip
       d. Is it a boundary adapter for a static-only API? → Exception, skip
     → If no exception: SEALED POINT (counts toward OCP-1)

  4. Is it used by an injected dependency? (transitive)
     → INDIRECT — checked for testability but not for sealed points
```

---

## 4. Fix Strategy Selection

When a violation is detected, the fix strategy depends on the principle and severity.

### SRP Fix Strategy

```
if severity == MINOR:
    Light touch — extract methods within the same class
    Group related methods, rename for clarity
    Do not split the class

if severity == SEVERE:
    Phase 1: Extract methods within class (group by cohesion)
    Phase 2: Extract each cohesion group into its own type behind a protocol
    Original class becomes a Facade/Coordinator
```

### OCP Fix Strategy

```
For each sealed point:
    1. Check if a protocol already exists for this dependency → use it
    2. Check if the concrete type can be extended to conform → extension conformance
    3. Create an Adapter/Wrapper → only if the type can't reasonably conform
    4. Update the original class to depend on the protocol

Priority order: reuse > extend > adapt > wrap
```

### LSP Fix Strategy

```
For type checks (LSP-1):
    → Protocol extraction + generic constraints
    → Eliminate the need for runtime type switching

For contract violations (LSP-2):
    strengthened preconditions → Update base contract OR handle in subtype
    weakened postconditions   → Honor base guarantees OR update base contract
    invariant violations      → Add validated setters with guards

For empty/fatal methods (LSP-3):
    → Interface redesign: split the protocol
    → Composition over inheritance
```

### ISP Fix Strategy

```
For each wide protocol:
    1. Identify cohesion groups from conformer usage patterns
    2. Split into role interfaces (one per cohesion group)
    3. Create a composition protocol: protocol Original: RoleA, RoleB {}
    4. Update consumers to depend on the narrowest role they need
    5. Provide default implementations where appropriate

Priority order: split > role_interface > composition_protocol > default_implementation
```

---

## 5. Cross-Principle Conflict Resolution (Synthesis)

This is the most critical decision point. When multiple principles suggest changes to the same code, their fixes can conflict.

### The Two-Pass Algorithm

**Pass 1 — Draft:** Each principle generates fix actions independently, using only its own fix patterns.

**Pass 2 — Cross-check:** Each draft action is tested against ALL other active principles:

```
For each draft action A from principle P:
  For each other active principle Q:
    Simulate: "If I apply action A, would Q's metrics worsen?"

    Example checks:
    - SRP action extracts a class → Does this create new sealed points? (OCP)
    - OCP action injects a dependency → Does this create multiple cohesion groups? (SRP)
    - LSP action adds a protocol → Does the hierarchy need type checking? (LSP self-check)
    - ISP action splits a protocol → Do the split protocols break existing conformers? (LSP check)

    if Q's metrics worsen:
        Attempt to patch action A using Q's fix patterns
        if patch succeeds:
            Update action A with patched version
            Record cross_check_result: { principle: Q, status: "patched" }
        if patch fails:
            Mark finding as UNRESOLVED
            Record reason: "Cannot satisfy both P and Q constraints"
```

### Conflict Types and Resolutions

| Conflict | Example | Resolution |
|----------|---------|------------|
| SRP extract creates sealed point | Extracting `NetworkService` from a class creates a concrete dependency | Make the extracted type protocol-backed (OCP patch) |
| OCP injection adds cohesion group | Injecting a `Logger` creates a new cohesion group | Accept if single-method bridge; otherwise extract logger usage to decorator |
| SRP + OCP same code | Both want to modify how a dependency is used | Merge into single action: extract + inject in one step |
| Unresolvable | Principle requirements are fundamentally contradictory for this code | Mark as unresolved with explanation |

### Merge Rules

```
For actions that touch the same code region:
  if synergistic (both improve the same thing from different angles):
      MERGE into single action
      Combine todo_items
      Union of resolves[]

  if conflicting (one undoes the other):
      Keep the higher-severity resolution
      Mark the other as unresolved

  if independent (different code regions):
      Keep both, add dependency ordering
```

### Ordering

Final actions are ordered by:
1. **Dependency graph** — if action B depends on action A's output, A goes first
2. **Severity** — SEVERE before MINOR within the same dependency level

---

## 6. File Organization Decisions

When creating new types during refactoring, the system follows these rules:

```
For each new type created:

  if type is a protocol AND its base implementation:
      → Same file, named after the implementation
      Example: UserFetching protocol + RemoteUserFetcher → RemoteUserFetcher.swift

  if type is an additional conformer of an existing protocol:
      → Separate file, named after the conformer
      Example: MockUserFetcher → MockUserFetcher.swift

  if type is a small helper (<10 lines):
      → Stays inline in the file that uses it

  if type is a facade/coordinator:
      → Keep the original filename
      Extracted types get their own files
```

---

## 7. Iteration Decisions

After implementation, the system decides whether to iterate:

```
if iteration_counter >= MAX_ITERATIONS:
    STOP — report results as-is

if iteration_counter < MAX_ITERATIONS:
    Re-prepare input (source_type = "changes")
    Re-run review on modified files only

    if new findings exist:
        Re-synthesize + Re-implement
        Increment counter
        Loop

    if no new findings:
        STOP — code is clean
```

Default MAX_ITERATIONS = 2. Configurable via `--iterations N`.

The iteration loop catches cascading issues — for example, an SRP extraction in iteration 1 might create a new OCP violation that gets caught and fixed in iteration 2.

---

## 8. Exception Recognition

Exceptions are a key part of reducing false positives. Each principle has specific exception patterns:

### SRP Exceptions
- **Facade/Coordinator:** All dependencies are protocol-typed, all methods are pure delegation (no logic, no transformation), no internal construction → COMPLIANT

### OCP Exceptions
- **Factory:** Its job is to create concrete instances → constructing types is expected
- **Helper:** Encoders, Formatters, Locks, DateFormatters → stateless utilities with no variation points
- **Pure Data Structure:** Struct/class with only stored properties and no behavior
- **Boundary Adapter:** Wraps a truly static-only API (enum with static members, global functions) that cannot be instantiated or subclassed

### LSP Exceptions
- **Framework-forced casts:** `response as? HTTPURLResponse`, `error as NSError` → the framework API requires this, developer has no choice
- **NoOp objects:** Name explicitly says NoOp AND 100% of methods are empty → intentional null object pattern

### Design Pattern Recognition

The system loads pattern references from `references/design_patterns/` to recognize when code follows a known pattern. Each pattern has structural criteria:

| Pattern | Recognition Criteria |
|---------|---------------------|
| **Facade** | All-protocol dependencies + pure delegation + no internal construction |
| **Adapter** | Conforms to target protocol + wraps adaptee + translates interface |
| **Decorator** | Same interface as wrapped + single wrapped dependency + delegates with additions |
| **Strategy** | Protocol-typed strategy property + no type-switching in context |
