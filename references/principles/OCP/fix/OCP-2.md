<fix id="OCP-2" name="Testability">

<trigger>
1+ untestable dependencies — injected dependencies that cannot be substituted in tests
(no protocol, `final` class with no subclassing path).
</trigger>

<strategy severity="MINOR">
No structural change required. Document that the dependency is testable but flagged.
Consider adding a protocol if the dependency is expected to vary.
</strategy>

<strategy severity="SEVERE">
Make each untestable dependency substitutable by abstracting it behind a protocol or
ensuring it can be subclassed.
</strategy>

<diagnosis>
Read the untestable dependencies from the findings. For each:
- Is it `final` with no protocol? → introduce a protocol
- Is it a class that can be subclassed? → document as testable via subclassing (may downgrade to MINOR)
- Is it a value type with no protocol? → protocol + extension conformance
</diagnosis>

<todo>
- [ ] For each untestable dependency:
  - [ ] Check if the class is `final` — if not, it CAN be subclassed in tests; verify if this resolves testability
  - [ ] If still untestable: create a protocol covering only the methods the original class calls on this dep
  - [ ] Add extension conformance on the existing type (preferred over wrapping)
  - [ ] Update the original class to hold the protocol type instead of the concrete type
  - [ ] Verify: can a test substitute a mock/stub conforming to the protocol?
- [ ] Predict post-fix: 0 untestable dependencies; all direct deps are protocol-typed or subclassable
</todo>

<suggested_fix_must_include>
- Protocol definition covering the methods the caller uses
- Extension conformance on the existing type (if applicable)
- Modified original class holding the protocol-typed property
- A note showing how a test mock would conform to the protocol
</suggested_fix_must_include>

</fix>
