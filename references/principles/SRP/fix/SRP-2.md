<fix id="SRP-2" name="Cohesion Groups">

<trigger>
2+ cohesion groups detected — methods use disjoint sets of instance variables.
</trigger>

<strategy severity="SEVERE">
Full two-phase extraction. Each cohesion group becomes its own type behind a protocol.
No MINOR path — disjoint variable sets are an unambiguous split signal.
</strategy>

<diagnosis>
Read the cohesion groups from the findings (each group: methods + the variables they touch).
Each group is a candidate extracted type.
Variables used only by one group move with that group; shared variables stay in the facade.
</diagnosis>

<todo>
- [ ] For each cohesion group:
  - Create a protocol (name reflects the group's responsibility)
  - Create an extracted type owning the group's methods and variables
  - Add `init` parameters for any dependencies the extracted type needs
- [ ] Update the original class:
  - Remove moved methods and variables
  - Inject extracted types via `init` as protocol-typed properties
  - Delegate calls to the injected types
- [ ] **Facade check**: the original class must become a pure Facade — all-protocol deps, pure delegation, no internal logic. Keep extracting if it retains logic.
- [ ] Predict post-fix: 1 cohesion group per extracted type, 1-2 verbs per type
</todo>

<suggested_fix_must_include>
- Protocol definition for each extracted group
- Extracted type with moved variables and methods
- Modified original class with injected protocol-typed dependencies
- Before/after showing the delegation change
</suggested_fix_must_include>

</fix>
