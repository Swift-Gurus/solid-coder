---
name: testing-code
type: code
---

# Unit Testing Coding Instructions

These are mandatory rules that must be followed when writing unit tests. Every test method you write must be validated against these rules. Run this checklist twice — once before writing (plan your approach) and once after writing (verify what you wrote).

---

## For Every Test Method You Write

<rule id="TEST-1" name="Test Isolation">
- No `static var`/`static let` mutated across tests.
- All class-level `var` properties reset in `setUp`/`init`.
- No singleton access (`.shared`, `.default`) — inject the dependency instead.
- No test references state written by another test.
- No order-dependent assertions.
Note isolation violations.
</rule>

<rule id="TEST-2" name="Test Structure">
- Does this file already contain a test suite? If yes, create a new file instead.
- No `if`/`else`/`switch`/`for`/`while` in the test body.
- No `try?`, `do { try } catch { XCTFail }`, or force unwrap — use bare `try` or `try #require`.
- No `guard let ... else { XCTFail }` — use `try #require`.
- No phase comments (`// Arrange`, `// Given`, etc.) — use blank lines.
- No assertions interleaved with actions — clear Arrange-Act-Assert order.
- No vacuous assertions — every assertion must be falsifiable by the SUT.
- No 4+ unrelated assertions — one behavior per test.
- No `Thread.sleep`/`Task.sleep` to wait for async results — use `await fulfillment(of:timeout:)`.
Note structure violations.
</rule>

<rule id="TEST-3" name="Test Naming">
- No generic names (`test1`, `testIt`, `testBasic`, `testFunction`).
- No method-name-only names (`testLogin`, `testSave`) — include condition and expected outcome.
- Name must answer: what is tested, under what condition, what should happen.
- Convention consistent with the rest of the test class.
Note naming violations.
</rule>

<rule id="TEST-4" name="Test Double Quality">
- No mocking value types, pure logic types (formatters, mappers, calculators), or simple data structures — use the real instance.
- No partial mocks (subclassing the SUT to override some methods) — inject dependencies instead.
- No verifying internal method calls — assert on observable outcomes.
- No circular mock assertions (set value on mock, assert same mock returns it).
- No stubs in integration tests — integration tests use real implementations.
Note test double violations.
</rule>

<rule id="TEST-5" name="Test Setup Complexity">
- No inline SUT construction repeated across 2+ test methods — extract to `setUp`, computed property, or factory.
- 3+ dependencies → dedicated factory type with `makeSUT()`.
Note setup complexity violations.
</rule>

<rule id="TEST-6" name="Testing Framework">
- Use `import Testing`, `@Test`, `#expect`, `#require` — not `import XCTest` / `XCTestCase` (unless UI test with `XCUIApplication`).
- No `XCTAssert*` macros — use `#expect(...)`.
- No `try XCTUnwrap` — use `try #require(...)`.
- No `XCTFail` — use `Issue.record(...)`.
Note framework violations.
</rule>

<exceptions>
- UI tests — `import XCTest` and `XCTestCase` are required for any test that uses `XCUIApplication`. Do not flag TEST-6 for UI tests.
- Integration tests — explicitly marked integration tests are exempt from TEST-1 isolation rules for real external calls. Shared mutable state is still a violation.
- Performance tests — `measure {}` blocks have different structural needs. Do not flag TEST-2 for them.
- Parameterized test loops — `for` loops that iterate test data to run the same assertion with different inputs are not a TEST-2 structure violation.
- Test helpers/fixtures in shared setUp — shared immutable fixtures reset per test are not TEST-1 isolation violations.

If the test falls into one of these exceptions, note it and do not treat it as a violation. Otherwise, validate noted violations against severity bands:
- MINOR (1-2 naming violations only, no other issues) → Proceed.
- SEVERE (any isolation, structure, test double, setup, or framework violation; 3+ naming violations) → Fix before proceeding. Use loaded fix instructions.
</exceptions>
