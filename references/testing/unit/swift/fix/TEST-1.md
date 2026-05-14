<fix id="TEST-1" name="Test Isolation">

<trigger>
Shared mutable state between tests (`static var` not reset, class-level `var` not
reset in setUp) or test interdependencies (tests that reference state from other tests).
</trigger>

<strategy severity="SEVERE">
Remove all shared state. Each test sets up its own preconditions independently.
</strategy>

<todo>
- [ ] Convert `static var` to instance `var` — static state persists across tests and cannot be reset
- [ ] Add `setUp`/`tearDown` (or `init`/`deinit` in Swift Testing) to reset all mutable instance properties before each test
- [ ] Remove singleton access (`.shared`, `.default`) — inject the dependency via init instead. If the SUT does not support injection, note it as an OCP violation.
- [ ] Break test interdependencies — each test must set up its own preconditions without reading state written by another test
- [ ] Remove `continueAfterFailure = false` combined with assertions that depend on earlier assertions passing — split into independent tests instead
</todo>

<suggested_fix_must_include>
- setUp/tearDown with fresh state initialisation
- Static vars converted to instance vars
- Independent precondition setup per test
- Before/after showing the isolation fix
</suggested_fix_must_include>

</fix>
