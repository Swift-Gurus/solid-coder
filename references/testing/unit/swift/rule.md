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
   - `do { try ... } catch { XCTFail(...) }` — wrapping a throwing call in a
     do-catch and manually calling `XCTFail` in the catch block loses the
     original error and stack trace, adds boilerplate, and hides the real
     failure reason; mark the test function as `throws` and use bare `try`
     instead — XCTest records the thrown error automatically with full context
   - `guard let value = optional else { XCTFail(...); return }` or
     `guard let value = optional else { Issue.record(...); return }` — control
     flow to unwrap optionals adds logic to the test body and swallows the
     failure location; use `try #require(optional)` so the test propagates
     the error naturally with full context
   - Force unwrap (`!`) on optional values produced by the system under test —
     crashes instead of recording a test failure with a useful message; use
     `try #require(optional)` instead
   - Conditional assertions (`if condition { XCTAssert... }`)
2. **Missing phases** — check for:
   - No clear separation between setup, action, and assertion
   - Assertions interleaved with actions (act-assert-act-assert)
   - No assertions at all (test does something but verifies nothing)
   - **Vacuous assertions** — assertion exists but is always true regardless
     of SUT behavior. The assertion does not constrain the result to a
     specific expected value. Signals: assertion uses a tautology,
     assertion checks a type that's always valid, assertion compares
     the same value to itself, assertion checks a condition that cannot
     fail given the setup
   - **Assertion-intent mismatch** — test name or description claims to
     verify a specific behavior but assertions check something unrelated
     or weaker. Read the assertion, not the name — if the assertion
     doesn't prove what the test claims, it's a violation
   - Phase comments (`// Arrange`, `// Act`, `// Assert`, `// Setup`,
     `// Given`, `// When`, `// Then`) — use blank lines to separate
     phases, the code structure should make them obvious
3. **Multiple behaviors** — detect:
   - Tests with 4+ unrelated assertions (testing multiple behaviors)
   - Tests that exercise multiple independent code paths that could be
     tested separately (e.g., testing validation AND persistence in one
     test when they have no dependency on each other)
   - Decomposed model assertions — asserting individual properties (`model.text == x`,
     `model.number == y`) when a single whole-model comparison would cover all of
     them; prefer `#expect(model == expected)` which verifies the entire model in
     one assertion and produces a full diff on failure
   - Model not conforming to `Equatable` when it is used in assertions — if a model
     lacks `Equatable` conformance, the test is forced into field-by-field comparisons;
     flag the missing conformance as the root cause
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
4. **Stub in integration context** — detect:
   - Test named or categorized as "integration" but injects stubs/mocks
     for the component under test. Integration tests must use real
     implementations — stubs are for unit test isolation only
   - Test claims to validate real external behavior (real shell, real
     file system, real network) but substitutes the dependency with a
     test double

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

### TEST-6: Testing Framework

Detect use of XCTest in non-UI test files.

**Definition:** Unit and integration tests must use Swift Testing (`import Testing`, `@Test`, `#expect`, `#require`). XCTest (`import XCTest`, `XCTestCase`) is reserved for UI tests that use `XCUIApplication`. Swift Testing produces clearer failure messages, supports parameterized tests natively, and eliminates the `XCTestCase` subclass requirement.

**Detection:**

1. **XCTest in non-UI test files** — flag any file that:
   - Contains `import XCTest` and does NOT also import or use `XCUIApplication`
   - Defines a class inheriting from `XCTestCase` for unit or integration tests
   - Uses `XCTAssert*`, `XCTUnwrap`, `XCTFail` macros outside of UI test context
2. **XCTest assertion macros** — flag in unit test context:
   - `XCTAssertEqual`, `XCTAssertTrue`, `XCTAssertNil`, etc. → use `#expect(...)`
   - `XCTUnwrap` / `try XCTUnwrap(optional)` → use `try #require(optional)`
   - `XCTFail(...)` → use `Issue.record(...)`
   - `XCTSkipIf`, `XCTSkipUnless` → use `try #require(condition)`

**Count:** Number of framework violations found.

---

### Exceptions (NOT violations):
1. **UI tests** — `import XCTest` and `XCTestCase` are required for any test that uses `XCUIApplication`. UI tests cannot use Swift Testing.
2. **Integration tests** — tests explicitly marked as integration (file name, class name, or annotation) are exempt from isolation rules for real external calls. They still must not have shared mutable state.
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
    - 1+ framework violations (XCTest used in non-UI test files)
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
| TEST-6 | Testing framework   | 0 violations                                 | COMPLIANT |
| TEST-3 | Naming              | 1-2 naming violations, all else clean        | MINOR     |
| TEST-1 | Isolation           | 1+ shared state or test dependencies         | SEVERE    |
| TEST-2 | Structure           | 1+ logic, missing phases, or multi-behavior  | SEVERE    |
| TEST-3 | Naming              | 3+ naming violations                         | SEVERE    |
| TEST-4 | Test doubles        | 1+ over-mock, brittle verify, or mock logic  | SEVERE    |
| TEST-5 | Setup complexity    | 1+ repeated inline SUT construction          | SEVERE    |
| TEST-6 | Testing framework   | 1+ XCTest usage in non-UI test files         | SEVERE    |
---
