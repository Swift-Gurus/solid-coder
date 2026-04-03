---
name: testing
displayName: Unit Testing
category: practice
description: Test isolation, structure, naming, and test double quality analysis with direct severity scoring
tags:
  - unit-test
  - xctest
  - testing
---

# Unit Testing

> Write tests that are isolated, readable, and verify one behavior each. Tests are documentation — they should explain what the code does and why it matters.
---

## The Testing Metrics Framework

This framework provides objective scoring for unit test quality. The primary
metrics are test isolation, test structure, test naming, and test double quality
— all directly observable from test code.

## Metrics:

### TEST-1: Test Isolation

Detect tests that depend on shared mutable state or execution order.

**Definition:** An isolated test can run in any order, concurrently, and repeatedly with the same result. Shared mutable state between tests and test interdependencies break isolation.

**Detection:**

1. **Shared mutable state** — scan test class for:
   - `static var` / `static let` that is mutated across tests
   - Class-level `var` properties not reset in `setUp`/`init`
   - Singleton access (`.shared`, `.default`) without injection
2. **Test interdependencies** — look for:
   - Tests that reference results or state from other test methods
   - Tests that must run in a specific order (fragile sequencing)
   - `continueAfterFailure = false` combined with dependent assertions

**Count:** Number of isolation violations found.

### TEST-2: Test Structure

Detect tests that contain logic, lack clear phases, or verify too many behaviors at once.

**Definition:** A well-structured test follows Arrange-Act-Assert (or Given-When-Then): set up preconditions, perform one action, verify one behavior. Tests should not contain conditional logic — a test with an `if` is two tests.

**Detection:**

1. **Logic in tests** — flag any of:
   - `if` / `else` / `switch` statements in test body
   - `for` / `while` loops (except parameterized test data setup)
   - `try?` that silently swallows errors — in tests, prefer `try` (throwing)
     so failures surface as test errors with stack traces instead of being
     silently ignored (see `Examples/try-swallowing-*.swift`)
   - Conditional assertions (`if condition { XCTAssert... }`)
2. **Missing phases** — check for:
   - No clear separation between setup, action, and assertion
   - Assertions interleaved with actions (act-assert-act-assert)
   - No assertions at all (test does something but verifies nothing)
   - Phase comments (`// Arrange`, `// Act`, `// Assert`, `// Setup`,
     `// Given`, `// When`, `// Then`) — use blank lines to separate
     phases, the code structure should make them obvious
3. **Multiple behaviors** — detect:
   - Tests with 4+ unrelated assertions (testing multiple behaviors)
   - Tests that exercise multiple independent code paths that could be
     tested separately (e.g., testing validation AND persistence in one
     test when they have no dependency on each other)
4. **Sleep-based waiting** — detect:
   - `Thread.sleep`, `Task.sleep`, `sleep()`, `usleep()` used to wait
     for async operations to complete
   - Hardcoded delays to "give enough time" for a result
   - Use `async/await` test methods with `await fulfillment(of:timeout:)`
     instead — test doubles should hold expectations and fulfill them
     when called, so the test only needs to `await fulfillment`
     (see `Examples/sleep-waiting-*.swift`)

**Count:** Number of structure violations found.

### TEST-3: Test Naming

Detect tests with unclear, ambiguous, or non-descriptive names that fail to communicate intent.

**Definition:** A test name should describe the scenario and expected outcome without reading the test body. The name is documentation — it should answer: what is being tested, under what condition, and what should happen.

**Detection:**

1. **Non-descriptive names** — flag:
   - Generic names: `test1`, `testIt`, `testFunction`, `testBasic`
   - Method-name-only: `testLogin`, `testFetch`, `testSave` (no condition or expectation)
   - Implementation-leaked: names referencing private methods or internal state
2. **Missing condition or expectation** — check:
   - Name describes the method but not the scenario (e.g., `testCalculateTotal` vs `testCalculateTotal_withDiscount_appliesPercentage`)
   - Name describes setup but not the expected outcome
3. **Inconsistent convention** — detect:
   - Mixed naming styles within the same test class (some snake_case, some camelCase, some with "should")
   - No consistent pattern across the test suite

**Count:** Number of naming violations found.

### TEST-4: Test Double Quality

