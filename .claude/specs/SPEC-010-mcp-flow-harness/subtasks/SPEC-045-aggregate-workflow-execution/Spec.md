---
number: SPEC-045
feature: aggregate-workflow-execution
type: subtask
status: complete
parent: SPEC-010
blocked-by: [SPEC-037, SPEC-042, SPEC-043, SPEC-044]
blocking: [SPEC-036]
---

# Aggregate Workflow Execution

## Description

Allow a workflow author to opt compatible model-owned workflow segments into aggregate execution so existing multi-step workflows can be tested as fewer model turns without creating duplicate single-prompt workflow variants. The engine compiles typed step prompts and output contracts in dependency order, renders each unique instruction once, lists the opaque workflow instances assigned to it, validates one structured submission, and maps every result back to the original step instances.

The compiler is generic. It does not know about reviews, principles, units, packages, files, scoring, or any other domain concept. Review-rule discovery and MCP scoring are consumers of the same capability; non-review workflows retain their ordinary output and completion behavior.

Aggregate execution does not replace the DAG. Original step identity, output validation, attempts, events, replay, conditions, workflow outputs, and optional rule scoring remain authoritative. Engine-owned or externally interactive boundaries split aggregation into separate phases.

## Proposed YAML

```yaml
steps:
  - group: selected_work
    execution:
      mode: aggregate
    presentation:
      mode: combined
    steps:
      - include:
          rules: all
        as: selected_rules
        depends_on: [prepare]
        for_each:
          source: "{{steps.prepare.outputs.items}}"
          mode: batch
          label: "{{item.name}}"
        with:
          review_unit: "{{item}}"
```

`execution.mode: aggregate` controls compilation of compatible steps within each included workflow instance. `presentation.mode: combined` controls whether compatible compiled workflow instances share one model-facing turn. Either mode may be used independently.

## Input / Output

| | Detail |
|---|---|
| Input | A typed aggregation boundary containing already resolved workflow steps, includes, dependencies, conditions, batch labels, and output specifications |
| Output | One or more aggregate model assignments translated into ordinary validated completions for the original step instances |
| Optional consumers | Rule discovery, rule scoring, review policy, release workflows, documentation workflows, research workflows, and custom project workflows |

## User Stories and Acceptance Scenarios

### US-1: Compile existing workflows without duplicating them

As a workflow author, I want to select aggregate execution on existing workflows so I can compare granular and low-turn execution without maintaining alternate prompt copies.

#### Scenario 1.1 — Aggregate a compatible multi-step workflow

**Given** an included workflow contains three model-owned steps with an acyclic dependency order
**And** the enclosing group declares `execution.mode: aggregate`
**When** all external dependencies of that workflow instance are satisfied
**Then** MCP creates one aggregate assignment containing the three steps in topological order
**And** it does not modify or duplicate the source workflow definition
**And** granular execution remains available when aggregate mode is omitted.

#### Scenario 1.2 — Preserve transport-neutral authored instructions

**Given** compatible steps contain authored prompts
**When** MCP compiles them
**Then** every prompt is copied verbatim into its identified step section
**And** MCP does not parse, rewrite, concatenate heuristically, or infer meaning from prompt text
**And** workflow authors remain responsible for instructions that make sense in both granular and aggregate execution.

#### Scenario 1.3 — Reject an unknown execution mode

**Given** a group declares an unsupported `execution.mode`
**When** the workflow is loaded
**Then** loading fails with a validation error naming the unsupported mode
**And** the engine does not silently fall back to granular execution.

### US-2: Apply discovery and conditions before aggregation

As a workflow author, I want existing discovery and filtering to decide the assignments so aggregate execution never runs inapplicable work.

#### Scenario 2.1 — Aggregate dynamically discovered workflows

**Given** an include such as `rules: all` expands dynamically from the workflow catalog
**And** policy, matcher, scope, and condition evaluation retain a subset of workflow instances
**When** aggregate execution is planned
**Then** only the retained instances appear in aggregate assignments
**And** aggregation does not implement another discovery or applicability mechanism.

#### Scenario 2.2 — Exclude a conditionally skipped instance

**Given** two instances of the same included workflow exist
**And** an existing condition evaluates false for one instance before compilation
**When** the aggregate prompt is rendered
**Then** only the applicable instance label appears
**And** the skipped instance retains the existing auditable skip event and completion semantics.

#### Scenario 2.3 — Do not guess unresolved conditions

**Given** a candidate step condition depends on an output that is not available before the aggregate turn
**When** MCP plans aggregation
**Then** that step is not moved across the unresolved dependency
**And** MCP ends the aggregate phase before that step
**And** the step may participate in a later aggregate phase after its condition becomes resolvable.

