---
number: SPEC-037
feature: conditional-workflow-routing-and-result-aggregation
type: subtask
status: ready
parent: SPEC-010
blocked-by: [SPEC-030, SPEC-035]
blocking: [SPEC-036, SPEC-033]
---

# Conditional Workflow Routing and Result Aggregation

## Description

Extend the flow engine so a workflow can classify its input, conditionally execute matching steps or included workflow packages, and converge their declared outputs into a final aggregation step. This enables flows such as health-check to break source into units, run the general reviews plus specialized reviews such as SwiftUI only for matching units, and return one normalized review result without generating a different workflow file for every run. Conditional routing builds on SPEC-030's completed `for_each` lifecycle; it must not introduce a second expansion, retry, replay, or fan-in mechanism.

## Input / Output

| | Detail |
|---|---|
| Input | A validated workflow definition containing ordinary steps and included workflow packages with optional `depends_on`, `for_each`, declarative `when` rules, and explicit input mappings; top-level `flow_start` parameters, current items, and upstream step outputs provide values. |
| Output | Durable completed or skipped branch events, validated workflow-level output envelopes for every executed branch instance, and deterministic branch-result collections available to downstream aggregation steps. |
| Consumer | `flow_start`, `flow_next`, `flow_status`, bundled review and gate workflows from SPEC-036, and client-authored workflow packages. |

## User Stories

### US-1: Route classified units through matching review workflows and converge their results

As the flow engine, I want to route classified review units through every matching workflow branch so that one final aggregation step can consume all completed branch results.

**Acceptance Criteria:**

- A workflow definition, ordinary step, path-based include, or workflow-ID include may declare an optional `when` rule using the same grammar; omitting `when` at any scope preserves unconditional execution at that scope.
- An included workflow may declare `depends_on` and `for_each` alongside `when`, allowing the condition to be evaluated once per expanded item after its declared dependencies complete.
- A reusable workflow may declare named inputs with inline or file-backed JSON Schemas. Top-level values come from `flow_start(..., params=...)`; an include maps parent values into the child through `with`. Child steps read those mapped values through the existing `params.<name>` namespace.
- A condition may read declared flow inputs, the current `for_each` item, and outputs from declared upstream dependencies. Unknown input names, invalid item paths proven by the source array's item schema, and non-upstream step references fail workflow validation before the run starts; a missing path that cannot be proven statically fails before that branch starts an execution attempt.
- Nested item paths such as `{{item.language}}` are an explicit extension of the expression resolver. Existing `{{item}}`, `{{params.<name>}}`, and `{{steps.<id>.outputs.<name>}}` behavior remains unchanged.
- Conditions use structured `all`, `any`, and `not` composition with the leaf operators `equals`, `not_equals`, `in`, `not_in`, and `exists`; arbitrary code and host-language expression evaluation are rejected.
- Condition evaluation is deterministic engine behavior. The LLM is not asked to interpret the condition, classify the payload, choose branches, or report which branches should run.
- Health-check file and unit classification is produced by an engine-owned script/command step or an existing deterministic MCP boundary with schema-validated outputs; the classifier is not an agent step.
- Equality and membership comparisons are type-strict: the engine does not coerce strings, numbers, booleans, arrays, objects, or null values before comparison.
- When a condition evaluates true, the step or included workflow instance follows the existing execution, retry, output-validation, and failure lifecycle.
- When a condition evaluates false, the engine records a durable skipped outcome containing the branch identity and evaluated condition, starts no execution attempt, and consumes neither an execution attempt nor a turn.
- A false workflow-level condition skips the complete workflow instance before any internal step becomes ready. For an included workflow, the parent alias records a skipped instance and publishes no result for it; for a top-level run, the engine records the skipped workflow outcome and completes the run without executing steps.
- A false step-level condition skips only that expanded step instance. Its internal dependents treat it as terminal for dependency resolution, while the rest of the workflow continues.
- A skipped branch is terminal for dependency resolution, so a downstream join waits until every dependency is either completed or skipped and does not deadlock on a non-matching branch.
- Conditions are not exclusive: when multiple branches match the same item, all matching branches execute; when no optional branch matches, the workflow may still proceed to its join with an empty result collection.
- A workflow package may declare named workflow outputs that select values from its completed internal steps and validate those values against inline or file-backed JSON Schemas before the included workflow instance is complete.
- Every included-workflow alias exposes an ordered `results` collection to downstream interpolation; each completed item contains its stable instance identity, source item, and already validated declared workflow outputs, while skipped items are omitted from the collection. The envelope does not create a second output-schema system.
- A non-iterated included workflow exposes the same collection shape with zero or one item, so aggregators do not need separate scalar and fan-out handling.
- The result collection order follows the source `for_each` order, independent of the order in which parallel branches finish.
- A downstream aggregation step may depend on included-workflow aliases and interpolate their `results` collections into an agent prompt, script argument, or command text; the aggregation operation itself remains workflow-defined and may call an MCP tool or use a process-backed step.
- The bundled health-check flow can break input into units, run a general review for applicable units, additionally run the SwiftUI review only when `language == "swift"` and `unit_kind == "view"`, and aggregate every emitted review result into the existing normalized review-result structure.
- If an executed branch exhausts retries, produces an invalid declared workflow output, or otherwise fails, the join does not run, a `run_failed` event is recorded, and the run reports `failed`; skipped branches are not failures.
- Event replay restores the original completed/skipped decisions and branch output ordering without re-evaluating conditions or re-running completed workflow instances.
- `flow_status` distinguishes pending, running, completed, and skipped branch instances and reports the condition summary for skipped instances.
- A conditional ordinary step that is skipped has no outputs. Existing interpolation failure behavior applies if a downstream step incorrectly references those absent outputs; optional branch aggregation uses the include alias's zero-or-one `results` collection.

