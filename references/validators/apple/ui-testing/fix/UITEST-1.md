<fix id="UITEST-1" name="Flow Encapsulation">

<trigger>
Navigation logic (3+ UI interactions to reach a state) is inlined in test methods
or duplicated across multiple tests without a coordinator.
</trigger>

<strategy severity="SEVERE">
Extract each navigation sequence into a named coordinator type. Compose coordinators
— never re-implement prior-screen steps.
</strategy>

<todo>
- [ ] For each duplicated or inlined navigation sequence:
  - Create a coordinator struct named after the screen/flow it navigates to
  - The coordinator holds `app: XCUIApplication` as a stored property (passed via `init(app:)`, never created internally)
  - Each navigation sequence becomes a named method on the coordinator
  - Every coordinator method containing assertions must accept `file: StaticString = #file, line: UInt = #line` and forward them to all assertions and helper calls
- [ ] For coordinators that duplicate prior-screen steps:
  - Add the prior-screen coordinator as a stored property
  - Delegate all prior-screen navigation to it — do not copy steps
- [ ] Update test methods to call coordinator methods instead of inline interactions
</todo>

<suggested_fix_must_include>
- Coordinator struct with `app: XCUIApplication` property
- Named flow methods with `file:line:` parameters
- Composition example showing coordinator holding and delegating to a prior-screen coordinator
- Before/after of a test method using the coordinator
</suggested_fix_must_include>

</fix>
