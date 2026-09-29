---
number: SPEC-058
feature: co-located-metric-authoring
type: subtask
status: complete
parent: SPEC-010
blocked-by: [SPEC-039, SPEC-053, SPEC-054]
blocking: []
---

# Co-Located Metric Authoring

## Description

Allow a workflow author to declare deterministic metrics beside the agent step
that produces their observations. The compact declaration is authoring sugar:
the flow engine normalizes every co-located declaration into the same typed,
independently identified runtime metric node used by an explicit
`type: metric` step.

This feature is additive. Explicit metric steps remain supported and are the
correct form when a metric needs its own scheduling, routing, fan-out,
dependencies, prompt, or source outside one producing step. A workflow is not
required to declare a metric after every prompt. Classification, routing,
preparation, search, command, script, and operation steps may have no metrics.

The goal is to remove repetitive YAML from the common rule shape:

1. an agent submits typed observations;
2. MCP filters and reduces those observations;
3. MCP applies severity bands and records audit evidence.

The feature does not merge model instructions, ask the model to calculate a
score, or remove the runtime boundary between an observation and its metric.

## Proposed YAML Contract

### Compact co-located form

```yaml
steps:
  - id: classify_actions
    type: agent
    prompt: |
      Classify every externally meaningful action performed by the supplied
      unit and identify lifecycle actions.
    outputs:
      - name: actions
        type: data
        schema:
          type: array
          items:
            type: object
            additionalProperties: false
            required: [method, action, is_lifecycle, reasoning, evidence]
            properties:
              method: {type: string, minLength: 1}
              action: {type: string, minLength: 1}
              is_lifecycle: {type: boolean}
              reasoning: {type: string, minLength: 1}
              evidence: {type: string, minLength: 1}
    metrics:
      - id: action_count
        metric_id: SRP-1
        value: {type: integer, minimum: 0}
        scoring:
          source: actions
          when:
            ref: "{{item.is_lifecycle}}"
            equals: false
          severe: {operator: greater_than_or_equal, value: 3}
```

Within `metrics`, `scoring.source` is the exact name of one data output declared
by the owning step. It is not a template expression and cannot address another
step. Filtering, reducers, severity bands, effective policy, exception handling,
audit, replay, and persistence retain the SPEC-039, SPEC-053, and SPEC-054
contracts.

### Equivalent explicit form

```yaml
steps:
  - id: classify_actions
    type: agent
    prompt: |
      Classify every externally meaningful action performed by the supplied
      unit and identify lifecycle actions.
    outputs:
      - name: actions
        type: data
        schema:
          type: array
          items:
            type: object
            additionalProperties: false
            required: [method, action, is_lifecycle, reasoning, evidence]
            properties:
              method: {type: string, minLength: 1}
              action: {type: string, minLength: 1}
              is_lifecycle: {type: boolean}
              reasoning: {type: string, minLength: 1}
              evidence: {type: string, minLength: 1}

  - id: action_count
    type: metric
    metric_id: SRP-1
    depends_on: [classify_actions]
    value: {type: integer, minimum: 0}
    scoring:
      source: "{{steps.classify_actions.outputs.actions}}"
      when:
        ref: "{{item.is_lifecycle}}"
        equals: false
      severe: {operator: greater_than_or_equal, value: 3}
```

Both declarations produce the same runtime metric identity, calculation,
events, rule result, policy behavior, and audit projection.

## Choosing an Authoring Form

| Requirement | Co-located `metrics:` | Explicit `type: metric` |
|---|---:|---:|
| Measure an output of the same agent step | Preferred | Supported |
| Declare several metrics over the same output | Supported | Supported |
| Read an output from a different step | Not supported | Required |
| Depend on several steps | Not supported | Required |
| Use step-level `when` routing | Not supported | Required |
| Use independent `for_each` expansion | Not supported | Required |
| Ask the model to submit a scalar metric | Not supported | Required |
| Give the metric an independent model prompt | Not supported | Required |
| Control metric scheduling separately | Not supported | Required |

Co-located metrics are not emitted in the owning agent step's submission schema.
The model submits only the declared outputs. MCP evaluates the metrics after the
owning step instance completes.

