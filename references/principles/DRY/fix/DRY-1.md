<fix id="DRY-1" name="Reuse Miss">

<trigger>
A type or logic already exists in the codebase that this code duplicates — the
existing implementation was not reused.
</trigger>

<strategy severity="SEVERE">
Replace the duplicate code with the existing type. Do not keep two implementations
of the same thing.
Priority: EXACT match → EXTENSIBLE match → remove redundant code.
</strategy>

<diagnosis>
Read the reuse-miss table from findings (existing code, confidence, interface differences).
- **EXACT** (high confidence, no interface differences): the new code is redundant — delete it, use the existing type directly
- **EXTENSIBLE** (high/medium confidence, resolvable differences): adapt the existing type minimally, then use it

**Before deciding where to extract, check reachability:**
The existing match tells you what already exists — not automatically where the fix goes.

1. **Same module/target** → reuse or extend in place.
2. **Different module/package** → pick based on the semantic relationship:
   - (a) **Add the import/dependency** — correct when the existing module is a shared utilities package (not a peer feature package). State this explicitly in the fix.
   - (b) **Extract to the nearest accessible common ancestor** — correct when the existing module is a peer feature module and adding a dependency would create horizontal feature coupling.
   - (c) **Find or create a shared module** — correct when no accessible common ancestor exists AND the abstraction is generic enough to serve multiple modules.
     First, look for an existing module in the project that already collects shared or utility code of the same kind. If one exists and fits → move the abstraction there. Only if nothing suitable exists → propose a new module following the project's own naming and structural conventions.
3. **Different class hierarchy branch (sibling, not ancestor)** → do NOT move to the sibling class. Extract to the deepest common base class that is accessible in the current module. If none exists, apply option (c).

When the reachable target differs from where the pattern currently lives, note both: where it exists today and where the fix should actually go.
</diagnosis>

<todo>
**EXACT match:**
- [ ] Replace all usages of the new (redundant) code with direct usage of the existing type
- [ ] Remove the redundant type/function entirely
- [ ] Update call sites

**EXTENSIBLE match — determine what adaptation is needed:**
- [ ] **Missing protocol conformance** → add `extension ExistingType: NeededProtocol {}` (no new type)
- [ ] **Missing method** → add via `extension` or protocol `default` implementation
- [ ] **Signature mismatch** → add overload or adapter method on the existing type
- [ ] **Needs configuration** → use the existing type's parameters/init instead of reimplementing
- [ ] Update all call sites to use the existing type
- [ ] Remove the redundant new code

- [ ] Predict post-fix: 0 reuse misses; the existing type serves all use sites
</todo>

<suggested_fix_must_include>
- How to use the existing type (direct usage, extension conformance, or minimal adapter)
- Removal of the redundant code
- Updated call sites
- Before/after showing the deduplication
</suggested_fix_must_include>

</fix>
