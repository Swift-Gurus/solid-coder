# SPEC-045 Execution Plan

## Objective

Implement aggregate workflow execution without creating a second batching engine or changing the existing DAG semantics. Existing batching, readiness, engine-step execution, validation, events, replay, workflow-output publication, and Stop enforcement remain authoritative.

Implementation is test-first. Every phase begins with a focused failing test, adds only the production behavior required by that test, and reruns the affected flow-engine suite before proceeding.

## Delivery Sequence

This order is authoritative:

1. Write failing tests for parsing and scoping the execution and presentation declarations.
2. Write failing tests for aggregate phase planning across nested workflows and engine-owned boundaries.
3. Write failing tests for prompt/schema generation and instruction deduplication.
4. Write failing tests for partial submissions, retries, replay, and Stop enforcement.
5. Implement incrementally behind those tests, rerunning each focused test group after its corresponding production change.
6. Run all non-live tests and treat every failure as a regression.
7. Run locked Codex and Claude E2E comparisons before enabling aggregate execution in production workflows.

Steps 1–4 establish the executable contract before the feature is considered implemented. Production changes may be introduced incrementally after the corresponding failing test exists, but a later behavior area must not be implemented before its failing contract test has been written.

## Phase 1 — Parse and scope execution policy

1. Add focused parser tests under `tests/harness/flow_engine/resolvers/` proving:
   - omitted `execution` retains granular execution;
   - `execution.mode: aggregate` decodes to a typed enum;
   - an unknown execution mode fails at load time;
   - workflow-root and inline-group declarations survive include expansion and snapshot reload;
   - a child declaration remains scoped to that child when its parent declares no policy;
   - the nearest explicit enclosing declaration controls only its own boundary.
2. Add immutable execution declaration and mode models alongside the existing workflow presentation models.
3. Extend the typed workflow document, inline group, include runtime, alias-group snapshot, and included-workflow instance models to carry explicit execution and presentation policy without encoding policy in step IDs or prompt text.
4. Extend the existing include runtime parser, nested include merger/qualifier, snapshot converter, and snapshot parser so policy ownership survives static includes, dynamic includes, `for_each` materialization, and replay.

Checkpoint: parsing and snapshot tests pass; existing individual and combined presentation tests remain unchanged and passing.

## Phase 2 — Plan aggregate phases across the resolved DAG

1. Add focused planner tests under `tests/harness/flow_engine/resolvers/` proving:
   - compatible dependent agent steps inside one aggregate boundary form one topologically ordered phase;
   - ordinary execution is unchanged when aggregate mode is omitted;
   - a ready operation, command, or script prefix executes before aggregate model work;
   - an engine-owned middle step splits model work into two phases;
   - unresolved conditions and delegate/session work split phases;
   - a child-owned aggregate boundary does not absorb parent or sibling work;
   - a parent aggregate boundary treats a completed child phase as an opaque child assignment rather than reopening its internals.
2. Introduce typed aggregate-boundary, authored-step-coordinate, phase, and assignment models.
3. Add one planner that consumes the resolved `FlowDef`, ordinary `RunState`, and ready/dependency information. It must not mutate the DAG or create aggregate-only step instances.
4. Insert phase planning after `EngineStepDrainer` has exhausted ready engine-owned work and before ready model steps are converted to externally returned results.
5. Reuse existing condition evaluation and `DAGRunner` readiness. The planner may group compatible work but must never independently decide readiness or applicability.

Checkpoint: planner tests and existing operation, command, script, condition, delegate/session, nested include, and workflow-output tests pass. Explicit user-interaction boundaries are deferred until the flow schema has a typed interaction declaration.

## Phase 3 — Render compact prompts and generate exact schemas

1. Add focused renderer/schema tests under `tests/harness/flow_engine/resolvers/` proving:
   - authored prompts and output contracts are ordered by the planned phase;
   - identical authored instructions across batch items render once by typed authored-step identity;
   - item labels and workflow aliases form an applicability matrix without domain inference;
   - required model-visible bindings are present while internal IDs, indexes, persistence paths, and complete source buffers are absent;
   - repeated output names remain isolated by `item label → workflow alias → step ID → output`;
   - combined presentation omitted presents compiled workflow phases independently;
   - aggregate execution omitted combines only the currently ready granular frontier;
   - both modes together compile within workflow boundaries and combine compatible assignments across items/workflows.
2. Extend the existing step-result/rendering path with a typed aggregate presentation rather than a second flow response type.
3. Reuse existing prompt-content and output-schema resolution. Render each authored step as a distinct section; do not parse or rewrite its prose.
4. Generate the aggregate response schema from the original declared `OutputSpec` models and exact assignment coordinates.