### US-3: Render instructions once with a generic assignment matrix

As an agent, I want each instruction and schema shown once with its assigned items so prompt size does not multiply by the number of instances.

#### Scenario 3.1 — Deduplicate by typed authored-step identity

**Given** the same authored step is assigned to ten batch instances
**When** MCP renders an aggregate turn
**Then** the authored prompt and output contract appear exactly once
**And** ten opaque labels appear in its assignment list
**And** no regular expression or prompt-text equality is used to establish identity.

#### Scenario 3.2 — Render domain-neutral labels

**Given** an evaluated batch label is `Core`
**When** the assignment manifest is rendered
**Then** the engine labels it generically as an item
**And** it does not infer that `Core` is a package, unit, file, topic, or another domain type
**And** domain terminology appears only when provided by authored prompt text.

#### Scenario 3.3 — Render an applicability matrix without repeating instructions

**Given** workflow `alpha` applies to items `A` and `B`
**And** workflow `beta` applies only to item `B`
**When** combined presentation renders the aggregate assignments
**Then** the instruction for `alpha` appears once
**And** the instruction for `beta` appears once
**And** the manifest associates `A` with `alpha` and `B` with `alpha` plus `beta`.

#### Scenario 3.4 — Keep MCP-owned context out of the prompt

**Given** runtime instances contain source indexes, internal IDs, normalized inputs, applicability evidence, and persistence paths
**When** the aggregate prompt is rendered
**Then** only authored instructions, required model-visible bindings, opaque labels, and output contracts are shown
**And** internal runtime data and complete source buffers are not serialized into the prompt.

### US-4: Address every original step without output collisions

As the flow engine, I want aggregate results addressed by existing identities so arbitrary workflows can contain repeated output names safely.

#### Scenario 4.1 — Generate the generic response envelope

**Given** two workflow aliases each contain several compiled steps
**When** MCP generates the aggregate schema
**Then** results are addressed as `item label → workflow alias → step ID → declared outputs`
**And** every addressed step requires all of its declared outputs
**And** omitted assignments remain pending under the existing partial-submission contract
**And** undeclared keys are forbidden.

```json
{
  "Item A": {
    "alpha": {
      "analyze": {"analysis": {}},
      "measure": {"value": 1, "additional_info": {"reasoning": "...", "evidence": "..."}}
    }
  }
}
```

#### Scenario 4.2 — Preserve identical output names from different steps

**Given** an analysis step and a metric step both declare an output named `value`
**When** the aggregate schema is generated
**Then** each value remains under its original step ID
**And** no output is renamed, overwritten, or inferred from prompt text.

#### Scenario 4.3 — Preserve workflow-output aggregation

**Given** an included workflow publishes outputs derived from its child steps
**When** all compiled step outputs validate
**Then** existing workflow-output resolution runs unchanged
**And** downstream dependencies consume the same values as granular execution.

### US-5: Preserve validation, retry, replay, and completion

As a workflow maintainer, I want fewer model turns without weakening any existing correctness guarantee.

#### Scenario 5.1 — Complete a valid aggregate submission

**Given** an aggregate turn contains several item/workflow/step assignments
**When** the model submits every required output with valid values
**Then** MCP validates each value through the existing step-output validators
**And** records ordinary completion events for the original instances
**And** unlocks dependents only after their original dependencies are complete.

#### Scenario 5.2 — Retain missing work

**Given** the model omits one required workflow assignment but submits valid siblings
**When** MCP processes the response
**Then** valid siblings complete once
**And** the missing assignment remains pending
**And** the next response presents only the incomplete assignment
**And** the run cannot finish early.

#### Scenario 5.3 — Isolate an invalid assignment retry

**Given** one assignment violates its generated schema
**And** sibling assignments are valid
**When** MCP processes the response
**Then** only the invalid original instance consumes an attempt
**And** valid siblings remain complete
**And** only unfinished or rejected work is presented again.

#### Scenario 5.4 — Reject unknown addressing

**Given** a submission contains an unknown item label, workflow alias, step ID, or output name
**When** MCP decodes it
**Then** the submission is rejected without guessing by order or similarity
**And** unrelated pending instances remain unchanged.

#### Scenario 5.5 — Replay after interruption

**Given** some aggregate assignments completed before interruption
**When** a new engine process replays `events.jsonl`
**Then** it reconstructs the ordinary original instance state
**And** renders only incomplete assignments
**And** it does not require a separate aggregate-result event.

#### Scenario 5.6 — Stop enforcement sees original pending work

