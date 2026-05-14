<fix id="TEST-4" name="Test Double Quality">

<trigger>
Over-mocking (mocking value types, pure logic, or partial SUT mocks), brittle
interaction verification, circular mock assertions, or stubs in integration tests.
</trigger>

<strategy severity="SEVERE">
Use real instances where possible. Assert on observable outcomes, not internal calls.
</strategy>

<todo>
**Over-mocking:**
- [ ] Replace mocks of value types and pure logic types (formatters, mappers, calculators, validators) with real instances — deterministic output makes them better test subjects than mocks
- [ ] Replace partial mocks (SUT subclass overriding some methods) with proper dependency injection — test the real type, control behavior through injected dependencies

**Brittle verification:**
- [ ] Replace `verify(mock.method was called)` assertions with assertions on SUT output/state

**Circular mock assertions:**
- [ ] Remove tests that set a value on a mock then assert the mock returns it — this tests the mock, not the SUT

**Facades/coordinators:**
- [ ] Use real service implementations with their boundaries mocked (e.g. real `OrderService` with mocked network), not a `MockOrderService`

**Stubs in integration context:**
- [ ] Replace stubs with real implementations. Integration tests must use real types. Put any environment setup in test setUp instead.
</todo>

<suggested_fix_must_include>
- Real instance replacing unnecessary mock
- State-based assertion replacing interaction verification
- Before/after showing the test double replaced or removed
</suggested_fix_must_include>

</fix>
