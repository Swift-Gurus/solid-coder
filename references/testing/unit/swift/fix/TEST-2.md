<fix id="TEST-2" name="Test Structure">

<trigger>
Logic in test body (if/else, loops), missing phases, multiple unrelated behaviors
in one test, vacuous assertions, sleep-based waiting, or multiple test suites in one file.
</trigger>

<strategy severity="SEVERE">
Split, restructure, and rewrite to follow strict Arrange-Act-Assert with no logic.
</strategy>

<todo>
- [ ] Extract conditional branches into separate test methods (one per branch)
- [ ] Reorder into clear Arrange → Act → Assert sections separated by blank lines (no phase comments)
- [ ] Split multi-behavior tests — one test per scenario/behavior, max 3–4 related assertions
- [ ] Add assertions to tests that verify nothing
- [ ] Replace vacuous assertions with ones that would fail if the SUT behaved incorrectly
- [ ] Fix assertion-intent mismatch — if the name says X but the assertion checks Y, rewrite the assertion to check X
- [ ] Replace `try?` with throwing `try` — mark test function as `throws`
- [ ] Replace `do { try ... } catch { XCTFail(...) }` with bare `try` — mark test as `throws`
- [ ] Replace `guard let v = optional else { XCTFail(); return }` and `optional!` with `try #require(optional)`
- [ ] Replace sleep-based waiting with `async/await` + `await fulfillment(of:timeout:)` — test doubles should fulfill expectations when called by the SUT
- [ ] For decomposed model assertions: add `Equatable` conformance to the model, then replace multiple `#expect(model.x == a)` with `#expect(model == expected)`
- [ ] Split multiple test suites in one file into separate files — one file per suite
</todo>

<suggested_fix_must_include>
- Split test methods (before: 1 test with branches; after: N tests, one per branch)
- AAA structure with blank-line separation
- `try #require` replacing guard/force-unwrap
- `await fulfillment` replacing sleep (if applicable)
</suggested_fix_must_include>

</fix>