**Given** at least one compiled original step remains incomplete
**When** the agent attempts to stop
**Then** the existing transition gate denies completion
**And** reports actionable remaining work through model-visible labels
**And** aggregate presentation introduces no independent lock or completion state.

### US-6: Respect execution boundaries

As a workflow author, I want the planner to split unsafe workflows into valid phases rather than change their semantics.

#### Scenario 6.1 — Drain an engine-owned prefix

**Given** an operation, command, or script produces data required by later model steps
**When** the workflow advances
**Then** MCP executes the engine-owned step normally
**And** aggregates only compatible model work that becomes ready afterward.

#### Scenario 6.2 — Split at an engine-owned middle step

**Given** model step `A` feeds an operation that feeds model step `B`
**When** aggregate execution is requested
**Then** `A` and `B` are placed in separate model turns
**And** the operation runs between them
**And** dependency order is unchanged.

#### Scenario 6.3 — Preserve delegate/session execution

**Given** a delegate or session step exists within the requested boundary
**When** aggregation is planned
**Then** that step retains its existing runner and concurrency semantics
**And** model-owned work is aggregated only on a compatible side of that boundary.

#### Scenario 6.4 — Scope a nested workflow around engine-owned steps

**Given** a parent workflow declares no execution or presentation mode
**And** its nested workflow declares `execution.mode: aggregate` and `presentation.mode: combined`
**And** the nested workflow contains an operation, command, or script whose output is required by compatible model-owned steps
**When** the nested workflow advances
**Then** MCP executes each ready engine-owned step once through its existing runner without rendering it in the model prompt
**And** persists its ordinary outputs before planning the dependent aggregate model phase
**And** applies aggregate execution and combined presentation only within the nested workflow boundary
**And** does not combine the nested work with parent or sibling work that has no compatible enclosing policy
**And** publishes the nested workflow's declared outputs only after all of its internal phases complete
**And** replay recognizes completed engine-owned steps and does not execute them again.

### US-7: Support optional domain finalization without coupling

As a platform maintainer, I want review scoring and ordinary workflow completion to consume the same aggregate execution results independently.

#### Scenario 7.1 — Finalize an executable review rule

**Given** a compiled workflow carries typed rule metric and exception declarations
**When** its original step outputs complete
**Then** the existing rule observation collector and MCP scorer publish the same `RuleReviewResult` as granular execution
**And** aggregate compilation does not implement scoring.

#### Scenario 7.2 — Complete a non-review workflow

**Given** a release, documentation, or research workflow has no rule declaration
**When** its aggregate outputs validate
**Then** it completes through ordinary workflow-output and dependency mechanics
**And** no review result, severity, metric, or exception structure is required.

#### Scenario 7.3 — Preserve effective review selection

**Given** dynamically discovered review rules have file-extension, unit-kind, tag, policy, or exception applicability
**When** a combined aggregate review is planned
**Then** those existing decisions determine the exact assignment matrix
**And** disabled or inapplicable rules do not appear in the prompt or response schema.

## Technical Requirements

- Parse `execution.mode` once at the YAML boundary into a typed enum and immutable declaration.
- Represent compilation boundaries, authored-step identity, assignments, and aggregate response coordinates as typed models. Raw mappings remain limited to YAML, JSON Schema, MCP, and persistence boundaries.
- Build aggregate phases from the resolved DAG and existing readiness state. Do not discover dependencies by parsing prompt text.
- Preserve step prompts and output specifications as distinct typed sections until final rendering.
- Deduplicate instructions by stable authored workflow/step identity, never by string equality, regular expression, prefixes, or naming conventions.
- Address aggregate responses by exact item label, authored workflow alias, authored step ID, and declared output name.
- Reuse existing output validation, attempt recording, completion events, workflow-output publication, replay, Stop enforcement, and optional rule finalization.
- Do not create aggregate-only step instances, locks, result events, retry counters, or scoring paths.
- Persist enough typed aggregation metadata in the workflow snapshot to reconstruct the same phases and labels after restart.
- Aggregate planning must be deterministic: the same resolved workflow and state produce the same ordered instruction sections, assignments, and schema.

## Connects To

| Direction | Target | Relationship |
|---|---|---|
| Parent | SPEC-010 MCP-Driven Flow Orchestration | Adds generic low-turn execution planning while retaining the flow state machine |
| Upstream | SPEC-037 Conditional Routing and Result Aggregation | Supplies nested workflow identity, conditions, outputs, and runtime materialization |
| Upstream | SPEC-042 Batched `for_each` Presentation | Supplies opaque item labels, partial completion, retries, and replay |
| Upstream | SPEC-043 Combined Rule Presentation | Supplies deduplicated multi-workflow rendering and nested submission mapping |
| Optional consumer | SPEC-044 Aggregate Rule Scoring | Finalizes review-rule outputs without coupling scoring to compilation |
| Downstream | SPEC-036 Bundled SOLID Workflows | Enables gate/review experiments from canonical granular rules without duplicate single-prompt workflows |

