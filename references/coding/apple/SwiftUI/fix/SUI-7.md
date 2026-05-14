<fix id="SUI-7" name="Accessibility Identifier on Containers">

<trigger>
A container view (`HStack`, `VStack`, `ZStack`, `List`, `ScrollView`, `Form`,
`LazyVStack`, etc.) has `.accessibilityIdentifier(...)` but no preceding
`.accessibilityElement(children:)`. The container is invisible to the accessibility
tree and XCUI tests will fail to find it.
</trigger>

<strategy severity="SEVERE">
Insert `.accessibilityElement(children:)` immediately before `.accessibilityIdentifier(...)`
for each flagged container.
</strategy>

<todo>
- [ ] For each flagged container, choose the `children:` strategy:
  - `.contain` — children remain individually accessible (default, most common for test containers)
  - `.combine` — children merge into a single accessible element (for semantic units like label + value pairs)
  - `.ignore` — children hidden from accessibility (for decorative containers only)
- [ ] Insert `.accessibilityElement(children: .contain)` (or chosen strategy) immediately BEFORE the existing `.accessibilityIdentifier(...)` in the modifier chain
- [ ] Exception: if the container is a custom view that already applies `.accessibilityElement(children:)` internally, external callers adding `.accessibilityIdentifier(...)` are already compliant
</todo>

<suggested_fix_must_include>
- Before/after of the modifier chain showing `.accessibilityElement` inserted
- Rationale for the chosen `children:` strategy
</suggested_fix_must_include>

</fix>
