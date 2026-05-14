<fix id="TEST-6" name="Testing Framework">

<trigger>
`import XCTest` / `XCTestCase` used for unit or integration tests that do not use
`XCUIApplication`. `XCTAssert*` macros used outside UI test context.
</trigger>

<strategy severity="SEVERE">
Migrate to Swift Testing. XCTest is reserved for UI tests that use `XCUIApplication`.
</strategy>

<todo>
- [ ] Replace `import XCTest` with `import Testing`
- [ ] Replace `class FooTests: XCTestCase` with `struct FooTests` annotated with `@Suite`
- [ ] Replace `func testSomething()` with `@Test func something()` (drop `test` prefix, rename for clarity)
- [ ] Replace assertions:
  - `XCTAssertEqual(a, b)` → `#expect(a == b)`
  - `XCTAssertTrue(x)` → `#expect(x)`
  - `XCTAssertFalse(x)` → `#expect(!x)`
  - `XCTAssertNil(x)` → `#expect(x == nil)`
  - `XCTAssertNotNil(x)` → `#expect(x != nil)`
  - `try XCTUnwrap(optional)` → `try #require(optional)`
  - `XCTFail("message")` → `Issue.record("message")`
  - `XCTSkipIf` / `XCTSkipUnless` → `try #require(condition)`
- [ ] Replace lifecycle methods:
  - `setUp()` / `tearDown()` → `init()` / `deinit`
  - `setUpWithError()` / `tearDownWithError()` → `init() throws` / `deinit`
</todo>

<suggested_fix_must_include>
- Full before/after file showing the XCTest → Swift Testing migration
- All assertion replacements
- Renamed test methods (no `test` prefix)
</suggested_fix_must_include>

</fix>
