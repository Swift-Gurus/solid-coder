<fix id="SRP-3" name="Stakeholder Count">

<trigger>
2+ stakeholders detected — the class has multiple distinct reasons to change.
</trigger>

<strategy severity="SEVERE">
Identify which methods and variables serve which stakeholder. Extract per-stakeholder
types behind protocols. Use stakeholder boundaries as the extraction guide even when
cohesion groups are not fully disjoint.
</strategy>

<diagnosis>
Read the stakeholders from the findings.
Map each method and property to the stakeholder that drives it.
Methods that serve multiple stakeholders are coordination points — they stay in the
original class as delegation.
</diagnosis>

<todo>
- [ ] For each distinct stakeholder:
  - Create a protocol named after the role this stakeholder needs (e.g. `ReportGenerating`, `DataExporting`)
  - Create an extracted type implementing that protocol
  - Move only the methods driven by that stakeholder
- [ ] Update the original class:
  - Inject per-stakeholder types via `init` as protocol-typed properties
  - Replace direct method calls with delegation
- [ ] **Facade check**: original class becomes a coordination facade — all deps are protocol-typed, all methods delegate. Adjust if it retains stakeholder-specific logic.
- [ ] Predict post-fix: 1 stakeholder per extracted type, 1 reason to change per type
</todo>

<suggested_fix_must_include>
- Protocol per stakeholder with method signatures
- Extracted type per stakeholder with moved logic
- Modified original class as coordination facade
- Before/after of a method that was stakeholder-specific
</suggested_fix_must_include>

</fix>
