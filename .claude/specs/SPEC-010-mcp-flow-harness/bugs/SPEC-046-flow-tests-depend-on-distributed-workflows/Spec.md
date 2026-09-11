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

Aggregate flow-engine tests currently resolve `solid-file-review-aggregate` from the plugin's distributed workflow catalog. A test-only workflow must not become part of the client-visible plugin surface merely so unit, integration, or live E2E tests can execute it. This couples test setup to shipped files, makes catalog changes affect test behavior, and allows test requirements to shape workflows delivered to clients.

The tests must own their workflow definitions. Unit and integration tests may write workflows into their existing temporary packages. Live Codex and Claude tests must stage equivalent test fixtures into their isolated source project or another test-owned catalog root before starting the model session. Preserved run artifacts must still contain the exact resolved workflow snapshot and events used by the test.

## Steps to Reproduce

1. Remove or rename `workflows/review/experiments/solid-file-review-aggregate/workflow.yaml`.
2. Run the aggregate bundle integration test or aggregate SRP live E2E test.
3. Observe that the test cannot resolve the workflow ID even though aggregate execution is an engine capability that should be testable without a distributed experiment workflow.

## Expected vs Actual

| | Behavior |
|---|---|
| Expected | Every flow-engine test creates or stages its own workflow fixture and leaves the distributed workflow catalog unchanged. |
| Actual | Aggregate tests depend on a client-visible experimental workflow under `workflows/review/experiments`. |

## Affected Components

- `tests/harness/flow_engine/test_solid_review_bundle_execution.py`
- `tests/harness/flow_engine/aggregate_srp_validation_e2e_live_base.py`
- Aggregate live-test fixture preparation and temporary workflow-package discovery
- `workflows/review/experiments/solid-file-review-aggregate/workflow.yaml`

## Acceptance Criteria

- Given an aggregate unit or integration test, when it runs, then its workflow is created under its temporary test package or loaded from a test-only fixture.
- Given the aggregate Codex or Claude live E2E, when its isolated project is prepared, then the test-owned aggregate workflow is available to that session without adding it to the distributed catalog.
- Given the plugin's distributed workflows, when tests are collected or executed, then no test requires a workflow to be added, renamed, or retained there.
- Given a completed live run, when artifacts are preserved, then the resolved workflow snapshot, events, transcript/model result, scoring result, timing, and usage evidence remain auditable.
- Given canonical rule workflows are needed by a test-owned aggregate parent, when the fixture resolves `rules: all`, then it reuses the existing packaged rules without copying their implementation into the test fixture.

## Deferred Fix Boundary

Do not change the affected tests as part of the manual aggregate-prompt experiment. Implement this bug separately by introducing test-owned workflow fixture mechanics, migrating every affected test, and only then removing the obsolete distributed test workflow.
