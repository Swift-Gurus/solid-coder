<fix id="ISP-3" name="Protocol Cohesion Groups">

<trigger>
The protocol contains 2+ cohesion groups — sets of methods always used together by
different conformers but never cross-used between groups.
</trigger>

<strategy severity="SEVERE">
Split the protocol along cohesion group boundaries. Each group becomes its own role
protocol. Groups that never overlap are unambiguous split boundaries.
</strategy>

<diagnosis>
Read the cohesion groups from findings. Each group is a set of methods that co-occur
in conformer usage. Groups that never overlap are unambiguous split boundaries.
</diagnosis>

<todo>
- [ ] For each cohesion group identified in findings:
  - Define a narrow role protocol (name reflects the group's responsibility)
  - Include only the methods in that group
- [ ] Check existing protocols before creating new ones — reuse if a matching narrow protocol exists
- [ ] Create a composition protocol if any consumer needs the full combined interface:
  `protocol CombinedProtocol: GroupA, GroupB {}`
  — **Use `protocol`, not `typealias`** — typealiases cannot be conformed to, breaking decorators and wrappers
- [ ] Update conformers: each adopts only the group protocols covering its implemented methods; remove the original wide protocol
- [ ] Update consumers: replace the wide protocol type with the narrowest group protocol that covers their usage
- [ ] Predict post-fix: 1 cohesion group per narrow protocol; all conformer coverage ≥ 80%
</todo>

<suggested_fix_must_include>
- Narrow role protocol per cohesion group
- Composition protocol (if needed)
- Updated conformer declarations (adopting only relevant group protocols)
- Updated consumer signatures (narrower protocol types)
- Before/after showing the split
</suggested_fix_must_include>

</fix>
