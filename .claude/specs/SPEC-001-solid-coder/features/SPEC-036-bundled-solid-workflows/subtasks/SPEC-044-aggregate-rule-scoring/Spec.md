---
number: SPEC-044
feature: aggregate-rule-scoring
type: subtask
status: completed
parent: SPEC-036
blocked-by: [SPEC-039, SPEC-042, SPEC-043]
blocking: [SPEC-036]
---

# Aggregate Rule Scoring

## Description

Allow one agent step to collect every metric observation and the exception decision for one executable review rule, while retaining the existing MCP-owned scoring, policy, audit, persistence, replay, and aggregation pipeline. This closes the scoring gap in the single-prompt review experiment without adding a scoring operation or asking the model to select severity.

The first consumers are the SRP, OCP, and LSP single-prompt experiments used by combined presentation. ISP and DRY remain unchanged until their per-unit preparation is moved to a compatible scope.

## Input / Output

| | Detail |
|---|---|
| Input | One executable rule workflow containing one agent step with a typed `assessment` declaration and a validated aggregate submission |
| Output | Existing `RuleReviewResult` and aggregate `ReviewResult` artifacts and events, scored by MCP through the existing finalizer |
| Consumers | Single-prompt rule workflows, combined presentation, review policy planning, event replay, audit artifacts, and final review aggregation |

## User Stories

### US-1: Declare aggregate observations once

As a workflow author, I want one agent step to declare all rule metrics and its exception output so MCP can generate and validate one complete response contract.

**Acceptance Criteria:**

- An executable rule may declare one aggregate assessment step:

```yaml
rule:
  match:
    unit_kinds:
      included: [class, struct]

steps:
  - id: assess_srp
    prompt: Apply all SRP measurements and the exception rule.
    assessment:
      metrics:
        - metric_id: SRP-1
          observation_id: verb_count
          value: {type: integer, minimum: 0}
          scoring:
            minor: {operator: greater_than_or_equal, value: 3}
            severe: {operator: greater_than, value: 5}
      exception_observation_id: exception
```

- `assessment.metrics` contains at least one existing typed `MetricDeclaration` and therefore uses the same value and scoring vocabulary as granular metric steps.
- Every metric has a non-empty, unique `observation_id`; it becomes that metric's key in the aggregate output object.
- `exception_observation_id` is non-empty, distinct from every metric observation ID, and defaults to `exception`.
- An assessment step remains an ordinary agent-owned execution step. No new runner, model-session, fan-out, event, or retry mechanism is introduced.
- Authors must not declare `outputs` on an assessment step. MCP generates one audited metric object per observation plus the audited exception object.
- `assessment.supporting_outputs` may preserve typed analysis values needed for audit or explanation. They use the existing output-schema resolution path, are validated with the aggregate response, and do not participate in scoring.
- A rule workflow must use either one aggregate assessment step or the existing granular metric-plus-exception steps. Mixing the two shapes is rejected.

### US-2: Reuse deterministic scoring

As a reviewer, I want aggregate observations scored by the same MCP authority as granular rules so prompt shape cannot change severity semantics.

**Acceptance Criteria:**

- A completed aggregate step is decoded into the existing typed `RuleMetricObservation`, `RuleExceptionDecision`, and `RuleObservations` models.
- `RuleRunFinalizer`, `RuleReviewResultBuilder`, `MetricScoringEvaluator`, severity selection, result persistence, and result events are reused without an alternate scoring path.
- When the submitted exception is true, every metric remains compliant exactly as in granular rule execution.
- Invalid aggregate output is rejected by the existing output validator and consumes only the existing step attempt.
- Completion, retry, replay, nested include provenance, and `for_each` instance isolation use existing step-instance state.
- Final artifacts retain `scoring_authority: mcp`, metric IDs, observation IDs, submitted values, reasoning, evidence, exception decision, provenance, and aggregate severity.

### US-3: Preserve planning and workflow compatibility

As a workflow maintainer, I want aggregate rules to participate in catalog planning and combined presentation without special rule-name logic.

**Acceptance Criteria:**

- Effective rule planning discovers metrics declared inside an assessment and applies the existing workflow-ID and metric-ID policy coordinates.
- Workflow snapshots persist the public `assessment` declaration, omit generated outputs, and reload into the same typed contract.
- Root and included rule workflows support the aggregate shape.
- `rule.auto_include` defaults to `true`. Setting it to `false` keeps an explicitly included workflow executable and scoreable while excluding experimental or specialized variants from `rules: all` expansion.
- A batched aggregate rule remains compatible with `presentation.mode: combined`; partial combined submissions still finalize only completed rule instances.
- The SRP, OCP, and LSP single-prompt experiment workflows become executable rules by adding their existing matcher and authored scoring declarations without changing their detection instructions.
- ISP and DRY are not converted by this spec.

## Technical Requirements

- Parse the assessment declaration once at the YAML boundary into a strict immutable Pydantic model.
- Keep raw mappings inside YAML, JSON-schema, and event/persistence boundary adapters. Runtime scoring and finalization consume typed declarations and observations.
- Generate aggregate output schemas from supporting-output declarations, metric declarations, and the existing required `additional_info.reasoning` and `additional_info.evidence` contract.
- Extend rule structural validation, completion evaluation, observation collection, effective metric planning, and snapshot rewriting through typed assessment metadata.
- Do not add `review.score`, `score_results`, or another workflow operation.
- Do not duplicate scoring-band evaluation, exception handling, severity selection, result persistence, or result events.

## Connects To

| Direction | Target | Relationship |
|---|---|---|
| Parent | SPEC-036 Bundled SOLID Workflows | Makes the single-prompt review experiment produce authoritative scored results |
| Upstream | SPEC-039 Executable Rule Workflows and Review Policy | Reuses declarations, policy coordinates, scoring, audit, and finalization |
| Upstream | SPEC-042 Batched `for_each` Presentation | Preserves one aggregate rule execution per unit instance |
| Upstream | SPEC-043 Combined Rule Presentation | Allows several aggregate rule steps to share one model-facing turn |

## Test Plan

- Load a valid aggregate rule and assert its typed supporting analyses, metrics, generated outputs, and exception contract.
- Reject authored outputs, missing metrics, duplicate observation IDs, collisions with the exception ID, and mixed aggregate/granular rule shapes.
- Persist and reload an aggregate rule snapshot.
- Complete a root aggregate rule and assert deterministic metric and overall severity artifacts.
- Complete included aggregate rule instances through batch and combined presentation and assert independent scored results.
- Submit an exception and assert every metric is compliant.
- Assert effective rule planning includes aggregate metrics and rejects unknown policy metric IDs.
- Assert an executable rule with `auto_include: false` remains available to an explicit include but is omitted from `rules: all`.
- Convert SRP, OCP, and LSP single-prompt experiments and assert their existing output names and scoring bands are preserved.
- Run all non-live, non-E2E tests after focused coverage passes.

## Definition of Done

- [x] Aggregate assessment YAML is typed, validated, generated, and replay-safe.
- [x] Aggregate submissions feed the existing deterministic scorer and audit pipeline.
- [x] Policy planning recognizes aggregate metrics.
- [x] Combined presentation scores each completed rule/unit instance independently.
- [x] SRP, OCP, and LSP experiments are executable aggregate rules; ISP and DRY remain unchanged.
- [x] Focused and complete non-live, non-E2E tests pass.
