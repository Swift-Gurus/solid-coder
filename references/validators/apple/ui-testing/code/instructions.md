---
name: uitesting-code
type: code
---

# UI Testing Coding Instructions

These are mandatory rules that must be followed when writing UI tests. Check each rule before writing — if any gate fails, stop and redesign before proceeding.

---

<rule id="UITEST-1" name="Encapsulate Flows in Coordinators">
Before writing any sequence of 3 or more UI interactions inside a test method:
- Extract the sequence into a named coordinator type that holds an `app` reference and exposes named methods for reaching app states.
- Before creating a new coordinator → check if a coordinator for a prior screen already exists. Compose it — hold it as a dependency and delegate to it — do not re-implement its steps.
- Every coordinator method that contains assertions must accept `file: StaticString = #file, line: UInt = #line` and pass them to every assertion and helper call. Without this, failures report inside the coordinator, not at the test call site.
- Coordinators never create `XCUIApplication()` internally — always receive `app` via `init(app: XCUIApplication)`.
</rule>

<rule id="UITEST-2" name="Use the Shared Base Class">
Before creating any test class:
- Inherit from the project's shared base class, not directly from `XCTestCase`.
- Never manage `XCUIApplication`, `setUp`, or `tearDown` in an individual test class — these are base class responsibilities.
- Never configure launch arguments or environment variables (animation disabling, state reset, persistence prefill) directly in test methods — call named setup methods on the base class instead.
- `continueAfterFailure = false` must be set in the base class `setUp`. Without it, failed assertions cascade into misleading subsequent failures.

When writing app code that will be exercised by UI tests:
- All persistent state must go through `UserDefaults(suiteName:)`, not `.standard` — a named suite is required for per-test state reset.
- Any reset logic that checks for a launch argument must be wrapped in `#if DEBUG` so it never compiles into release builds.
</rule>

<rule id="UITEST-3" name="Assert All Properties of a State in One Test">
Before writing a test that navigates to a screen state:
- Assert ALL observable properties of that state in this one test — title, icons, buttons, labels — everything visible.
- Do NOT write separate `test_showsTitle`, `test_showsIcon`, `test_showsButton` methods that each re-run the same expensive navigation to assert one property. Group them.
</rule>

<rule id="UITEST-4" name="Condition-Based Waiting Only">
Before interacting with or asserting on any UI element:
- Never use `Thread.sleep`, `Task.sleep`, `sleep()`, `usleep()`, or `DispatchQueue.asyncAfter` as a delay before an interaction or assertion.
- Always wait for element existence first via `waitForExistence(timeout:)` or an equivalent condition-based wait — either directly or through a helper that internally performs the check.
- `app.activate()` does NOT simulate a Dock icon click and does NOT trigger `applicationShouldHandleReopen`. To simulate a Dock click: `XCUIApplication(bundleIdentifier: "com.apple.dock").icons[AppConstants.appName].click()`.
</rule>

<rule id="UITEST-5" name="Typed Identifiers Only">
Before querying any UI element:
- Never use raw string literals — no `app.buttons["Label"]`, no `.matching(identifier: "string")`, no hardcoded system dialog titles.
- Always reference identifiers through a typed constant system.
- Applies to both app-owned elements and system elements (dialogs, panels, Dock).
</rule>

<exceptions>
- Launch performance tests — `measure { app.launch() }` blocks that exist specifically to measure launch time.
- Terminate-and-relaunch boundary tests — tests that verify behavior across an intentional app termination (state restoration, crash recovery) may launch more than once.
- Single-method test classes — assertion grouping (UITEST-3) only applies when 2+ test methods share the same navigation preamble.

Validate noted violations:
- MINOR (1–2 UITEST-5 raw string violations only, nothing else) → Proceed.
- SEVERE (any UITEST-1/2/3/4 violation, OR 3+ UITEST-5 violations) → Do not write it this way. Use loaded fix instructions.
</exceptions>
