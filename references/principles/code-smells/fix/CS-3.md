<fix id="CS-3" name="No Inline Type Definitions Inside Function Scopes">

<trigger>
One or more class, struct, enum, interface, or protocol definitions found inside a
function or method body rather than at module/file scope.
</trigger>

<strategy severity="SEVERE">
Move each inline type definition to module/file scope with a descriptive name
that reflects its role. If the type is only used at one call site, prefer:

1. An existing mock framework (e.g. MagicMock in Python, protocol conformance in Swift)
   over a custom named type when the type has no invariants to assert.
2. A named test double at file scope when the type captures recording behaviour
   (e.g. CapturingResolver, FakeReader) — name it after what it does, not where it's used.
</strategy>

<diagnosis>
Scan each function and method body for nested class, struct, enum, interface, or protocol
declarations. For each found: identify what role it plays (spy, stub, fake, helper) and
whether an existing framework type or a file-scoped named type can replace it.
</diagnosis>

<todo>
- [ ] List all inline type definitions from the findings
- [ ] For each: determine the type's role (recording spy, behaviour stub, data helper)
- [ ] If a mock framework can cover it: replace with MagicMock / protocol conformance
- [ ] If custom recording logic is needed: extract to a named file-scoped class
  - Name it after its role: `CapturingResolver`, `FakeFileReader`, `RecordingReviewer`
  - Move all fields and methods intact
- [ ] Update the call site to instantiate the extracted type
- [ ] Verify: no remaining class/struct/enum declarations inside function bodies
</todo>

<suggested_fix_must_include>
- File-scoped replacement type with its full definition
- Updated call site showing instantiation of the extracted type
- Confirmation that no inline type definitions remain in the function
</suggested_fix_must_include>

</fix>