## Input / Output

| | Detail |
|---|---|
| Input | An agent step with typed outputs and zero or more compact metric declarations |
| Normalized form | Existing typed runtime metric nodes with stable IDs and an instance-local dependency on the owning step |
| Output | The same metric events, derivation evidence, severity, normalized rule result, and replay state produced by explicit metric steps |
| Consumers | Bundled rule workflows, client workflows, aggregate execution, rule policy, Stop enforcement, result persistence, and audit tooling |

## User Stories and Acceptance Scenarios

### US-1: Keep a simple metric beside its observations

As a workflow author, I want a deterministic metric beside the step that
produces its observations so a small rule does not require a repetitive sibling
step.

#### Scenario 1.1 — Load one co-located metric

**Given** an agent step declares an array output named `actions`
**And** its `metrics` collection declares `action_count` with source `actions`
**When** the workflow is loaded
**Then** the loader creates one typed runtime metric node
**And** the runtime metric ID is `action_count`
**And** it depends on the owning agent step
**And** it uses the existing collection-backed scoring declaration.

#### Scenario 1.2 — Load several metrics from one observation collection

**Given** one agent step produces a typed observation collection
**And** two co-located metrics filter or reduce that collection differently
**When** the workflow is loaded and executed
**Then** both metrics retain distinct step IDs and metric IDs
**And** the model submits the observation collection once
**And** MCP evaluates both metrics without another model turn.

#### Scenario 1.3 — Permit a prompt with no metric

**Given** a workflow step prepares context, routes work, searches the repository,
or produces non-scored data
**When** it omits `metrics`
**Then** the step remains valid
**And** the engine does not synthesize a metric.

### US-2: Preserve the explicit metric form

As an advanced workflow author, I want explicit metric steps to remain available
when a metric has a lifecycle separate from one producer.

#### Scenario 2.1 — Continue loading existing workflows unchanged

**Given** a workflow declares a top-level `type: metric` step
**When** it is loaded after this feature ships
**Then** its parsing, validation, execution, policy, audit, replay, and Stop
behavior remain unchanged
**And** no migration to `metrics` is required.

#### Scenario 2.2 — Use an explicit cross-step metric

**Given** a metric reads an output from another step or depends on several steps
**When** the workflow is authored
**Then** it is declared as an explicit `type: metric` step
**And** the existing dependency and reference validation applies.

#### Scenario 2.3 — Use an explicit model-owned metric

**Given** a workflow intentionally asks the model to submit a scalar metric
**When** the workflow is authored
**Then** it uses an explicit prompted `type: metric` step
**And** co-located `metrics` cannot declare a prompt or model-owned outputs.

#### Scenario 2.4 — Use explicit scheduling controls

**Given** a metric needs step-level `when`, independent `for_each`, additional
dependencies, or separately ordered execution
**When** the workflow is authored
**Then** it uses the explicit metric form
**And** the compact form is rejected rather than silently changing semantics.

### US-3: Normalize without changing runtime behavior

As a flow-engine maintainer, I want compact metrics normalized onto the existing
metric runtime so the feature does not create a second scoring engine.

#### Scenario 3.1 — Produce equivalent runtime declarations

**Given** one workflow uses the compact example above
**And** another uses its explicit equivalent
**When** both workflows are normalized
**Then** their metric declarations are behaviorally equivalent
**And** both use the existing evaluator, policy applier, event recorder, replay,
rule finalizer, and audit projection.

#### Scenario 3.2 — Drain a compact metric internally

**Given** the owning agent step completes successfully
**When** its co-located collection-backed metric becomes ready
**Then** MCP evaluates it before presenting more model-owned work
**And** neither `flow_start` nor `flow_next` asks the model to submit the metric.

#### Scenario 3.3 — Preserve aggregate presentation

**Given** the owning agent step participates in combined or aggregate
presentation
**When** the aggregate submission completes that step instance
**Then** MCP evaluates its co-located metrics through the ordinary internal drain
**And** the aggregate submission schema contains only authored agent outputs.

#### Scenario 3.4 — Preserve rule finalization

