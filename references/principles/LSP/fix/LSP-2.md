<fix id="LSP-2" name="Contract Compliance">

<trigger>
A subclass `override` strengthens preconditions, weakens postconditions, or breaks
invariants of the base class. Applies only to class inheritance with `override`.
</trigger>

<strategy severity="SEVERE">
Restore Liskov compliance by adjusting either the base contract or the subtype's
override, without breaking existing callers.
</strategy>

<diagnosis>
Read the contract violations from the findings. For each:
- **Strengthened precondition**: subtype rejects inputs the base accepts (e.g. narrower guard)
- **Weakened postcondition**: subtype returns values the base contract guarantees won't happen
- **Broken invariant**: subtype allows state the base declares impossible
</diagnosis>

<todo>
**Strengthened preconditions:**
- [ ] Option A: remove the extra guard in the subtype (handle the edge case differently)
- [ ] Option B: if the base contract is wrong, widen it — update the base class and all callers

**Weakened postconditions:**
- [ ] Option A: fix the subtype override to honor the base guarantee
- [ ] Option B: if the base guarantee is unrealistic, weaken it — update the base class and all callers

**Broken invariants:**
- [ ] Route all state mutation through validated setters (`didSet` or a private setter with guards)
- [ ] Ensure the invariant is enforced in both base and subtype

- [ ] Predict post-fix: 0 contract violations; subtype is substitutable for base at all call sites
</todo>

<suggested_fix_must_include>
- Modified base class contract (if updating the base) OR modified override (if fixing the subtype)
- Before/after of the violating override
- Setter/guard pattern if routing through validated setters
</suggested_fix_must_include>

</fix>
