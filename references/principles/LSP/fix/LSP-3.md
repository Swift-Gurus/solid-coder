<fix id="LSP-3" name="Empty / Non-Implemented Methods">

<trigger>
A conformer implements protocol methods with empty bodies or `fatalError` /
`preconditionFailure`, breaking the protocol contract.
</trigger>

<strategy severity="MINOR">
Watch item. Consider adding a protocol extension with a no-op default implementation
for optional-behaviour methods so conformers that have no meaningful implementation
no longer need to implement the method at all.
</strategy>

<strategy severity="SEVERE">
Redesign the interface so conformers are not forced to implement methods they cannot
support. Split the protocol into narrower role protocols.
</strategy>

<diagnosis>
Read the empty/fatal methods from the findings. Identify which protocol requirements
this conformer cannot meaningfully fulfill. This always signals the protocol is too
wide for this conformer.
</diagnosis>

<todo>
**Interface redesign (SEVERE):**
- [ ] Identify which subset of protocol methods this conformer CAN implement meaningfully
- [ ] Split the protocol into narrower role protocols (one per cohesion group of methods)
- [ ] Create a composition protocol if consumers need the full combined interface:
  `protocol Full: RoleA, RoleB {}`
  — **Use `protocol`, not `typealias`** — typealiases cannot be conformed to directly
- [ ] Update the conformer to adopt only the protocols it can meaningfully implement
- [ ] Update consumers to depend on the narrowest protocol they actually need

**No-op default (MINOR):**
- [ ] Add a protocol extension with a no-op default for optional-behaviour methods
- [ ] Conformers with no meaningful implementation no longer need to declare the method

- [ ] Predict post-fix: 0 `fatalError` methods; empty methods = 0% (split path) or covered by defaults (no-op path)
</todo>

<suggested_fix_must_include>
- Split protocol definitions (narrow role protocols)
- Composition protocol if needed
- Updated conformer adopting only the protocols it supports
- Before/after showing removal of `fatalError` or empty method
</suggested_fix_must_include>

</fix>