## Technical Requirements

### Conditional branch grammar

The condition grammar is declarative and uses the existing interpolation namespaces:

```yaml
when:
  all:
    - ref: "{{item.language}}"
      equals: swift
    - ref: "{{item.unit_kind}}"
      equals: view
```

- A leaf has exactly one `ref` and exactly one comparison operator.
- `exists` accepts a boolean and distinguishes an absent path from a present null value.
- `in` and `not_in` require a YAML array comparison value.
- `all` and `any` require a non-empty list of conditions; `not` wraps exactly one condition.
- A conditional declaration must depend on every step referenced by its condition. Transitive upstream references are valid; sibling, downstream, and cyclic references are invalid.
- `for_each` resolves before `when`, and `{{item}}` is available only for the corresponding expanded item.
- `for_each` instance identity, partial completion, empty-source completion, ordered output fan-in, replay, engine-owned process execution, and per-instance attempt budgets are inherited unchanged from SPEC-030 and its characterization tests.
- Conditions are evaluated from outermost to innermost without collapsing their namespaces: include-invocation `when`, workflow-level `when`, then each ready step's `when`. Every applicable scope must pass, and a false outer scope prevents evaluation or execution of inner scopes.

### Workflow inputs and include mappings

Reusable workflows declare the values they accept instead of reading undeclared ambient parent context:

```yaml
inputs:
  - name: review_unit
    schema_file: review-unit.schema.json
```

- Input names are unique within the workflow.
- Input schemas follow the existing output-schema grammar and package-relative resource resolution.
- At top level, `flow_start` parameters are matched to declared inputs. On an included workflow, `with` supplies an expression for each required child input.
- Missing required inputs, unknown mapped input names, and statically invalid mappings fail before a run starts. Resolved values are schema-validated before the child workflow instance starts.
- Workflows without an `inputs` declaration retain the existing unrestricted `params` behavior for backward compatibility, but they cannot use undeclared parameter names in statically validated conditions.

### Workflow-level conditions

A reusable workflow may own its intrinsic applicability rule so every caller receives the same protection without copying the condition into each include:

```yaml
id: solid-swift-ui-review
inputs:
  - name: review_unit
    schema_file: review-unit.schema.json
when:
  all:
    - ref: "{{params.review_unit.language}}"
      equals: swift
    - ref: "{{params.review_unit.unit_kind}}"
      equals: view
```

- Workflow-level `when` may reference only the workflow's declared inputs. It cannot reference a parent's steps, parent `item`, or the workflow's own steps because no internal step has executed yet.
- On `flow_start`, parameters are validated before workflow-level `when` is evaluated.
- On include execution, include-level `when` is evaluated in the parent context first; when it passes, `with` is resolved and validated, then workflow-level `when` is evaluated against the child's mapped `params` context.
- A caller may add an include-level `when` to narrow an invocation, but it cannot override a false workflow-level condition.
- The workflow-level decision is recorded once per workflow instance and restored by replay without re-evaluation.