## Execution Plan

See [ExecutionPlan.md](./ExecutionPlan.md).

## Test Plan

### Parsing and snapshots

- Given `execution.mode: aggregate`, when YAML loads, then the resolved group contains the typed aggregate execution declaration.
- Given an unknown mode, when YAML loads, then validation fails without fallback.
- Given a nested aggregate group, when its snapshot is persisted and reloaded, then its identity, mode, aliases, and ordering are unchanged.

### Compilation and boundaries

- Given three dependent compatible model steps, when planned, then one phase contains them in topological order.
- Given an operation between two model steps, when planned, then two aggregate phases surround one normal operation execution.
- Given a parent without execution or presentation settings and a nested aggregate/combined workflow with an engine-owned prefix, when advanced, then the prefix executes once, its persisted outputs feed one child-scoped aggregate phase, and the child policy does not affect its parent or siblings.
- Given that nested workflow is replayed after its engine-owned prefix completed, when planning resumes, then the prefix is not executed again and only its unfinished child phase is presented.
- Given a delegate/session boundary, when planned, then later work is not moved before that boundary.
- Given an unresolved condition, when planned, then compilation ends before the condition and resumes only after its dependency exists.

### Prompt compactness and privacy

- Given one authored step across ten items, when rendered, then its prompt and schema occur once and every label occurs once.
- Given overlapping workflow applicability, when rendered, then the manifest contains exactly the applicable matrix without duplicated instructions.
- Given the label `Core`, when rendered, then the engine uses generic item terminology and performs no domain inference.
- Given internal IDs, indexes, normalized source, policy evidence, and artifact paths, when rendered, then none appear unless explicitly authored as model-visible inputs.

### Submission correctness

- Given repeated output names in different steps, when the schema is generated, then step-ID nesting prevents collisions.
- Given a complete valid response, when submitted, then every original instance completes through existing events and downstream outputs match granular execution.
- Given a valid partial response, when submitted and replayed, then only missing assignments remain ready.
- Given one invalid assignment, when submitted, then only its attempt changes and valid siblings remain complete.
- Given unknown item, workflow, step, or output keys, when submitted, then MCP rejects them without completing unrelated work.
- Given a restart after partial completion, when events replay, then the same pending aggregate phase is reconstructed without aggregate-specific events.

### Generic and review consumers

- Given a non-review release-style workflow over several opaque items, when aggregated, then it completes without rule or scoring types.
- Given canonical SRP/OCP/LSP rule workflows selected dynamically, when aggregated, then their prompts occur once, all expected unit/rule/step outputs are required, and MCP-scored results equal granular scoring for identical observations.
- Given the SwiftUI fixture, when applicability is resolved, then ISP and test-only rules are absent, applicable file/unit/tag rules appear once, and engine-owned DRY search divides phases without being moved into a model prompt.
- Given project policy disables a discovered rule or metric, when aggregation is planned, then disabled work is absent and audit provenance remains unchanged.

### Complete validation

- Run focused parser, planner, renderer, submission, replay, and finalization tests.
- Run all non-live, non-E2E tests.
- Run the same locked fixture through granular and aggregate execution with Codex and Claude, capturing outputs, accuracy, model turns, elapsed time, input/cache/output tokens, and terminal artifacts before deciding whether aggregate mode is suitable for the gate.

## Definition of Done

- [x] Aggregate execution is a typed generic group capability independent of review semantics.
- [x] Existing workflows can switch between granular and aggregate execution without duplicate prompt workflows.
- [x] Dynamic discovery, matchers, policy, conditions, and scope decide assignments before compilation.
- [x] Each authored instruction/schema appears once per aggregate turn with a generic assignment matrix.
- [x] Generic step-level response addressing prevents collisions and maps to original instances.
- [x] Engine-owned and delegate/session boundaries split phases without reordering work. Explicit typed user-interaction boundaries remain deferred as recorded in the execution plan.
- [x] Existing validation, partial completion, retries, events, replay, outputs, Stop enforcement, and optional scoring remain authoritative.
- [x] Generic non-review and dynamically discovered review scenarios pass focused tests.
- [x] Full non-live tests and locked Codex/Claude comparisons pass.
