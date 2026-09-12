---
number: SPEC-046
feature: flow-tests-depend-on-distributed-workflows
type: bug
status: draft
parent: SPEC-010
blocked-by: [SPEC-045]
blocking: []
---

# Flow Tests Depend on Distributed Workflows

## Description

Generic aggregate flow-engine tests currently resolve `solid-file-review-aggregate` from the plugin's distributed workflow catalog. That workflow is now a legitimate production bundle used by `solid-gate-on-write`, but generic engine tests must not depend on it merely to exercise aggregate mechanics. The dependency couples engine-test setup to shipped review behavior, makes unrelated catalog changes affect the tests, and allows generic test requirements to shape a workflow delivered to clients.

The tests must own their workflow definitions. Unit and integration tests may write workflows into their existing temporary packages. Live Codex and Claude tests must stage equivalent test fixtures into their isolated source project or another test-owned catalog root before starting the model session. Preserved run artifacts must still contain the exact resolved workflow snapshot and events used by the test.

## Steps to Reproduce

1. Replace or rename the production `solid-file-review-aggregate` bundle while leaving aggregate engine behavior unchanged.
2. Run the generic aggregate SRP live E2E test.
3. Observe that the engine test cannot resolve the production review workflow ID even though aggregate execution should be testable from a test-owned fixture.

## Expected vs Actual

| | Behavior |
|---|---|
| Expected | Every flow-engine test creates or stages its own workflow fixture and leaves the distributed workflow catalog unchanged. |
| Actual | Generic aggregate tests depend on the production review bundle used by the write gate. |

## Affected Components

- `tests/harness/flow_engine/aggregate_srp_validation_e2e_live_base.py`
- Aggregate live-test fixture preparation and temporary workflow-package discovery

## Acceptance Criteria

- Given an aggregate unit or integration test, when it runs, then its workflow is created under its temporary test package or loaded from a test-only fixture.
- Given the aggregate Codex or Claude live E2E, when its isolated project is prepared, then the test-owned aggregate workflow is available to that session without adding it to the distributed catalog.
- Given the plugin's distributed workflows, when tests are collected or executed, then no test requires a workflow to be added, renamed, or retained there.
- Given a production integration test for `solid-gate-on-write`, when it executes, then it may resolve `solid-file-review-aggregate` because that dependency is the behavior under test; this exception does not apply to generic aggregate engine tests.
- Given a completed live run, when artifacts are preserved, then the resolved workflow snapshot, events, transcript/model result, scoring result, timing, and usage evidence remain auditable.
- Given canonical rule workflows are needed by a test-owned aggregate parent, when the fixture resolves `rules: all`, then it reuses the existing packaged rules without copying their implementation into the test fixture.

## Deferred Fix Boundary

Do not change the affected generic live tests as part of the gate migration. Implement this bug separately by introducing test-owned workflow fixture mechanics and migrating those tests. The production `solid-file-review-aggregate` bundle remains because it is now used by `solid-gate-on-write`; it is not removed as part of this bug.