### Conditional workflow include

Workflow includes retain SPEC-027 and SPEC-035 alias qualification and package resolution while adding runtime branch fields:

```yaml
- include: { workflow: solid-swift-ui-review }
  as: swift_ui_review
  depends_on: [break_down]
  for_each: "{{steps.break_down.outputs.units}}"
  with:
    review_unit: "{{item}}"
  when:
    all:
      - ref: "{{item.language}}"
        equals: swift
      - ref: "{{item.unit_kind}}"
        equals: view
```

- The include alias remains the opaque dependency name used by downstream steps.
- Each expanded include instance has a stable identity derived from the alias and source-item index.
- Runtime fields belong to the alias group as a whole. They are not copied onto every inlined child step; one matching group instance executes one complete child DAG with instance-scoped internal step identities.
- A false condition skips the complete included workflow instance rather than evaluating each internal step independently.
- A true condition resolves and validates `with`, then executes the included workflow using only its mapped inputs plus its own internal step outputs.

### Step-level conditions

Steps inside either a top-level or included workflow use the same grammar:

```yaml
- id: inspect_accessibility
  depends_on: [classify]
  when:
    ref: "{{steps.classify.outputs.requires_accessibility_review}}"
    equals: true
  prompt: Review accessibility behavior.
```

- A step-level condition is evaluated only after its declared dependencies complete and after its own `for_each` expansion, when present.
- Each expanded instance receives an independent condition decision using its own `item` binding.
- A skipped step instance starts no agent, process, or delegate execution and consumes no turn or attempt.
- Internal dependents wait until every relevant dependency instance is completed or skipped.

### Workflow output contract

Reusable review workflows publish their result without exposing their terminal internal step to the parent:

```yaml
outputs:
  - name: review_results
    type: data
    value: "{{steps.publish_review.outputs.review_results}}"
    schema_file: review-results.schema.json
```

- Workflow outputs are resolved only after every internal terminal dependency required by the output expression completes.
- Output names are unique within the workflow and output expressions may reference only internal steps.
- Output schemas follow the existing step-output schema rules and resolve relative to the declaring workflow package.
- A missing output reference or schema mismatch fails that workflow instance before its result is published.
- The parent accesses results through `{{workflows.<alias>.results}}`; an alias with no matching instances resolves to `[]`.

### Join and aggregation contract

```yaml
- id: aggregate_reviews
  depends_on: [general_review, swift_ui_review]
  prompt: |
    Call the review-result aggregation tool with these branch results:
    general: {{workflows.general_review.results}}
    swift_ui: {{workflows.swift_ui_review.results}}
  outputs:
    - name: review_result
      type: data
      schema_file: review-result.schema.json
```

- Alias dependencies are satisfied only when all expanded instances under that alias are completed or skipped.
- Result interpolation produces canonical JSON arrays rather than presentation-formatted text and uses the existing template renderer for prompts plus newly supported rendering of script arguments and command text.
- The flow engine gathers and orders branch outputs but does not define review-domain merge policy; the declared aggregation step owns deduplication, severity merging, and the final result schema.
- Existing workflows without conditions or workflow-level outputs retain their current parsed definitions, snapshots, events, and execution behavior.
- The shared live flow-engine E2E contract uses a fixed workflow definition whose classification step loads a package-relative `prompt_file`. Test setup may replace only that prompt file in a temporary workflow package so the same workflow can be exercised with different classification text without placing the text or expected category in the spawned model's launch prompt.

## Connects To

| Direction | Target | Relationship |
|---|---|---|
| Upstream | SPEC-030 Core Flow Engine | Extends step readiness, expansion, event replay, interpolation, validation, and status projection. |
| Upstream | SPEC-035 Workflow Packages, Discovery, and Composition | Uses stable workflow IDs, aliased includes, package resources, and opaque include-group dependencies. |
| Downstream | SPEC-036 Bundled SOLID Workflows and Gate-on-Write Migration | Enables one static health/review workflow to route units through general and specialized review packages before aggregation. |
| Downstream | SPEC-033 Subagent Flow Stop Hook | Deferred follow-up resumes only after the main conditional and included-workflow lifecycle is stable. |
| Downstream | Flow MCP tools | Returns conditional readiness and completed/skipped state through the existing start, next, and status boundaries. |

