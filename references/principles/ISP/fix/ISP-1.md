<fix id="ISP-1" name="Protocol Width">

<trigger>
Protocol width exceeds threshold — too many methods/properties force all conformers
to implement an oversized contract.
</trigger>

<strategy severity="MINOR">
Watch item. Document intent. Consider a future split if a new low-coverage conformer
appears. Width 6-8 with all conformer coverage ≥ 60% does not require action now.
</strategy>

<strategy severity="SEVERE">
Split the protocol along cohesion boundaries into narrower role protocols.
Width > 8 is an unambiguous split signal.
</strategy>

<diagnosis>
Read the protocol width from findings. Count the method/property groups that naturally
cluster together. Each cluster is a candidate role protocol.
</diagnosis>

<todo>
- [ ] Identify cohesion clusters in the protocol's methods (which methods are always used together by conformers?)
- [ ] Define narrow role protocols — one per cluster:
  - Name each after the role it represents (e.g. `UserReading`, `UserWriting`)
  - Include only the methods belonging to that cluster
- [ ] Create a composition protocol if existing consumers need the combined interface:
  `protocol UserManaging: UserReading, UserWriting {}`
  — **Use `protocol`, not `typealias`** — typealiases cannot be conformed to, breaking decorators
- [ ] Update each conformer: replace the wide protocol conformance with only the narrow protocols it meaningfully implements
- [ ] Update consumers: replace the wide protocol type with the narrowest protocol that covers their usage
- [ ] Predict post-fix: each narrow protocol width ≤ 5; each conformer coverage ≥ 80%
</todo>

<suggested_fix_must_include>
- Narrow protocol definitions (one per cluster)
- Composition protocol (if needed for existing consumers)
- Updated conformer declarations
- Updated consumer signatures using narrow protocols
- Before/after showing width reduction
</suggested_fix_must_include>

</fix>
