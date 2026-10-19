---
number: SPEC-065
feature: dry-shared-helper-call-false-positive
type: bug
status: draft
parent: SPEC-056
blocked-by: []
blocking: []
---

# Claude flags calls to an extracted shared helper as DRY duplication

## Description

Claude's live DRY review reports a SEVERE within-unit duplication finding for
two methods that delegate to the same already-extracted helper. The reviewed
calculation exists once, but the model classifies its two call sites as separate
duplicated implementations, failing the existing compliant-fixture assertion.
Investigation and implementation are deferred at the user's request; this draft
records the failure and evidence without changing prompts, fixtures, or scoring.

## Steps to Reproduce

1. Use `tests/principles/DRY/fixtures/fixture-2.swift` unchanged. In
   `PayrollLedger`, the private `accumulate` helper owns filtering, multiplication,
   accumulation, and rounding; `grossWages` and `reimbursements` each contain only
   `accumulate(entries)`.
2. Use the existing shared live harness in
   `tests/harness/flow_engine/dry_validation_e2e_live_base.py`. Its
   `test_extracted_helper_avoids_duplicate_findings` case copies the fixture
   into an isolated project's production-source folder, removes repository
   candidate files, enables only DRY, and runs the real `solid-review` bundle.
   Keep the expected values `0 / 0 / 0 / 0`, final `COMPLIANT` severity, and
   existing model profile unchanged.
3. From the repository root with the existing authenticated Claude test setup,
   run:

   ```sh
   python3.12 -m pytest tests/harness/flow_engine/test_dry_validation_live.py::TestClaudeDRYValidationLive::test_extracted_helper_avoids_duplicate_findings -v -s
   ```

4. Inspect `analyze_target_patterns` and `within_unit_duplicate_sites` in the
   preserved `flow-run/events.jsonl`, then the DRY `result.json`. Observe a
   completed review with two non-excepted `IDENTICAL` observations for the
   delegating methods and a within-unit DRY-2 value of two.

Observed on 2026-10-19 with `claude-opus-4-5`. One completed failing sample is
preserved; repeat frequency is unknown. The command reproduces the controlled
setup, not a guaranteed stochastic model response. No live rerun is required
just to record this deferred bug.

## Expected vs Actual

Metric order is repository reuse misses (DRY-1), repository duplicate locations
(DRY-2), within-unit duplicate locations (DRY-2), and missing abstractions (DRY-3).

| Case | Metric values | Final severity |
|---|---|---|
| Locked expectation | `0 / 0 / 0 / 0` | `COMPLIANT` |
| Preserved Claude run | `0 / 0 / 2 / 0` | `SEVERE` |
| Preserved Codex comparison | `0 / 0 / 0 / 0` | `COMPLIANT` |

Shared calls must not be treated as multiple copies of the helper's implementation
in this fixture. The expected result does not exempt duplicated implementation
bodies or repeated logic surrounding a helper call in other fixtures.

Claude supplied `is_exception: false` for both method observations, citing the
single-line calls as its source evidence. Its reasoning asserted that different
business concepts should have different logic, while its assessment also
acknowledged: "accumulate already encapsulates the validation-transform-sum-round
pattern appropriately." Its exception explanation additionally inferred missing
differentiation from the unused `Entry.category` field; that is not duplicated
calculation code in the supplied fixture.

Repository search returned no candidates, with one file scanned. MCP's persisted
derivation counts the two submitted locations (`matched_indexes: [0, 1]`) and
produces DRY-2 = 2. An arithmetic, search, or workflow-completion defect is not
established by this evidence; the semantic classification remains to be
investigated.

Preserved evidence, relative to the repository:

- Claude failure:
  `.solid-coder/.artifacts/test/claude/e2e/review/dry-extracted-helper/20261019T170735Z-e2f99b4e/`.
  Run ID: `f780f184eac94f80ab35ef63b96361a3`.
- Codex compliant comparison:
  `.solid-coder/.artifacts/test/codex/e2e/review/dry-extracted-helper/20261019T170455Z-df37ebb8/`.
- Both directories retain effective workflow snapshots, events, and normalized
  review results under `flow-run/`. The Claude result is at
  `flow-run/results/review/dry/file_review-1.rule_reviews.dry-1/result.json`.
  These local artifacts are not committed; the relevant observations and scores
  are summarized above so this report survives artifact cleanup.

## Affected Component

- Parent: SPEC-056, DRY candidate classification workflow.
- `workflows/review/rules/dry/workflow.yaml`: target-pattern classifications,
  exception interpretation, and the observations consumed by the within-unit
  DRY-2 metric.
- `tests/principles/DRY/fixtures/fixture-2.swift` and the existing live test named
  in the reproduction steps. Preserve the failing assertion; do not mark it
  skipped, weaken its expected result, or retry until green to close this report.
- Related but separate: SPEC-061 concerns a DRY-3 missing-abstraction false
  negative on repeated calculation bodies. This report concerns a DRY-2 false
  positive after the helper has already been extracted. It is also independent
  of SPEC-050 gate applicability and timeout work.

This report does not authorize a prompt rewrite, new engine exception, scoring
change, or fix implementation. Revisit those only when the deferred investigation
is resumed.
