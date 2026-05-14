<fix id="TEST-5" name="Test Setup Complexity">

<trigger>
SUT constructed inline in 2+ test methods — same construction pattern repeated
regardless of dependency count.
</trigger>

<strategy severity="SEVERE">
Extract SUT construction. For 3+ dependencies use a dedicated Factory type.
</strategy>

<todo>
**Fewer than 3 dependencies:**
- [ ] Extract SUT construction to a `var sut` computed property or `setUp` method shared by all tests in the class

**3 or more dependencies:**
- [ ] Create a dedicated SUT Factory type:
  - Holds all mocks as stored properties with sensible defaults
  - Exposes `makeSUT()` → returns configured SUT
  - Tests access SUT via: `var sut: SUTType { factory.makeSUT() }`

**3+ dependencies AND different mock configurations per test:**
- [ ] Add builder methods to the factory (use `@discardableResult` for chainability):
  - `factory.withFailingNetwork()`, `factory.withEmptyCache()`, etc.
  - Each test declares only the condition it varies — all others use defaults
</todo>

<suggested_fix_must_include>
- Factory type with mock properties and `makeSUT()`
- Builder methods for varying conditions (if applicable)
- Before/after showing inline construction replaced with factory usage
</suggested_fix_must_include>

</fix>
