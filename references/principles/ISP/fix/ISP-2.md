<fix id="ISP-2" name="Conformer Coverage">

<trigger>
One or more conformers implement fewer than 60% of the protocol's methods, or have
3+ empty/stub implementations.
</trigger>

<strategy severity="MINOR">
Consider a protocol split or adding default implementations for optional-behaviour
methods. Coverage 60–79% with width ≤ 5 does not require full extraction yet.
</strategy>

<strategy severity="SEVERE">
Extract the unused methods into a separate protocol so each conformer only implements
what it uses. Any conformer below 60% coverage or with 3+ stubs requires immediate split.
</strategy>

<diagnosis>
Read the conformer coverage table from findings. Identify which methods the
low-coverage conformer does NOT implement (or stubs with an empty body). Those methods
belong in a separate protocol this conformer should not adopt.
</diagnosis>

<todo>
- [ ] Identify the methods the low-coverage conformer stubs or leaves empty
- [ ] Extract those methods into a new narrow protocol (name reflects the subset's purpose)
- [ ] Check existing protocols first — does any already cover the extracted subset? Use it instead.
- [ ] Create a composition protocol if consumers need both:
  `protocol Full: NarrowA, NarrowB {}`
  — **Use `protocol`, not `typealias`**
- [ ] Update the low-coverage conformer: remove stubs, adopt only the protocols it meaningfully implements
- [ ] Update high-coverage conformers: adopt both narrow protocols if they implement all methods
- [ ] Update consumers: depend on the narrowest protocol for their usage
- [ ] Predict post-fix: all conformer coverage ≥ 80%; no empty/stub implementations
</todo>

<suggested_fix_must_include>
- Extracted narrow protocol for unused methods
- Composition protocol (if needed)
- Updated low-coverage conformer with stubs removed
- Updated consumer signatures
</suggested_fix_must_include>

</fix>
