---
number: SPEC-061
feature: dry-3-missing-abstraction-classification
type: bug
status: draft
parent: SPEC-056
blocked-by: []
blocking: []
---

# DRY-3 missing-abstraction classification differs between live backends

## Description

The locked DRY fixture produces DRY-3 = 0 through Codex and DRY-3 = 1 through
Claude, although both runs complete the same review scenario and detect the two
within-unit duplicate locations. This leaves the Codex live contract failing
and missing-abstraction detection unverified across backends. The investigation
must establish whether the discrepancy comes from effective instructions,
model classification, or the locked expectation; the recorded MCP count matches
each submitted observation collection, so an engine counting defect is not
established.

## Steps to Reproduce

1. Use `tests/principles/DRY/fixtures/fixture-1.swift` unchanged. Its
   `PayrollLedger.grossWages` and `PayrollLedger.reimbursements` methods repeat
   positive-entry filtering, multiplication, accumulation, and cent rounding.
2. Use the shared live harness in
   `tests/harness/flow_engine/dry_validation_e2e_live_base.py`. It copies the
   target into an isolated project's `Sources/ReviewTarget.swift`, removes
   scenario candidate files, enables only the `dry` rule, and launches the real
   `solid-review` bundle through shared file normalization. Keep the locked
   expected values `0 / 0 / 2 / 1` and existing model profiles unchanged.
3. From the repository root, run the specific Codex case:

   ```sh
   python3 -m pytest tests/harness/flow_engine/test_dry_validation_live.py::TestCodexDRYValidationLive::test_workflow_satisfies_its_live_contract -v -s
   ```

4. Run the matching Claude case as a separate comparison:

   ```sh
   python3 -m pytest tests/harness/flow_engine/test_dry_validation_live.py::TestClaudeDRYValidationLive::test_workflow_satisfies_its_live_contract -v -s
   ```

5. Compare the preserved `flow-run/events.jsonl` entries for
   `search_repository`, `analyze_target_patterns`, and `missing_abstractions`,
   then compare `flow-run/results/review/result.json`. Observe the Codex
   assertion `0 != 1` for DRY-3 despite a completed workflow.

Observed on 2026-09-30 in one completed run per backend; repeat frequency is
unknown. These commands reproduce the controlled setup, not a guaranteed model
response. No repeated measurements are required merely to file this report.

## Expected vs Actual

Metric order below is DRY-1 repository reuse misses, DRY-2 repository duplicate
locations, DRY-2 within-unit duplicate locations, then DRY-3 missing abstractions.

| Case | Values | Target-analysis evidence |
|---|---|---|
| Locked expectation | `0 / 0 / 2 / 1` | Two repeated implementation locations and one non-excepted missing abstraction. |
| Codex actual | `0 / 0 / 2 / 0` | Both locations classified `IDENTICAL`, `is_exception: false`; `missing_abstractions: []`. |
| Claude actual | `0 / 0 / 2 / 1` | Both duplicate locations reported; one non-excepted `currency-rounding` pattern citing `(subtotal * 100).rounded() / 100` in both methods. |

Both searches return `candidates: []`, `files_scanned: 1`, and
`files_with_frontmatter: 0`. Both final reviews are `SEVERE` because of DRY-2;
matching overall severity does not make the individual DRY-3 results equivalent.
Codex's metric event records `source_size: 0`, `matched_indexes: []`, and
`value: 0`; Claude's records one source entry, `matched_indexes: [0]`, and
`value: 1`. MCP therefore correctly derives each count from what was submitted.

Preserved run evidence (paths relative to the repository):

- Codex failure:
  `.solid-coder/.artifacts/test/codex/e2e/review/dry/20260930T231323Z-8d8fd4a1/`.
  Model session: `01a0f498-2c69-7aa2-b330-7e45b47f11d4`.
- Claude comparison:
  `.solid-coder/.artifacts/test/claude/e2e/review/dry/20260930T231626Z-a8dafbfa/`.
- Each directory preserves the effective `flow-run/workflow.yaml`,
  `flow-run/events.jsonl`, normalized review results, and model-session evidence.
  These local artifact copies are not committed; the observed submissions and
  count derivations are recorded above so the report survives artifact cleanup.

## Affected Component

- Parent: SPEC-056, DRY candidate classification workflow, specifically its
  missing-abstraction live contract.
- Authored workflow: `workflows/review/rules/dry/workflow.yaml`,
  `analyze_target_patterns` output `missing_abstractions` and the downstream
  MCP-owned DRY-3 metric.
- Canonical intent: `references/principles/DRY/rule.md` and its review
  instructions. Compare these with the effective prompts, schemas, supplied
  source, and model-profile settings in the preserved runs before proposing a
  change. Determine why Codex omitted the observation Claude supplied, and
  validate the fixture expectation against the original rule.
- Existing live assertions:
  `tests/harness/flow_engine/dry_validation_e2e_live_base.py` and
  `tests/harness/flow_engine/test_dry_validation_live.py`.
- Related but separate: SPEC-060 shared source-search performance. Search returns
  the expected empty collection in both runs. Earlier harness-wiring failures
  and the preceding Codex startup/tool-availability failure are not this
  completed-run discrepancy.

This is an investigation report, not an approved prompt or scoring change.
Preserve the fixture, locked expectation, and generic MCP counting behavior
until evidence supports a proposed correction. Do not hide the mismatch by
retrying until a passing response, weakening assertions, or special-casing DRY
inside the engine. Append the root cause, fix plan, and targeted tests after
investigation rather than assuming them here.