**Given** compact and explicit metrics belong to the same rule workflow
**When** all metrics and the rule exception complete
**Then** the normalized rule result includes both forms identically
**And** severity selection does not depend on authoring syntax.

### US-4: Preserve instance identity through nested workflow fan-out

As a workflow author, I want a compact metric to score the exact output instance
that owns it so results cannot cross units or nested rule instances.

#### Scenario 4.1 — Score nested workflow instances independently

**Given** a rule workflow containing a co-located metric is included once per
review unit
**When** the include is materialized
**Then** each runtime metric instance depends on its matching agent-step instance
**And** it reads only that instance's output.

#### Scenario 4.2 — Require explicit metrics for owner-level fan-out

**Given** an agent step with a co-located metric is expanded with `for_each`
**When** the workflow is loaded
**Then** validation rejects the compact declaration
**And** directs the author to use explicit metric steps until the engine has an
instance-local direct-step output reference contract.

#### Scenario 4.3 — Replay without recompilation drift

**Given** compact metric declarations were normalized and their completion events
were persisted
**When** the run is resumed or replayed
**Then** the same instance identities and derived results are restored
**And** completed metrics are not reevaluated.

### US-5: Reject ambiguous compact declarations

As a workflow author, I want invalid compact syntax rejected at load time so the
engine never guesses at metric ownership or source identity.

#### Scenario 5.1 — Require a declared local output

**Given** a co-located metric names a source that is absent from the owning
step's outputs
**When** the workflow is loaded
**Then** validation fails with the owning step ID, metric ID, and missing output
name.

#### Scenario 5.2 — Reject a cross-step expression

**Given** a co-located metric uses a template expression or names another step's
output as its source
**When** the workflow is loaded
**Then** validation directs the author to use an explicit `type: metric` step.

#### Scenario 5.3 — Reject scheduling fields

**Given** a compact metric declares `type`, `prompt`, `outputs`, `depends_on`,
step-level `when`, or `for_each`
**When** the workflow is loaded
**Then** validation rejects the unsupported field and recommends the explicit
metric form.

#### Scenario 5.4 — Reject duplicate IDs

**Given** a compact metric ID collides with an authored step ID or another
compact metric ID in the same workflow scope
**When** the workflow is loaded
**Then** validation rejects the collision before materialization.

#### Scenario 5.5 — Reuse existing source-schema validation

**Given** a compact metric has an invalid item condition, reducer projection,
value type, or severity declaration
**When** the workflow is loaded
**Then** the existing SPEC-053 and SPEC-054 validation reports the same failure
that its explicit equivalent would report.

## Technical Requirements

- Add optional `metrics` only to model-owned agent step declarations in the
  initial contract.
- A compact metric requires `id`, `metric_id`, `value`, and `scoring`.
- `scoring.source` is a plain local output name in compact syntax and must name a
  data output declared by the owning step.
- A compact metric cannot declare fields that create independent execution:
  `type`, `prompt`, `outputs`, `depends_on`, step-level `when`, or `for_each`.
- Normalization occurs before ordinary workflow validation and materialization.
- The normalized runtime model is the existing metric declaration and instance
  model; no compact-only evaluator, event, result, or replay format is added.
- Normalized metric IDs participate in the existing workflow-scope uniqueness
  check.
- The runtime dependency on the owning step is implicit and instance-local.
- Include-level fan-out creates one metric instance per materialized rule
  workflow instance through the existing included-workflow runtime.
- Direct owner-step `for_each` is rejected in the initial contract; it requires
  a separate instance-local output-reference design before compact metrics can
  support it without consuming sibling fan-in output.
- Compact metrics are engine-owned deterministic calculations. Model-owned
  scalar metrics remain explicit steps.
- Existing workflows and clients are backward compatible without migration.
- Workflow snapshots preserve enough normalized declaration data for stable
  replay and audit while retaining source-location information for diagnostics.

## Non-Goals

- Removing or deprecating explicit `type: metric` steps.
- Requiring metrics after every prompt.
- Combining prompts or altering aggregate/combined presentation.
- Allowing a compact metric to read arbitrary steps or multiple sources.
- Adding a new condition, reducer, severity, policy, exception, or expression
  language.