Detect improper use of mocks, stubs, and fakes — over-mocking, under-mocking, and brittle verification.

**Definition:** Test doubles should isolate the unit under test from its dependencies. Good test doubles are minimal (only stub what's needed), verify behavior (not implementation), and don't couple tests to internal call sequences.

**Detection:**

1. **Over-mocking** — flag:
   - Mocking value types or simple data structures (mock where a real instance works)
   - Subclassing the SUT to override some methods while testing others
     (partial mocks — e.g., overriding `validate()` to return `true` while
     testing `placeOrder()`). Test the real type; control behavior through
     injected dependencies instead
   - Mocking pure logic types (formatters, mappers, calculators, validators)
     that have no I/O, no state, and deterministic output — use the real
     implementation, it's a better test than verifying against a mock
2. **Brittle verification** — detect:
   - Verifying internal method calls instead of observable outcomes
3. **Testing mock logic instead of SUT logic** — detect:
   - Setting a value on a mock then asserting that same mock returns it
     (tests the mock, not the SUT)
   - Facades/coordinators where direct dependencies are mocked — prefer
     using real service implementations with their boundaries mocked
     (e.g., real `OrderService` with mocked network layer, not a
     `MockOrderService`)

**Count:** Number of test double quality violations found.

### TEST-5: Test Setup Complexity

Detect inline SUT construction repeated across tests.

**Definition:** Inline SUT construction repeated across test methods is
a violation regardless of dependency count. Each test should focus on
its scenario, not on assembling the SUT.

**Detection:**

1. **Repeated inline construction** — flag any test class where:
   - SUT is constructed inline in 2+ test methods
   - Same construction pattern repeated (even with 1 dependency)
2. **Dependency count** — record how many mock/stub dependencies the
   SUT requires. This informs fix strategy (see `fix/instructions.md`).

**Count:** Number of setup complexity violations found.

### Exceptions (NOT violations):
1. **Integration tests** — tests explicitly marked as integration (file name, class name, or annotation) are exempt from isolation rules for real external calls. They still must not have shared mutable state.
2. **Snapshot/UI tests** — different testing paradigm, not governed by these rules
3. **Performance tests** — `measure {}` blocks have different structural needs
4. **Parameterized test loops** — `for` loops that iterate test data to run the same assertion with different inputs are not a structure violation
5. **Test helpers/fixtures in shared setUp** — shared immutable fixtures reset per test are not isolation violations

### Severity Bands:
- COMPLIANT (0 violations across all metrics)
- MINOR (any of the following):
    - 1-2 naming violations only (no isolation/structure/double/setup issues)
    - Inconsistent naming convention but names are still descriptive
- SEVERE (any of the following):
    - 1+ isolation violations (shared state, test dependencies)
    - 1+ structure violations (logic in tests, missing phases, multiple behaviors)
    - 3+ naming violations
    - 1+ test double quality violations (over-mocking, brittle verification)
    - 1+ setup complexity violations (repeated inline SUT construction)
---

## Quantitative Metrics Summary
| ID     | Metric              | Threshold                                    | Severity  |
|--------|---------------------|----------------------------------------------|-----------|
| TEST-0 | Exception           | Falls into exception category                | COMPLIANT |
| TEST-1 | Isolation           | 0 violations                                 | COMPLIANT |
| TEST-2 | Structure           | 0 violations                                 | COMPLIANT |
| TEST-3 | Naming              | 0 violations                                 | COMPLIANT |
| TEST-4 | Test doubles        | 0 violations                                 | COMPLIANT |
| TEST-5 | Setup complexity    | 0 violations                                 | COMPLIANT |
| TEST-3 | Naming              | 1-2 naming violations, all else clean        | MINOR     |
| TEST-1 | Isolation           | 1+ shared state or test dependencies         | SEVERE    |
| TEST-2 | Structure           | 1+ logic, missing phases, or multi-behavior  | SEVERE    |
| TEST-3 | Naming              | 3+ naming violations                         | SEVERE    |
| TEST-4 | Test doubles        | 1+ over-mock, brittle verify, or mock logic  | SEVERE |
| TEST-5 | Setup complexity    | 1+ repeated inline SUT construction          | SEVERE |
---