## Diagrams

### Connections

```mermaid
flowchart LR
    Input["Source and health-check parameters"] --> Breakdown["Break down and classify units"]
    Breakdown --> Router["Conditional workflow router"]
    Catalog["Workflow package catalog"] --> Router
    Router --> General["General review workflow instances"]
    Router --> SwiftUI["SwiftUI review workflow instances"]
    General --> Join["Completed and skipped branch join"]
    SwiftUI --> Join
    Join --> Aggregate["Workflow-defined result aggregator"]
    Aggregate --> Result["Normalized review result"]
```

### Flow

```mermaid
flowchart TD
    Start["Start health-check workflow"] --> BreakDown["MCP classifies files and units"]
    BreakDown --> Expand["Expand candidate branches per unit"]
    Expand --> Evaluate{"Evaluate branch condition"}
    Evaluate -- "true" --> Execute["Execute included workflow instance"]
    Evaluate -- "false" --> Skip["Record skipped branch instance"]
    Execute --> Validate["Validate declared workflow outputs"]
    Validate --> Join["Wait for all instances to complete or skip"]
    Skip --> Join
    Join --> Aggregate["Aggregate ordered completed results"]
    Aggregate --> Done["Return normalized result"]
```

### Sequence

```mermaid
sequenceDiagram
    participant Agent
    participant MCP as Flow MCP
    participant Engine as Flow Engine
    participant Child as Included Review Workflows
    participant Aggregator

    Agent->>MCP: flow_start(health-check, input)
    MCP->>Engine: create run and execute deterministic classification
    Engine->>Engine: expand items and evaluate conditions
    Engine->>Child: start every matching workflow instance
    Engine->>Engine: record non-matching instances as skipped
    Child-->>Engine: schema-validated workflow outputs
    Engine-->>Agent: aggregation step with ordered branch results
    Agent->>Aggregator: aggregate normalized review results
    Aggregator-->>Agent: final review result
    Agent->>MCP: flow_next(final result)
    MCP-->>Agent: status done
```

## Test Plan

### Unit Tests — Condition validation and evaluation

- When a condition uses each supported leaf and composition operator, validation accepts it and evaluation returns the type-strict result.
- When a condition contains an unknown, sibling, downstream, or cyclic output reference, workflow loading fails with the condition location and invalid reference.
- When an `in` comparison does not provide an array or a composition node is empty, workflow loading fails before a run is created.
- When a referenced value is absent versus present with null, `exists` distinguishes the two states.
- When a `for_each` item is available, the condition evaluates separately for each item without leaking another item's context.
- When a workflow-level condition references parent state or an internal step, workflow loading rejects the invalid namespace.
- When a step-level condition references a valid transitive dependency, it is accepted and evaluated only after that dependency completes.

### Characterization Tests — Existing `for_each` lifecycle

These tests are written and passing before conditional execution code is changed:

- Partial submissions return only unfinished instances and do not unlock downstream dependencies.
- Out-of-order completions aggregate outputs in source-item order.
- Empty source arrays complete inside MCP with empty outputs and no agent turn.
- Replay restores completed instances without repeating them.
- Invalid instances retain independent attempt budgets and do not reopen completed siblings.
- Script and command fan-out executes inside MCP and returns only downstream agent-owned work.

### Unit Tests — Conditional readiness and replay

- When a top-level workflow condition is false, no internal step executes and the run records a skipped workflow outcome before completing.
- When an included workflow condition is false, the whole workflow instance is skipped and its parent alias publishes no result for that instance.
- When a step-level condition is false, only that step instance is skipped and its dependents may proceed once their remaining dependencies are terminal.
- When include-level and workflow-level conditions are both present, the include condition evaluates in parent context before input mapping and the workflow condition evaluates afterward in child context; both must pass.
- When a condition is true, the branch becomes ready and follows the existing attempt lifecycle.
- When a condition is false, one durable skipped outcome is recorded and no attempt or turn is consumed.
- When a downstream step depends on completed and skipped branches, it becomes ready only after every branch reaches either terminal state.
- When a run is replayed, recorded branch decisions and ordered outputs are restored without condition re-evaluation.
- When status is requested, skipped instances and their condition summaries are distinct from failed and pending instances.

