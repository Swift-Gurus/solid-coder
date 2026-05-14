<fix id="SRP-1" name="Verb Count">

<trigger>
3+ distinct verbs (responsibilities) detected in the unit.
</trigger>

<strategy severity="MINOR">
Rename methods for clarity — no extraction. Document the single responsibility more
clearly. No structural change required.
</strategy>

<strategy severity="SEVERE">
Extract verb clusters into dedicated types behind protocols. Each cluster of related
verbs serving the same stakeholder or concern becomes a new type.
</strategy>

<diagnosis>
List every verb the class performs (what it actually does, not just method names).
Group verbs by which stakeholder or concern they serve.
Each verb cluster with a distinct stakeholder is a candidate for extraction.
</diagnosis>

<todo>
- [ ] Identify verb clusters from the findings' verb list
- [ ] For each cluster: create a protocol (name reflects the role, e.g. `UserPersisting`, `UserAuthenticating`)
- [ ] Create an extracted type implementing the protocol (owns only the variables it needs)
- [ ] Update the original class: inject the extracted type via `init`, delegate calls
- [ ] **Facade check**: after extraction the original class should have all-protocol deps and pure delegation — no internal logic or construction. Adjust if not.
- [ ] Predict post-fix: 1-2 verbs per type, 1 cohesion group per type, 1 stakeholder per type
</todo>

<suggested_fix_must_include>
- Protocol definition with method signatures
- Extracted type with `init` and moved methods
- Modified original class with injected dependency
- Before/after of key delegating methods
</suggested_fix_must_include>

</fix>
