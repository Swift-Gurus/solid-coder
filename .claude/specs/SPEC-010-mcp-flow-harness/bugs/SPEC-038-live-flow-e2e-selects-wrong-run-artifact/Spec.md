---
number: SPEC-038
feature: live-flow-e2e-selects-wrong-run-artifact
type: bug
status: draft
parent: SPEC-010
blocked-by: []
blocking: []
---

# Live Flow E2E Selects the Wrong Run Artifact

## Description

The shared live flow-engine E2E identifies its run by selecting the newest `events.jsonl` created while the model session was active. When another flow E2E runs concurrently, the test can inspect that other run while it is still being written and report a false failure even though its own flow completed successfully. This makes live Codex and Claude results unreliable under overlapping execution.

## Steps to Reproduce

1. Start two live flow-engine E2E invocations against the same project artifact directory so their execution overlaps.
2. Allow both invocations to create and append events to separate flow runs.
3. Allow one invocation to finish while the other run has completed classification but has not completed its selected response branch.
4. Observe: the finished invocation selects the other run's newer `events.jsonl` and fails while searching for its expected completed branch.

## Expected vs Actual

|          | Behavior |
|----------|----------|
| Expected | Each live E2E reads only the event log belonging to the flow run it started, independent of other concurrent runs and their modification times. |
| Actual   | The E2E selects the newest newly created event log by modification time and can read another concurrent run's partial events, producing a false assertion failure. |

## Affected Component

The shared Codex and Claude live flow-engine E2E harness under `tests/harness/flow_engine`, specifically run-artifact discovery and correlation after the spawned model session completes.
