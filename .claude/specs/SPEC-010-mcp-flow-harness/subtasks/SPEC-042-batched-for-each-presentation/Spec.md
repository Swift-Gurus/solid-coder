---
number: SPEC-042
feature: batched-for-each-presentation
type: subtask
status: in-progress
parent: SPEC-010
blocked-by: [SPEC-030, SPEC-031, SPEC-037]
blocking: [SPEC-036]
---

# Batched Model Presentation for `for_each`

## Description

Allow one model-facing workflow turn to complete multiple ready `for_each` instances that share the same authored agent step. The engine continues to materialize, validate, persist, retry, aggregate, and replay one instance per source item; batching changes only how sibling work is presented to the model and how one batch response is translated back into those existing instances.

The model receives the shared authored instruction and output schema once, followed by a compact manifest containing only domain identity such as unit name and unit kind. Engine-qualified instance IDs, include aliases, source indexes, and internal result envelopes remain hidden. MCP owns the mapping from submitted domain identities to runtime instances and proves that every expected item was addressed before the fan-out can complete.

This capability is intended for rule workflows that apply one procedure to several review units. It avoids repeating a large rule prompt and schema once per unit without replacing `for_each`, weakening instance-scoped validation, or relying on prior conversational turns.

## Input / Output

| | Detail |
|---|---|
| Input | A step or included workflow using the typed object form of `for_each` with `mode: batch`, a source collection, and a compact item label expression |
| Output | One model-facing batch instruction and a domain-keyed batch submission translated into ordinary validated per-instance completions |
| Consumers | Bundled review workflows, client-authored workflows, `flow_start`, `flow_next`, event replay, result aggregation, and Stop enforcement |

## User Stories

### US-1: Present one shared instruction for several units

As a workflow author, I want a rule instruction and its schema shown once for all applicable units so repeated unit review does not multiply prompt size and model round-trips.

**Acceptance Criteria:**

- Existing scalar `for_each: "{{steps.<id>.outputs.<name>}}"` behavior remains unchanged.
- A typed object form enables batching explicitly:

```yaml
for_each:
  source: "{{steps.prepare_review.outputs.units}}"
  mode: batch
  label: "{{item.target.name}}"
```

- `source` follows the existing typed step-output reference grammar and resolves to the same ordered collection used by ordinary `for_each`.
- `mode` accepts only `individual` or `batch`; omission means `individual`.
- `label` is required for `batch`, is evaluated once per item, and must resolve to a non-empty string.
- Batch presentation applies only to model-facing agent work. Engine-owned operation, script, and command steps continue to drain without a model turn.
- One batch contains only ready sibling instances derived from the same authored step and batch declaration. Unrelated rules, steps, nested workflow definitions, or dependency stages are never merged.
- The model-facing text contains the shared authored prompt and output contract once plus an ordered item manifest containing `unit_name` and, when available from typed applicability, `unit_kind`.
- The manifest does not contain runtime instance IDs, include aliases, source indexes, complete source buffers, engine context objects, or internal result envelopes.
- The prompt remains self-contained. A batch step never says to reuse rules shown in a previous model turn.

### US-2: Submit results using domain identity

As an agent, I want to return one result per named unit without understanding internal workflow identities.

**Acceptance Criteria:**

- The returned batch contract uses the existing `flow_next.outputs` object. Each key is one exact domain label supplied in the manifest, and each value contains the outputs declared by the authored step.
- MCP maps each unique output key to its existing internal `StepInstance`; the model never echoes an internal instance ID.
- Unknown labels, duplicate labels, missing labels, malformed result objects, and output-schema violations are reported with domain names and do not silently complete the batch.
- Label uniqueness is checked before presentation. Ambiguous labels fail deterministically before a model attempt and identify the colliding source items; MCP does not guess by result order.
- Successful item results are validated through the existing `StepOutputValidator` and recorded through the existing `OutputRecorder` as ordinary per-instance completion events.
- No separate batch-result event or second output-schema system is introduced.

### US-3: Preserve partial completion, retries, and completion guarantees

As the flow engine, I want batching to retain all existing fan-out guarantees so reducing model turns does not weaken correctness or auditability.

**Acceptance Criteria:**

- A batch may submit every item or a valid subset. Valid addressed items complete once; omitted items remain incomplete and are returned in the next batch presentation.
- The workflow cannot unlock dependents or report completion until every non-skipped source instance has completed.
- An invalid item consumes only that instance's attempt and does not reopen valid siblings.
- A resubmission contains only unfinished or rejected items; already completed items are not shown or accepted again.
- Empty source collections complete internally with existing empty fan-in behavior and no model turn.
- Ordered fan-in continues to use original source order, independent of result order or completion turn.
- Replay reconstructs completed, rejected, skipped, and outstanding instances from existing events and presents only outstanding domain labels.
- Stop enforcement reports outstanding domain labels rather than internal instance IDs when a batched step remains actionable.

### US-4: Batch included rule-workflow instances

As a bundled review workflow, I want a rule included once per normalized unit while presenting its model-facing assessment as one batch so file/unit scoping and rule audit remain correct.

**Acceptance Criteria:**

- Batch presentation may be declared on a workflow include using the same object-form `for_each` contract.
- Runtime include materialization still creates one child workflow instance per source item and retains isolated child dependencies, conditions, inputs, attempts, and declared outputs.
- Ready child agent steps may batch only when they originate from the same included workflow ID and authored child step.
- Child engine-owned preparation operations run per instance before their dependent model-facing steps become batch candidates.
- If only a subset of child instances reaches the same model-facing step, only that ready subset is presented; instances at another child step are not merged.
- Completed child workflow outputs continue to publish through the include alias's ordered `results` collection.
- File-scoped rules remain non-iterated and run once. Unit-scoped rules use batched `for_each`; batching does not turn file-scoped rules into unit rules or vice versa.

