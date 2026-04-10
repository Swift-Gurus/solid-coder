---
name: uitesting-fix
type: fix
input_schema: PRINCIPLE_FOLDER_ABSOLUTE_PATH/review/output.schema.json
output_schema: output.schema.json
---

### Phase 0: Load Context

- [ ] **0.1 Read the review findings JSON** (provided as structured input_schema)
- [ ] **0.2 Read the source file** (provided as input)

#### Phase 1: Determine Fix Strategy

- [ ] **1.1 Read `scoring.final_severity` from findings**
    - MINOR → identifier fixes only (replace raw strings with typed constants)
    - SEVERE → structural fixes based on which metrics triggered

- [ ] **1.2 Identify which metrics triggered the severity**
    - UITEST-1 (flow encapsulation) → Extract Coordinator pattern
    - UITEST-2 (base class structure) → Extract Base Class pattern
    - UITEST-3 (assertion grouping) → Merge Assertions pattern
    - UITEST-4 (synchronization) → Replace Time-Based Wait pattern
    - UITEST-5 (typed identifiers) → Replace Raw Strings pattern; if no identifier system exists → Create Identifier System pattern

#### Phase 2: Identify Suggestions

- [ ] **2.1 Analyze findings** — read metrics tables from review output
- [ ] **2.2 Propose suggestion** — which tests/flows to restructure
- [ ] **2.3 Create todo items** — concrete actionable steps:

    - [ ] For UITEST-1 (flow encapsulation):
        - For each duplicated or inlined navigation sequence:
            - Extract into a coordinator struct named after the screen or flow it navigates to
            - The coordinator holds `app: XCUIApplication` as a stored property
            - Each navigation sequence becomes a named method on the coordinator
            - Methods accept `file: StaticString = #file` and `line: UInt = #line` and forward them to all assertions, so failures report at the call site
        - For coordinators that duplicate prior-screen steps:
            - Add the prior-screen coordinator as a stored property
            - Delegate all prior-screen navigation to it (do not copy steps)

    - [ ] For UITEST-2 (base class structure):
        - Create a generic `BaseUITestCase<Coordinator: FlowCoordinating>` open class that:
            - Owns `app: XCUIApplication` and `coordinator: Coordinator` as non-optional properties
            - Launches the app in `setUpWithError` (or async `setUp`) — once, consistently, with all required launch arguments applied
            - Terminates and nils the app in `tearDownWithError`
            - Exposes named methods for each launch configuration variant (e.g., `launchWithCleanState()`, `launchWithPrefilledData(...)`, `launchWithAnimationsDisabled()`) — test methods call these, never set `launchArguments` or `launchEnvironment` directly
        - Update all test classes to inherit from the base class with their coordinator type
        - Remove all `setUp`/`tearDown` overrides from individual suites that duplicate base class responsibilities

    - [ ] For UITEST-3 (assertion grouping):
        - For each fragmented group:
            - Merge all methods in the group into one test method
            - Name it after the screen state: `test_<state>_<allPropertiesDescription>` (e.g., `test_launchWithNoData_showsWelcomeScreenWithBrandingAndEmptyState`)
            - Assert all properties of that state in sequence
            - Delete the individual methods
        - Keep tests separate only when they have different preconditions or when one assertion's failure would mask a genuinely independent behavior

    - [ ] For UITEST-4 (synchronization):
        - For each time-based wait:
            - Replace with a condition-based wait on the element or state that signals readiness
            - The wait should observe a specific element or predicate — not a fixed duration

        **If a typed helper system already exists** (e.g. `getButton(_:)`, `getGroup(_:)`):
        - Replace each unguarded element access with the appropriate typed helper
        - Replace each time-based wait with the helper that waits for the relevant element

        **If no helper system exists:**
        - Create helpers on `XCUIElement` — not `XCUIApplication` — so they can be called on any element (app root, window, dialog, or any sub-element):
            - Each method accepts a typed identifier (or string if no identifier system exists yet)
            - Each method calls `waitForExistence(timeout: defaultTimeout)` before returning the element
            - Each method fails the test at the call site using `file: StaticString = #file, line: UInt = #line`
            - Define a `defaultTimeout` constant shared across all helpers — never scatter literal timeout values
            - Since `XCUIApplication` is a subclass of `XCUIElement`, helpers on `XCUIElement` work on both the app and any sub-element (e.g. `dialog.getButton(...)`)
          ```swift
          extension XCUIElement {
              @discardableResult
              func getButton(
                  _ identifier: String,
                  file: StaticString = #file,
                  line: UInt = #line
              ) -> XCUIElement {
                  let element = buttons[identifier]
                  XCTAssertTrue(
                      element.waitForExistence(timeout: UITestConstants.defaultTimeout),
                      "Button '\(identifier)' did not appear",
                      file: file, line: line
                  )
                  return element
              }
          }

          // Called on app root: app.getButton("open")
          // Called on sub-element: dialog.getButton("confirm")
          ```
        - Replace all unguarded accesses and time-based waits with the new helpers

    - [ ] For UITEST-5 (typed identifiers) — two sub-cases:

        **If a typed identifier system already exists:**
        - Replace each raw string query with the typed constant equivalent
        - For system elements (dialogs, panels), add the system-assigned identifiers to the catalogue alongside app-owned ones

        **If no typed identifier system exists:**
        - Create a typed identifier catalogue:
            - Define a nested enum hierarchy reflecting the screen/component structure
            - Each leaf case produces the string value used as the accessibility identifier
            - Example structure:
              ```swift
              enum AccessibilityID {
                  enum WelcomeScreen {
                      static let appTitle = "welcome.appTitle"
                      static let openProjectButton = "welcome.openProjectButton"
                  }
                  enum FilePicker {
                      static let panel = "open-panel"          // system-assigned
                      static let openButton = "open-panel.open" // system-assigned
                  }
              }
              ```
            - System-assigned identifiers for dialogs and panels must be catalogued here too — no raw string for any system element at a call site
        - Set `accessibilityIdentifier` in the production views using the same constants from the catalogue
        - Replace all raw string queries in tests with the typed constants

#### Phase 3: Write suggested_fix

- [ ] **3.1 Write full code snippets** showing:
    - For UITEST-1: coordinator struct with `app` property, named flow methods, composition example
    - For UITEST-2: `BaseUITestCase` with generic coordinator, setUp/tearDown, conditional setup methods; updated test class declaration
    - For UITEST-3: merged test method with all assertions; before (N separate tests) and after (1 grouped test)
    - For UITEST-4: condition-based replacement for each time-based wait; helper method wrapping existence check
    - For UITEST-5: typed identifier catalogue structure; before/after query examples
- [ ] **3.2 Predict post-fix metrics** (violation counts per metric after applying fix)

#### Phase 4: Generate Output

- [ ] **4.1 Produce JSON matching output schema**
    - [ ] 4.1.1 Fill `suggested_fix` with full text + code snippets from Phase 3
    - [ ] 4.1.2 Fill `todo_items` with actionable steps from Phase 2.3
    - [ ] 4.1.3 Fill `verification` with predicted metrics from Phase 3.2
    - [ ] 4.1.4 Fill `addresses` with finding IDs this suggestion resolves

#### Constraints
- Include full code snippets — coordinators, base class, merged tests, identifier catalogue, before/after
- Todo items must be concrete and implementable
- Preserve test coverage — merging tests must not reduce what is verified
- Coordinator composition is always preferred over step duplication
- When no identifier system exists, the fix must include creating one — not just replacing strings inline
