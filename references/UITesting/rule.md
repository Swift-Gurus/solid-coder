---
name: uitesting
displayName: UI Testing
category: practice
description: UI test structure, flow encapsulation, assertion efficiency, synchronization, and identifier quality with direct severity scoring
tags:
  - ui-test
---

# UI Testing

> A UI test suite is code. It has the same quality obligations as production code: single responsibilities, no duplication, clear structure. The difference is that every bad pattern costs test time — repeated flows, sleep-based waits, and missing coordinators compound across every CI run.
---

## The UI Testing Metrics Framework

Five metrics cover the structural and behavioral properties of a UI test suite. Each is directly observable from test code.

## Metrics:

### UITEST-1: Flow Encapsulation

Detect navigation logic that is not encapsulated in a coordinator.

**Definition:** 
Any multi-step sequence of UI interactions needed to reach a specific app state is a flow. 
Flows belong in dedicated coordinator types — not inlined in test methods. 
A coordinator is any named type (struct or class) that holds an `app` reference and exposes named methods for reaching app states. 
Coordinators compose: a coordinator for a later screen holds and delegates to the coordinator for the screen that precedes it.

**Detection:**

1. **Inline flows** — flag any test method that contains a sequence of 3 or more direct UI interactions (tap, type, navigate, wait for element, keyboard shortcut) to reach a state, without delegating to a named coordinator type
2. **Duplicated sequences** — scan all test methods in the same class (and across classes in the same file) for identical or near-identical interaction sequences; each duplication that has no coordinator is a violation
3. **Coordinator not composing** — flag a coordinator type that re-implements navigation steps already encapsulated in another coordinator for a prior screen, instead of holding and calling it

**Count:** Number of flow encapsulation violations found.

---

### UITEST-2: Base Class Structure

Detect test suites that manage their own lifecycle and setup instead of inheriting from a shared base class.

**Definition:** 
App launch, teardown, and all conditional setup (clean persistence, prefilled state, animation control, state reset arguments) are base class responsibilities. 
The base class owns the `XCUIApplication` instance, launches before each test, tears down after, and exposes methods for conditional configurations. 
A test suite that re-implements any part of this is duplicating infrastructure that belongs in one place.

**Detection:**

1. **No shared base class** — flag test classes that inherit directly from `XCTestCase` and manage their own `XCUIApplication`, `setUp`, or `tearDown`
2. **Lifecycle in individual suites** — flag test classes that override `setUp`/`tearDown` to perform app launch, app termination, or state reset that should be the base class's responsibility
3. **Conditional setup not exposed by base** — flag test methods that configure launch arguments or environment variables for cross-cutting concerns (animation disabling, state reset, persistence prefill) instead of calling a named setup method on the base class
4. **Coordinator not owned by base** — flag test classes that instantiate their coordinator directly instead of receiving it from the base class

**Count:** Number of base class structure violations found.

---

### UITEST-3: Assertion Grouping

Detect tests that fragment the assertions for a single screen state across multiple test methods.

**Definition:** Navigating to a screen state — launching the app, performing a flow, triggering a transition — should happen once per state. All observable properties of that state are asserted in a single test. Splitting into `test_showsTitle`, `test_showsIcon`, `test_showsButton` runs the same expensive navigation N times to verify N independent properties that could be checked in one pass.

**Detection:**

1. **Fragmented assertions** — identify groups of test methods in the same class where:
   - Each method shares the same setup preamble (same coordinator call or navigation path to reach the same state)
   - Each method asserts only 1–2 properties of that state
   - The assertions are independent of each other (no ordering dependency)
   - Combined, they cover the observable surface of a single screen state
2. **Single-assertion tests on multi-step flows** — flag a test method that performs a coordinator flow of 3+ steps and makes only one assertion afterward, when another test in the same class performs the same flow and makes a different single assertion

**Count:** Number of fragmented assertion groups found (count groups, not individual tests).

---

### UITEST-4: Synchronization

Detect time-based waiting instead of condition-based waiting.

**Definition:**
A UI test must wait for the app to reach a state before it can interact with or assert on it.
The correct mechanism is condition-based: wait until an element exists, until a predicate is true, or until an expectation is fulfilled.
Time-based waiting (sleep, fixed delays) is always wrong — it either waits too long (wastes CI time) or too short (flaky).
Calling `waitForExistence(timeout:)` directly on an element is compliant. A wrapper method that internally calls `waitForExistence` or any other condition-based wait is also compliant — and preferred, since it centralizes the timeout constant and failure message. The violation is when nothing in the call chain waits for a condition at all.