## Technical Requirements

### Typed declaration

`for_each` decodes immediately into one typed declaration rather than remaining a dictionary:

```text
ForEachDeclaration
  source: StepOutputReference
  mode: ForEachMode
  label: WorkflowExpression | None

ForEachMode
  INDIVIDUAL
  BATCH
```

The scalar syntax maps to `INDIVIDUAL` with no label. The persisted workflow snapshot stores the normalized typed fields so runtime execution does not parse strings, trim values, or inspect raw YAML mappings.

### Batch identity and model contract

- Runtime `StepInstance.instance_id` remains the authoritative internal identity.
- `BatchPresentationItem` carries the internal instance reference, validated domain label, optional typed unit kind, and resolved authored outputs internally.
- `BatchPresentation` exposes only shared instructions, the ordered domain manifest, and the shared response schema to the renderer.
- `BatchSubmission` decodes the model response into typed domain-keyed output entries before mapping them to instances.
- Mapping is exact and case-sensitive. Names are not trimmed, normalized, guessed, or position-matched.
- The model-facing response envelope is equivalent to:

```json
{
  "outputs": {
    "ReportComposer": {
      "<declared-output>": "<value>"
    },
    "ReportEnvelope": {
      "<declared-output>": "<value>"
    }
  }
}
```

- The actual envelope schema is generated from the existing authored output specifications. Every authored output is required and undeclared fields are forbidden.
- Internal translation produces the existing `outputs[instance_id] = {<declared outputs>}` structure before invoking the existing submission lifecycle.

### Selection and rendering

- `FirstReadyStepSelector` remains the default individual selector.
- A batch-aware selector groups only sibling `StepResult` values that carry the same typed batch group identity and authored contract identity.
- A dedicated batch renderer formats the shared prompt once, appends the compact manifest and generated response envelope once, and does not concatenate already-rendered per-item prompts or deduplicate text using regular expressions.
- Shared and item-specific material are represented separately before rendering. Downstream components do not parse prompt strings to recover identity or context.

### Validation and event compatibility

- Batch envelope decoding happens at the flow boundary. Application services consume typed submission objects rather than dictionaries.
- Coverage validation runs before ordinary output validation and returns exact missing, unknown, and duplicate domain labels.
- Valid partial submissions are translated and passed to the existing output-submission path. Invalid individual results retain existing per-instance attempt accounting.
- Existing `step_completed`, `step_attempt_failed`, skipped-step, workflow-result, and run-terminal events remain authoritative. No compatibility handling for unpublished batch event formats is required.
- Result replay and run snapshots preserve internal identity only; model-facing labels are deterministically reconstructed from the snapshotted source items and typed declaration.

## Connects To

| Direction | Target | Relationship |
|---|---|---|
| Parent | SPEC-010 MCP-Driven Flow Orchestration | Extends model presentation without replacing flow state or fan-out |
| Upstream | SPEC-030 Flow Engine | Reuses instance expansion, partial completion, retries, ordered fan-in, and replay |
| Upstream | SPEC-031 Flow MCP Tools | Reuses `flow_start`/`flow_next` and the existing output submission boundary |
| Upstream | SPEC-037 Conditional Routing and Result Aggregation | Reuses dynamic include materialization, child identities, conditions, and result publication |
| Downstream | SPEC-036 Bundled SOLID Workflows | Enables one model call per rule across applicable review units |

## Test Plan

- Parse scalar `for_each` into individual presentation and parse the typed object form into batch presentation.
- Reject unknown presentation values, missing batch labels, non-step source references, blank labels, and ambiguous evaluated labels.
- Render one ordinary batched agent step and assert the rule prompt and output schema appear once while every domain label and unit kind appears exactly once.
- Assert internal instance IDs, include aliases, source indexes, source buffers, and engine context do not appear in model-facing text.
- Submit a complete batch and prove every existing per-instance completion event, ordered fan-in result, and dependent transition is unchanged.
- Submit a valid subset and prove completed siblings are not rendered again, omitted siblings remain ready, and the workflow cannot finish early.
- Submit unknown, duplicate, missing, and schema-invalid items and assert domain-readable errors plus instance-scoped attempts.
- Replay after partial completion and assert only unfinished domain items are presented without reevaluating completed work.
- Run a nested included workflow with engine-owned preparation before its agent step and prove only child instances ready at the same authored step are grouped.
- Apply batch mode to the experimental SRP file-review workflow and prove two normalized units require one SRP model submission while preserving two internal SRP instance results.
- Run the experimental batched composite through Codex and Claude using the same fixture, model profiles, and locked expected outputs; capture model turns, input/cache/output tokens, elapsed time, events, and final rule results.
- Run all non-live tests before live comparison.

## Definition of Done

- [ ] Scalar `for_each` behavior remains backward compatible.
- [ ] Typed batch declarations work for ordinary steps and included workflows.
- [ ] The model sees one shared rule prompt/schema and only domain unit identity.
- [ ] MCP rejects or retains every missing, unknown, duplicate, ambiguous, or invalid item without internal IDs leaking to the model.
- [ ] Existing per-instance validation, attempts, completion events, ordered fan-in, replay, conditions, and workflow outputs remain authoritative.
- [ ] Experimental per-rule review workflows can batch all applicable units into one model-facing submission.
- [ ] Focused tests, all non-live tests, and Codex/Claude live composite validation pass.