- Supporting co-located metrics on a directly iterating owner step; use an
  included workflow or explicit metric steps for that case.
- Automatically rewriting bundled workflows.
- Moving whole-rule exception steps into agent steps.
- Asking the model to calculate counts, extrema, distinct values, ratios, or
  severity.

## Connects To

| Direction | Spec | Relationship |
|---|---|---|
| Parent | SPEC-010 | Owns workflow loading, normalization, materialization, execution, replay, and Stop behavior |
| Upstream | SPEC-039 | Supplies executable rule metrics, rule finalization, policy, and audit contracts |
| Upstream | SPEC-053 | Supplies filtered collection scoring and engine-owned metric execution |
| Upstream | SPEC-054 | Supplies deterministic reducers and source-schema validation |
| Consumer | SPEC-055 | Bundled count-backed rules may adopt the compact syntax after this contract is complete |
| Consumer | SPEC-057 | Reducer-backed bundled rules may adopt the compact syntax during deliberate workflow cleanup |

## Test Plan

- Parsing tests for absent, single, and multiple `metrics` declarations.
- Normalization tests comparing compact declarations with explicit equivalents.
- Validation tests for missing local outputs, cross-step sources, forbidden
  scheduling/model fields, duplicate IDs, invalid filters, invalid reducers, and
  incompatible value schemas.
- Execution tests proving metrics drain after an ordinary agent submission and
  after an aggregate submission without appearing in model-facing schemas.
- Instance-scoping tests for nested includes and validation coverage rejecting
  direct owner-step `for_each`.
- Rule-result tests mixing compact and explicit metrics with a whole-rule
  exception and effective project policy.
- Event/replay tests proving stable identity, source evidence, no duplicate
  evaluation, and unchanged Stop behavior.
- Backward-compatibility tests loading representative existing explicit metric
  workflows without normalization changes.
- A test-owned Codex and Claude live workflow that submits one observation
  collection and proves MCP derives two compact metrics from it.

## Implementation Plan

1. Add failing decoding tests for optional co-located `metrics` on agent steps.
2. Add failing validation tests for local sources, forbidden fields, duplicate
   IDs, and equivalence with existing collection/reducer validation.
3. Introduce a typed compact metric declaration distinct from the existing
   runtime metric declaration.
4. Add a normalization boundary that expands compact declarations into existing
   typed runtime metric nodes while retaining source locations.
5. Add failing execution tests for ordinary completion, aggregate completion,
   nested includes, and rejected owner-level `for_each` declarations.
6. Implement instance-local materialization and reuse the existing internal
   metric drain, event, policy, exception, result, audit, replay, and Stop paths.
7. Add mixed compact/explicit compatibility coverage and representative legacy
   workflow loading tests.
8. Run all non-live tests.
9. Run the locked test-owned Codex and Claude live comparison before migrating
   any bundled rule workflow.

## Definition of Done

- [x] Workflow authors may declare deterministic local-output metrics beside an
  agent step.
- [x] Compact declarations normalize to existing runtime metric nodes.
- [x] Explicit `type: metric` workflows remain fully supported and unchanged.
- [x] Prompts without metrics remain valid; no metric is inferred.
- [x] Invalid local sources and independent-execution fields fail at load time.
- [x] Ordinary, aggregate, nested, fan-out, policy, exception, audit, replay, and
  Stop behavior have deterministic coverage.
- [x] All non-live tests pass.
- [x] Locked Codex and Claude test-owned live workflows pass before bundled
  workflow migration begins.

## Validation Evidence

- The complete non-live suite passes with live integration folders excluded.
- Compact execution coverage proves ordinary and aggregate drain, nested
  include fan-out, mixed explicit/compact finalization, exception audit,
  persisted derivation evidence, and replay without duplicate evaluation.
- Project-policy integration proves effective scoring overrides apply to a
  normalized co-located metric.
- Stop-hook integration proves the gate blocks on authored model work, never
  exposes the internally drained metric as a pending model step, and allows Stop
  after the rule completes.
- The test-owned compact workflow passes through both Codex and Claude. Each
  model submits one observation collection and MCP derives two metrics from it.