### Unit Tests — Workflow outputs and aggregation

- When an included workflow completes with a valid declared output, its parent alias publishes one result envelope.
- When an included workflow output is missing or violates its schema, the alias does not publish the result and the join remains blocked by the failed branch.
- When parallel branch instances finish out of order, alias results remain ordered by source item and declaration order.
- When every instance of an optional alias is skipped, its result interpolation is an empty array.
- When a join interpolates multiple alias result collections, the downstream aggregation step receives JSON-compatible values conforming to the shared review-result schema.

### Unit Tests — Workflow inputs and dynamic include groups

- Top-level parameters and include `with` mappings validate against the same declared workflow input schemas.
- Missing, unknown, or schema-invalid mapped inputs fail before the child workflow instance starts.
- One iterated include creates one complete instance-scoped child DAG per matching source item rather than applying iteration independently to every child step.
- A child workflow cannot read undeclared parent parameters, parent step outputs, or another child instance's context.

### Integration Tests — Health-check routing

- When health-check starts, MCP classifies files and units before returning agent-owned review work; no agent response supplies routing tags or branch decisions.
- When breakdown returns a Swift view and a non-view Swift unit, the general review runs for applicable units and the SwiftUI review runs only for the view.
- When breakdown returns no Swift views, the SwiftUI branch records skipped instances and the final aggregation still completes.
- When two specialized branch conditions match one unit, both workflows execute and both results reach the final aggregation step.
- When one selected review workflow exhausts retries, the final aggregation does not execute and the run reports the existing failure outcome.
- When a conditional health-check run is interrupted and resumed, completed reviews are not repeated and skipped branches remain skipped.

### Live Model E2E — Swappable classification prompt and conditional routing

- The test copies the fixed E2E workflow package to a temporary directory and writes `prompts/classify.md` before launching the model session; the workflow YAML and branch definitions remain identical between cases.
- The spawned Codex or Claude session receives only the temporary workflow path and instructions to drive the flow to a terminal state. Its launch prompt does not contain the injected classification text, expected category, or expected branch.
- With an unambiguous question injected into `classify.md`, the classification step emits `category: question`, the question branch emits its exact required sentence, the statement branch records one durable skipped outcome, and the run completes without retries or failures.
- With an unambiguous statement injected into `classify.md`, the classification step emits `category: statement`, the statement branch emits its exact required sentence, the question branch records one durable skipped outcome, and the run completes without retries or failures.
- A fan-out case uses an engine-owned preparation step to emit multiple already categorized source units, then expands per-item conditional steps over those units with `for_each`. For mixed question and statement units, each conditional step completes only its matching instance, skips its non-matching instance, preserves source order, consumes no attempt or turn for skips, and reaches `run_completed`.

## Definition of Done

- [ ] Flow definitions accept and validate the same declarative `when` grammar at workflow, include-invocation, and step scopes.
- [ ] Workflow-level conditions evaluate against validated declared inputs and can skip a complete top-level or included workflow instance.
- [ ] Step-level conditions evaluate after dependencies and per-instance `for_each` expansion, skipping only the addressed step instance.
- [ ] Conditional workflow includes support dependency waiting and per-item fan-out without executing false branches.
- [ ] Workflow inputs and include `with` mappings provide explicit, schema-validated child values without ambient parent-context access.
- [ ] Skipped outcomes are durable, replayable, terminal for dependency joins, and visible through flow status.
- [ ] Workflow packages can declare schema-validated outputs exposed through stable alias result collections.
- [ ] Downstream aggregation steps receive deterministic results from every completed matching branch and no results from skipped branches.
- [ ] Existing unconditional workflows remain backward compatible.
- [ ] The health-check integration proves SwiftUI routing by language and unit kind followed by normalized result aggregation.
- [ ] Shared Codex and Claude live E2E tests prove that prompt-file content can be swapped without changing workflow YAML or exposing test expectations in the launch prompt, and that model-produced categories deterministically select the matching conditional branch.
- [ ] A live E2E fan-out case proves per-item `for_each` condition evaluation with mixed categories, completed matching instances, and durable non-matching skips.
- [ ] Unit and integration tests cover validation, execution, failure, ordering, status, and resume behavior.
- [ ] Existing `for_each` characterization tests pass unchanged before and after conditional routing is added.
