<fix id="UITEST-3" name="Assertion Grouping">

<trigger>
Multiple test methods navigate to the same screen state and each asserts only 1–2
properties. The same expensive navigation runs N times instead of once.
</trigger>

<strategy severity="SEVERE">
Merge all methods in a fragmented group into one test that asserts all observable
properties of that state in a single navigation pass.
</strategy>

<todo>
- [ ] For each fragmented group (methods sharing the same navigation preamble):
  - Merge all methods into one test method
  - Name it after the screen state: `test_<state>_showsExpectedUI` or `test_<state>_<allPropertiesDescription>`
  - Assert ALL observable properties of that state in sequence (title, icons, buttons, labels — everything visible)
  - Delete the individual single-assertion methods
- [ ] Keep tests separate only when:
  - They have genuinely different preconditions, OR
  - One assertion's failure would mask a genuinely independent behavior
</todo>

<suggested_fix_must_include>
- Before: N separate test methods each navigating to the same state
- After: 1 merged test method with all assertions
- Naming convention showing the screen state
</suggested_fix_must_include>

</fix>