**Detection:**

1. **Time-based waits** — flag any use of:
   - `Thread.sleep`, `Task.sleep`, `sleep()`, `usleep()`, or `DispatchQueue.asyncAfter` used as a delay before an assertion or interaction
   - These are unconditional — no element or state is being observed, only time is passing
2. **No existence check in the call chain** — flag any element interaction (tap, click, type) or assertion (XCTAssert on an element property) where nothing in the call chain first confirms the element exists:
   - Directly calling `.tap()`, `.click()`, `.value`, `.frame`, `XCTAssertTrue(element.exists)`, etc on a freshly queried element with no prior existence wait
   - Accessing an element immediately after launch, navigation, or a state transition with no condition-based wait anywhere between the transition and the access
   - Note: a helper method that internally performs a condition-based wait before returning the element is compliant — trace the call chain into the helper implementation; if the helper calls further methods, continue tracing until you find where the existence check occurs, not just the call site

**Count:** Number of synchronization violations found.

---

### UITEST-5: Typed Identifiers

Detect raw string literals used to identify UI elements.

**Definition:** 
Element queries that use string literals directly couple tests to the current identifier values and break silently on rename. 
All identifiers — whether owned by the app or assigned by the system (dialogs, panels, Dock) — must be referenced through a typed constant system.

**Detection:**

1. **Raw string queries** — flag any element query that uses a string literal directly:
   - App-owned elements: subscript syntax (`app.buttons["Label"]`), predicate with string literal, `.matching(identifier: "string")`
   - System elements: system dialogs, panels, or controls accessed by hardcoded title or identifier strings
2. **Mixed usage** — flag a test class that uses typed constants for some queries and raw strings for others — partial adoption is a smell that the raw strings will grow

**Count:** Number of typed identifier violations found.

---

### Exceptions (NOT violations):
1. **Launch performance tests** — `measure { app.launch() }` blocks that exist specifically to measure launch time
2. **Terminate-and-relaunch boundary tests** — tests that verify behavior across an intentional app termination (state restoration, crash recovery) may call launch more than once
3. **Single-method test classes** — assertion grouping only applies when 2+ methods share the same setup preamble

---

### Severity Bands:
- COMPLIANT (0 violations across all metrics)
- MINOR (any of the following):
    - 1–2 UITEST-5 violations only (isolated raw string identifiers, no other violations)
- SEVERE (any of the following):
    - 1+ UITEST-1 violations (inline flows, duplicated sequences, coordinator not composing)
    - 1+ UITEST-2 violations (no base class, lifecycle in individual suites)
    - 1+ UITEST-3 violations (fragmented assertions across tests)
    - 1+ UITEST-4 violations (time-based waits, no condition check in call chain)
    - 3+ UITEST-5 violations (pervasive raw string identifiers)
---

## Quantitative Metrics Summary
| ID       | Metric              | Threshold                                              | Severity  |
|----------|---------------------|--------------------------------------------------------|-----------|
| UITEST-0 | Exception           | Falls into exception category                          | COMPLIANT |
| UITEST-1 | Flow encapsulation  | 0 violations                                           | COMPLIANT |
| UITEST-2 | Base class structure| 0 violations                                           | COMPLIANT |
| UITEST-3 | Assertion grouping  | 0 violations                                           | COMPLIANT |
| UITEST-4 | Synchronization     | 0 violations                                           | COMPLIANT |
| UITEST-5 | Typed identifiers   | 0 violations                                           | COMPLIANT |
| UITEST-5 | Typed identifiers   | 1–2 raw string violations, all else clean              | MINOR     |
| UITEST-1 | Flow encapsulation  | 1+ inline flows or duplicated sequences                | SEVERE    |
| UITEST-2 | Base class structure| 1+ lifecycle or setup in individual suites             | SEVERE    |
| UITEST-3 | Assertion grouping  | 1+ fragmented assertion groups                         | SEVERE    |
| UITEST-4 | Synchronization     | 1+ time-based waits or unchecked element access        | SEVERE    |
| UITEST-5 | Typed identifiers   | 3+ raw string violations                               | SEVERE    |
---
