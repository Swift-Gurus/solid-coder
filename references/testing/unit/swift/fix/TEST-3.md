<fix id="TEST-3" name="Test Naming">

<trigger>
Generic names (`test1`, `testIt`), method-name-only names (`testLogin`, `testSave`
with no condition or expectation), or inconsistent convention across the test class.
</trigger>

<strategy severity="MINOR">
Rename tests to describe the scenario and expected outcome. Standardise convention.
</strategy>

<todo>
- [ ] Rename each violating test to the pattern: `test_<methodOrFeature>_<condition>_<expectedResult>`
  - Example: `testLogin` → `test_login_withValidCredentials_succeedsAndNavigatesToHome`
- [ ] Ensure every name answers: what is tested, under what condition, what should happen
- [ ] Remove implementation-leaking names (references to private methods or internal state)
- [ ] Standardise naming convention across the entire test class — no mixed camelCase/snake_case/`should` styles
</todo>

<suggested_fix_must_include>
- Renamed test methods showing the before/after
- Applied consistently across all tests in the class
</suggested_fix_must_include>

</fix>
