<fix id="UITEST-4" name="Synchronization">

<trigger>
Time-based waiting (`Thread.sleep`, `Task.sleep`, fixed delays) used before
interactions or assertions, OR UI elements accessed without any prior existence check.
</trigger>

<strategy severity="SEVERE">
Replace all time-based waits with condition-based waits. Every element interaction
must be preceded by an existence check in the call chain.
</strategy>

<todo>
**If a typed helper system already exists (e.g. `getButton(_:)`, `getGroup(_:)`):**
- [ ] Replace each unguarded element access with the appropriate typed helper
- [ ] Replace each time-based wait with the helper that waits for the relevant element

**If no helper system exists — create helpers on `XCUIElement` (not `XCUIApplication`):**
- [ ] Create extension methods on `XCUIElement` (works on both app root and sub-elements):
  ```swift
  extension XCUIElement {
      @discardableResult
      func getButton(_ identifier: String, file: StaticString = #file, line: UInt = #line) -> XCUIElement {
          let element = buttons[identifier]
          XCTAssertTrue(element.waitForExistence(timeout: UITestConstants.defaultTimeout),
                        "Button '\(identifier)' did not appear", file: file, line: line)
          return element
      }
  }
  ```
- [ ] Define `defaultTimeout` as a single shared constant — never scatter literal timeout values
- [ ] Replace all `Thread.sleep`/`Task.sleep` with appropriate helper calls
- [ ] Replace all unguarded element accesses with helper calls

</todo>

<suggested_fix_must_include>
- `XCUIElement` extension with helper methods and `defaultTimeout` constant
- Before/after showing sleep replaced with condition-based wait
- Usage on both app root (`app.getButton(...)`) and sub-element (`dialog.getButton(...)`)
</suggested_fix_must_include>

</fix>
