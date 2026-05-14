<fix id="UITEST-2" name="Base Class Structure">

<trigger>
Test suites manage their own app lifecycle (launch, teardown, launch arguments)
instead of inheriting from a shared base class.
</trigger>

<strategy severity="SEVERE">
Create a generic base class that owns the app lifecycle and coordinator. All test
suites inherit from it — none manage their own setUp/tearDown.
</strategy>

<todo>
- [ ] Create `BaseUITestCase<Coordinator: FlowCoordinating>` open class:
  - `app: XCUIApplication` and `coordinator: Coordinator` as non-optional properties
  - Launch app in `setUpWithError` (or async `setUp`) — once, consistently, with all required launch arguments applied
  - Terminate and nil app in `tearDownWithError`
  - `continueAfterFailure = false` in setUp
  - Expose named methods for each launch configuration variant:
    - `launchWithCleanState()`, `launchWithPrefilledData(...)`, `launchWithAnimationsDisabled()`
  - Test methods call these named methods — never set `launchArguments`/`launchEnvironment` directly
- [ ] Update all test classes to inherit from the base class with their coordinator type
- [ ] Remove all `setUp`/`tearDown` overrides from individual suites that duplicate base class responsibilities
</todo>

<suggested_fix_must_include>
- `BaseUITestCase` class with generic coordinator, setUp/tearDown, named launch configuration methods
- Updated test class declaration showing inheritance
- Before/after showing removal of inline setUp from individual suite
</suggested_fix_must_include>

</fix>