Checkpoint: prompt compactness, schema, ordinary batch, and combined presentation suites pass with no changes to granular rendering.

## Phase 4 — Map submissions to original steps

1. Add integration tests under `tests/harness/flow_engine/` proving:
   - a complete aggregate response validates and records every original step completion;
   - a partial response completes valid assignments once and presents only missing assignments next;
   - one invalid assignment consumes only its original instance attempt;
   - unknown item, workflow, step, or output keys are rejected without changing unrelated work;
   - downstream steps unlock only when their original dependencies complete;
   - included workflow outputs publish through the existing aggregation path after all internal phases complete;
   - rule observations still reach the existing MCP scorer unchanged.
2. Add an aggregate submission mapper that translates exact aggregate coordinates into the existing per-instance output mapping.
3. Pass translated outputs through `OutputSubmissionAdvancer`, existing handlers, output validators, attempt handling, and `OutputRecorder`; do not add an aggregate completion event or retry counter.

Checkpoint: submission, retry, workflow-output, and aggregate-rule-scoring integration tests pass.

## Phase 5 — Prove replay and Stop enforcement

1. Add restart/replay tests proving ordinary completion events reconstruct the same remaining aggregate phase without rerunning completed model or engine-owned steps.
2. Add an engine-owned nested-workflow fixture proving a completed operation/command/script prefix executes once, its persisted outputs feed the child phase, and replay presents only unfinished child assignments.
3. Add transition-gate tests proving any missing original step keeps the run active and produces actionable model-visible labels.
4. Reuse `EventReplayer`, run-state reconstruction, readiness, and the existing transition gate. Persist only stable policy/assignment metadata required to reproduce deterministic grouping.

Checkpoint: replay, audit, session scoping, and Stop tests pass without aggregate-specific run state.

## Phase 6 — Full non-live validation

1. Run every non-live test in `tests/`, excluding only explicitly marked live E2E cases.
2. Treat every new failure as a regression and fix it before live testing.
3. Confirm granular workflows, individual `for_each`, batched `for_each`, combined rule presentation, dynamic rule discovery, operations, commands, scripts, delegates/sessions, scoring, and legacy health-check behavior remain passing.

## Phase 7 — Locked Codex and Claude comparison

1. Add one shared live comparison base under `tests/harness/flow_engine/` and thin Codex/Claude subclasses following the existing model-profile test convention.
2. Run the same locked source project, fixture, applicable workflow set, expectations, model-visible source context, and output assertions through granular and aggregate modes.
3. Preserve each run's workflow snapshot, events, transcript, model result, normalized review result, elapsed time, model-turn count, and input/cache/output token measurements in the established test artifact scope.
4. Assert result completeness and locked metric/exception/severity values before comparing cost or speed.
5. Do not enable aggregate execution in bundled production review or gate workflows until both model backends complete the locked comparison and the results are reviewed.

## Planned Reuse and Change Boundaries

| Existing area | Plan |
|---|---|
| `WorkflowIncludeRuntimeParser` and typed workflow models | Extend with typed execution policy and explicit lexical ownership |
| Include resolution, qualification, and materialization | Preserve policy while reusing existing nested and dynamic identities |
| `EngineStepDrainer` and registered step runners | Reuse unchanged as the authority for operations, commands, and scripts |
| `DAGRunner` and condition machinery | Reuse as the authority for readiness and applicability |
| `StepResultBuilder` and rendering capabilities | Extend with typed aggregate phase presentation |
| Existing batch/combined renderers | Reuse shared item labels and presentation capability registration; generalize only where required by generic step-level addressing |
| `OutputSubmissionAdvancer` | Reuse after aggregate coordinates are mapped to existing instance outputs |
| Output validators and attempt handling | Reuse unchanged per original step instance |
| `OutputRecorder`, events, and `EventReplayer` | Reuse ordinary events; add no aggregate completion state |
| Workflow output publication and rule scoring | Reuse after original steps complete |
| Transition gate | Reuse original pending-step state for Stop enforcement |

## Removal and Migration Boundary

- Do not delete experimental single-prompt workflows during implementation; they remain comparison fixtures until the locked Codex/Claude evaluation is accepted.
- Do not modify bundled production review/gate workflows during implementation.
- After comparison approval, migrate selected bundled workflows by adding policy declarations, rerun the locked suite, and only then consider removing redundant experimental prompt copies in a separate change.
