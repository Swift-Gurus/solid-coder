# Workflow YAML Reference

This document is the author-facing contract for the current solid-coder flow
engine. It describes YAML that the runtime actually loads today. Design specs
may describe planned behavior that is not yet enforced; when they differ, this
document calls out the current runtime limitation explicitly.

## Quick start

A discoverable workflow is a directory containing `workflow.yaml`:

```text
.solid-coder/workflows/
  research/
    workflow.yaml
```

```yaml
id: research
name: Research with the user
description: Collect three facts from the user in order.
max_turns: 3

steps:
  - id: ask_name
    prompt: |
      Ask the user for their first name. Do not infer it. After the user
      answers, submit the answer as the `name` output.
    outputs:
      - name: name
        type: data
        schema:
          type: string
          minLength: 1

  - id: ask_last_name
    depends_on: [ask_name]
    prompt: |
      Ask the user for their last name. After the user answers, submit the
      answer as the `last_name` output.
    outputs:
      - name: last_name
        type: data
        schema:
          type: string
          minLength: 1

  - id: ask_birthday
    depends_on: [ask_last_name]
    prompt: |
      Ask the user for their birthday. After the user answers, submit the
      answer as the `birthday` output.
    outputs:
      - name: birthday
        type: data
        schema:
          type: string
          minLength: 1
```

Start it by public ID:

```text
flow_start({"flow": "research", "params": {}})
```

The engine returns one current step and an opaque instance ID. After completing
that step, submit its values under the returned ID:

```json
{
  "outputs": {
    "ask_name-1": {
      "name": "Alex"
    }
  }
}
```

Never construct or predict an instance ID. Always use the ID returned by the
latest `flow_start` or `flow_next` response.

## Why `type: string` fails

The output declaration has two type layers:

```yaml
outputs:
  - name: name
    type: data       # flow-engine output transport type
    schema:
      type: string   # JSON Schema value type
```

The flow-engine output transport type is a closed set:

| Output type | Meaning |
|---|---|
| `data` | An inline JSON value, optionally validated by JSON Schema. |
| `file` | A filesystem path; the engine checks that the path exists. |

`string`, `integer`, `number`, `boolean`, `object`, and `array` are JSON
Schema types. They are valid under `schema`, not as the output declaration's
top-level `type`.

Therefore this is invalid:

```yaml
- name: name
  type: string
```

It fails at submission time with `Unknown output type: 'string'`.

## Workflow package discovery

Public workflow packages are discovered recursively from:

```text
{project}/.solid-coder/workflows/**/workflow.yaml
{plugin}/workflows/**/workflow.yaml
```

Folder names organize packages but do not identify or execute them. The public
identity is the workflow's `id`. Discovery never automatically runs every
workflow in a folder.

One `flow_start` selects exactly one workflow by ID or by an explicit YAML path.
Only its authored steps and explicit includes are reachable.

Public IDs must match:

```text
^[a-z0-9]+(?:[-/][a-z0-9]+)*$
```

Examples: `research`, `solid-review`, `review/swift`. A duplicate ID anywhere
in the combined project and plugin catalog is an error; project workflows do
not silently override bundled workflows.

For a discoverable package, these fields are required and validated during
catalog construction:

| Field | Type | Requirement |
|---|---|---|
| `id` | string | Required; must match the public-ID pattern. |
| `name` | string | Required; non-empty after trimming. |
| `max_turns` | integer | Required; at least `1`. |
| `steps` | array | Required; at least one entry. |

An explicit YAML path can currently receive looser defaults, but package-style
documents should always declare all four fields.

## Workflow root fields

```yaml
id: example
name: Example workflow
description: Human-readable purpose.
max_turns: 20

execution:                    # optional; granular is the default
  mode: granular

presentation:                 # optional; individual is the default
  mode: individual

when:                         # optional workflow-level condition
  ref: "{{params.enabled}}"
  equals: true

rule:                         # optional; enrolls this as a review rule
  scope: unit
  match: {}

outputs:                      # optional public outputs when included by a parent
  - name: result
    type: data
    value: "{{steps.finish.outputs.result}}"
    schema:
      type: string

steps: []
```

| Field | Purpose |
|---|---|
| `id` | Stable catalog ID. |
| `name` | Human-readable name stored with the run. |
| `description` | Informational package description. |
| `max_turns` | Circuit breaker for successful model-owned step submissions. It is not the per-step retry count. |
| `execution.mode` | `granular` returns compatible model-owned steps separately; `aggregate` compiles a compatible dependency phase into one submission contract. |
| `presentation.mode` | `individual` presents eligible children separately; `combined` combines compatible rule instructions and outputs without changing rule identity. |
| `when` | Eligibility condition evaluated once before any step executes. At the root, reference `params` only. |
| `rule` | Enrolls the workflow in the review-rule catalog. See [Review rule workflows](#review-rule-workflows). |
| `outputs` | Values published to a parent when this workflow is included. |
| `steps` | Ordered declarations used to construct the DAG. YAML order is not a dependency. |

### Current `inputs:` limitation

`flow_start.params` and include-level `with` mappings are functional. Included
steps receive mapped values as `params.<name>`. However, a root `inputs:` list
is not currently decoded or schema-validated by the production loader. An
`inputs:` declaration appears in an E2E fixture, but it is documentary today.

Do not rely on `inputs:` to reject missing, unknown, or incorrectly shaped
values until input declaration validation is implemented. An unresolved
`params.<name>` expression still fails when the workflow tries to render it.

## DAG and turn semantics

`steps` is a DAG, not a script. Use `depends_on` to express ordering:

```yaml
- id: first
  prompt: Do the first task.

- id: second
  depends_on: [first]
  prompt: Do the second task.
```

Without `depends_on`, both steps are ready independently. The model-facing
renderer currently returns one ready step at a time, but that presentation
choice does not create a data or ordering dependency.

Rules enforced at load time include:

- every step has a non-empty, unique `id`;
- every dependency names a known step or include alias;
- the graph is acyclic;
- an include alias cannot collide with a top-level step ID;
- callers depend on an include alias, not a private child step;
- `for_each` references a declared array output from a transitive dependency.

`max_turns` counts successful externally submitted transitions. Engine-owned
commands, scripts, operations, and skipped branches are drained automatically.
Failed submissions consume `max_attempts`, not `max_turns`.

Every ordinary step defaults to:

```yaml
max_attempts: 3
```

After the attempts are exhausted, the run fails. A model-owned step with no
declared outputs is completed by submitting an empty object for its current
instance ID.

## Common step fields

```yaml
- id: step_id
  type: agent
  depends_on: [other_step]
  for_each:
    source: "{{steps.other_step.outputs.items}}"
    mode: batch
    label: "{{item.name}}"
  when:
    ref: "{{item.enabled}}"
    equals: true
  max_attempts: 3
  outputs: []
```

| Field | Meaning |
|---|---|
| `id` | Required identity local to the workflow. Prefer `snake_case` for predictable references. |
| `type` | Execution owner. Omit for `agent`. |
| `depends_on` | Array of prerequisite step IDs or include aliases. |
| `for_each` | Array-valued output reference, or a structured source/mode/label declaration, used to create one instance per item. |
| `when` | Conditional execution; a false condition records an auditable skip. |
| `max_attempts` | Maximum failed submissions or executions for this step; default `3`. |
| `outputs` | Named values validated when the step completes. |

Type-specific fields are described below. Do not add fields belonging to a
different type merely because the YAML parser accepts arbitrary mappings at an
earlier boundary; the resolved workflow validator may reject them or they may
be ignored.

## Step types

### Agent step

`agent` is the default. It is returned to the calling model and completed by a
`flow_next` submission.

```yaml
- id: classify
  type: agent              # optional because agent is the default
  prompt: |
    Classify the supplied text.
  outputs:
    - name: category
      type: data
      schema:
        type: string
        enum: [question, statement]
```

An agent step must declare exactly one of `prompt` and `prompt_file`:

```yaml
- id: classify
  prompt_file: classify.md
```

It must not declare `command`, `file`, `args`, or `operation`.

### Command step

A command is owned and executed by MCP. The scalar command is passed to the
selected shell as `<executor> -lc <command>`.

```yaml
- id: inspect_environment
  type: command
  executor: bash           # optional; defaults to bash
  command: >-
    printf '%s\n' '{"ready": true}'
  timeout_seconds: 30
  outputs:
    - name: ready
      type: data
      schema:
        type: boolean
```

Requirements:

- `command` is one non-empty string;
- `executor` is optional and defaults to `bash`;
- the executor must be listed in `[flow_engine].permitted_executables`;
- `file`, `args`, `prompt`, and `prompt_file` are forbidden;
- stdout must be exactly one JSON object containing the declared outputs;
- a non-zero exit, timeout, invalid JSON, or schema mismatch is a failed attempt.

### Script step

The preferred structured form names a package script separately from its
executor and arguments:

```yaml
- id: prepare_units
  type: script
  file: prepare_units.py
  executor: python3
  args:
    - "{{params.source_path}}"
  timeout_seconds: 30
  outputs:
    - name: units
      type: data
      schema:
        type: array
        items:
          type: object
```

`file: prepare_units.py` resolves from the package's `scripts/` directory.
`executor` defaults to `bash`, so Python scripts should explicitly declare
`executor: python3`. The executor must be allowlisted. As with command steps,
stdout must be exactly one JSON object.

The legacy array form is still accepted:

```yaml
- id: legacy_script
  type: script
  command: [python3, scripts/prepare_units.py]
```

The legacy form cannot be mixed with `file`, `executor`, or `args`. New package
workflows should use the structured form.

### Operation step

An operation is a typed, in-process MCP capability. It does not call an MCP
tool through a model and does not expose its internal inputs to the model.

```yaml
- id: prepare_review
  type: operation
  operation: review.prepare
  with:
    target: "{{params.target}}"
```

The operation registry defines required inputs, optional inputs, and outputs.
The loader rejects unknown operations, missing inputs, and unknown inputs.
Operation outputs are generated from the registered Pydantic result model;
authors must not duplicate an `outputs` block.

Current production operations:

`source.analyze` exposes one named `result` containing its complete typed analysis.
For example, `{{steps.inspect.outputs.result}}` is one analysis for an ordinary
step, or an ordered array of complete analyses when `inspect` uses `for_each`.
The underlying analysis service still returns the analysis model directly.

`source.resolve_relationships` accepts that array as `analyses`. It exposes
`result` (the complete bounded inventory) and `relationships` (its ordered links).
Use `{{steps.link.outputs.relationships}}` for iteration, and pass
`{{steps.link.outputs.result}}` plus `{{item}}` to `source.match_requirements` as
`inventory` and `relationship`. Its named outputs are `inventory`, `relationship`,
and `matches`. An inherited-type relationship is required for requirement matching;
use an authored `when` condition to exclude other link kinds.

`source.declaration_members` accepts `inventory` and a prepared `declaration`
identity (`source_identity`, `unit_identity`, and `granularity: unit`). The identity
must belong to the supplied inventory; it is MCP-owned data, not an identifier
the model should invent. Its named outputs are `inventory`, `declaration`, and
`members`. Each member retains its owner, source evidence, visibility, matching
declarations, and a structural role: `declared`, `implementation`, `additional`,
or `unresolved`. Supported default implementations do not become additional
declarations. Conformer-only members are not part of the selected interface's
member collection. Visibility filtering and scoring remain workflow policy.
Ambiguous ownership, conditional applicability, unsupported signatures, and
unresolved inherited-member identity retain uncertainty rather than asserting
an exact additional-member count. This operation does not perform discovery or
read source files again.

Typed operation-output schemas expose referenced nested fields to collection
conditions while retaining definitions for validation and recursive references.
For example, `item.role` and `item.reference.member.visibility` can be used in a
metric's `scoring.when` without duplicating the operation schema in YAML.

These bindings use the existing named-output contract. They do not require
whole-step references, nested YAML objects in `with`, or LLM reconstruction of
parsed facts. Candidate and unresolved results do not prove semantic conformance
or complete repository discovery.

`source.discover_declaration` starts from a prepared `target` and authoritative
source `context`. It searches the exact declaration name, analyzes bounded hits,
and uses discovered owner names to find separate extensions when needed. It
publishes `inventory`, `declaration`, `related_declarations`, `limitations`,
`queries`, and `searches`. Prospective source snapshots override matching disk
content. The initial search is not broadened by synonyms or tags; candidate caps,
unreadable/truncated sources, and unresolved analysis remain explicit limitations.
This composes search and analysis; ordinary `source.search` remains parser-free.

| Operation | Required `with` inputs | Optional `with` inputs |
|---|---|---|
| `review.prepare` | `target` | `context_sources` |
| `source.collect_changes` | `project_root` | — |
| `source.analyze` | `source` | — |
| `source.resolve_relationships` | `analyses` | — |
| `source.match_requirements` | `inventory`, `relationship` | — |
| `source.declaration_members` | `inventory`, `declaration` | — |
| `source.discover_declaration` | `target`, `context` | `max_candidates`, `max_bytes_per_candidate` |
| `source.prepare_search_targets` | `source`, `granularity` | — |
| `source.prepare_search_query` | `target`, `generated_terms` | — |
| `source.search` | `queries` | `excluded_units`, `context`, `included_file_extensions`, `max_candidates` |
| `source.present_search` | `candidates`, `files_scanned` | — |
| `source.validate_candidate_selection` | `candidates`, `selections` | — |
| `source.read_candidates` | `candidates` | `context`, `max_bytes_per_candidate` |

`source` and `target` inputs use sealed objects. The two accepted source forms
are:

```yaml
# File-backed source
kind: file
path: /absolute/path/to/File.swift
```

```yaml
# In-memory source
kind: text
text: "class Example {}"
virtual_path: Sources/Example.swift   # optional
file_extension: .swift               # optional
```

Operation `with` values are workflow expressions, not arbitrary YAML literals.
Pass constants through `flow_start.params` when necessary and bind them with
`{{params.<name>}}`.

### Delegate step

A delegate step has a prompt and an explicit mode:

```yaml
- id: review_children
  type: delegate
  mode: session
  prompt: |
    Review {{item}} and return the declared outputs.
  for_each: "{{steps.prepare.outputs.items}}"
  depends_on: [prepare]
  outputs:
    - name: finding
      type: data
      schema:
        type: string
```

Supported modes:

| Mode | Behavior |
|---|---|
| `session` | MCP starts configured model sessions. A fan-out is executed with bounded concurrency and results remain source-ordered. |
| `subagent` | The current model receives an instruction to launch an isolated child flow and later submits its outputs. |

`[flow_engine].max_parallel_sessions` bounds session delegate concurrency and
defaults to `4`. A delegate must declare a prompt (inline or resolved from a
`prompt_file`) and must not declare a command.

### Metric and exception steps

`metric` and `exception` are model-owned steps available only inside a workflow
with a root `rule` declaration. Their output contracts are generated by the
engine. See [Review rule workflows](#review-rule-workflows).

## Step outputs

### Inline data schema

```yaml
outputs:
  - name: person
    type: data
    schema:
      type: object
      required: [name, age]
      properties:
        name:
          type: string
          minLength: 1
        age:
          type: integer
          minimum: 0
      additionalProperties: false
```

### File-backed data schema

```yaml
outputs:
  - name: findings
    type: data
    schema_file: findings.schema.json
```

Declare at most one of `schema` and `schema_file`. A bare
`findings.schema.json` resolves from the package's `schemas/` folder.

`type: data` without a schema accepts any inline value, including `null`. Use a
schema when the shape matters.

### File output

```yaml
outputs:
  - name: report_path
    type: file
```

The submitted value is converted to a path string and must exist when the step
is validated.

### Submission shape

The outer key is the current instance ID. The inner object maps every declared
output name to its value:

```json
{
  "outputs": {
    "classify-1": {
      "category": "question"
    }
  }
}
```

The engine validates declared values. The rendered prompt also asks the model
to avoid additional properties. Currently, unexpected extra keys in the inner
submission object are not independently rejected by the runtime, so authors
must not use them as an undeclared data channel.

## Expressions and interpolation

Expressions may be written with or without braces where a field expects a
whole expression. Prompts use `{{...}}` interpolation.

Supported namespaces:

| Expression | Value |
|---|---|
| `params.name` | A `flow_start.params` value, or a child value supplied through include `with`. |
| `steps.step_id.outputs.output_name` | A completed local step output. |
| `item` / `item.field` | The current `for_each` item. |
| `workflows.alias.results` | Ordered result envelopes published by an included workflow. |
| `rejection_reasons.step_id` | Latest recorded rejection reason for retry-aware prompts. |
| `attempts_used.step_id` | Failed-attempt count for retry-aware prompts. |

The only supported expression filter is `length`:

```yaml
prompt: >-
  There are {{steps.prepare.outputs.items | length}} items.
```

References are scope-aware. An included workflow sees its mapped `params`, its
own local step outputs, its own `item`, and workflow results visible within its
scope. It does not receive ambient parent parameters unless the parent maps
them with `with`.

A step-output expression selects one declared output. It does not traverse
inside that output's JSON value. For example,
`steps.analyze.outputs.dependencies` is valid when `dependencies` is an output;
`steps.analyze.outputs.analysis.dependencies` is not a nested-property query.
Publish a collection as its own named output when `for_each` or
`scoring.source` must consume it.

When a fanned-out step completes, its parent step output is an ordered list of
the per-instance values. For example,
`{{steps.review.outputs.finding}}` resolves to a list after every `review`
instance reaches a terminal completed state.

## `for_each`

The compact form accepts a step-output reference and presents instances
individually:

```yaml
- id: prepare
  prompt: Return items.
  outputs:
    - name: items
      type: data
      schema:
        type: array
        items:
          type: object

- id: inspect
  depends_on: [prepare]
  for_each: "{{steps.prepare.outputs.items}}"
  prompt: Inspect {{item}}.
```

The structured form controls model presentation without changing per-item
execution identity:

```yaml
- id: inspect
  depends_on: [prepare]
  for_each:
    source: "{{steps.prepare.outputs.items}}"
    mode: batch
    label: "{{item.name}}"
  prompt: Inspect {{item}}.
```

| Field | Values | Meaning |
|---|---|---|
| `source` | Step-output expression | Required array-valued source. |
| `mode` | `individual`, `batch` | `individual` returns one item at a time. `batch` presents ready sibling instances together and validates coverage by item. |
| `label` | Workflow expression | Optional stable, human-readable item label used in a batch submission. It does not replace the engine-owned instance identity. |

The source output must:

- exist;
- declare `schema.type: array`;
- come from a transitive dependency of the iterated step or include.

An empty array creates no instances and completes that fan-out without model
work. `item` exposes the current value; no authored `index` expression is
currently available.

## Execution and presentation modes

Execution and presentation are independent:

```yaml
- group: aggregate_rule_reviews
  execution:
    mode: aggregate
  presentation:
    mode: combined
  steps:
    - include:
        rules: all
      as: rule_reviews
      depends_on: [prepare_review]
      for_each:
        source: "{{steps.prepare_review.outputs.units}}"
        mode: batch
        label: "{{item.target.name}}"
      with:
        review_unit: "{{item}}"
```

| Declaration | Default | Effect |
|---|---|---|
| `execution.mode: granular` | Yes | Preserve ordinary step-by-step model transitions. |
| `execution.mode: aggregate` | No | Compile compatible model-owned steps in the same dependency phase into one model submission. Engine-owned commands, scripts, operations, and collection-backed metrics remain phase boundaries and run internally. |
| `presentation.mode: individual` | Yes | Present eligible child rules independently. |
| `presentation.mode: combined` | No | Deduplicate shared authored instructions and present compatible rule contracts together while retaining each rule, metric, exception, and result identity. |

`combined` is not a scoring mode and `aggregate` does not flatten the DAG.
Dependencies, conditions, retries, audit events, replay identities, and child
workflow ownership remain intact. A nested workflow may declare its own modes;
an explicitly owned boundary applies within its own scope rather than silently
rewriting unrelated parent or child execution.

## Conditions

`when` is valid at three scopes:

- workflow root: evaluated once before any internal step;
- include entry: evaluated in the parent context before the child starts;
- step: evaluated for each ready step instance.

A false condition records a skip event. Skipped work is terminal for dependency
resolution and is restored from the event log during replay; it is not silently
re-evaluated on resume.

### Comparisons

Every comparison declares one `ref` and exactly one operator:

```yaml
when:
  ref: "{{steps.classify.outputs.category}}"
  equals: question
```

| Operator | Meaning |
|---|---|
| `equals` | Actual and expected have the same runtime type and value. |
| `not_equals` | Type-strict inequality. |
| `in` | Actual value is a member of the expected YAML array. |
| `not_in` | Actual value is not a member of the expected YAML array. |
| `contains` | Actual list contains the expected value. This is list membership, not substring matching. |
| `not_contains` | Actual list does not contain the expected value. |
| `exists` | The reference is present (`true`) or absent (`false`). |

Comparisons do not coerce values: `1`, `1.0`, and `"1"` are different.
`in`/`not_in` require an array comparison value, and `exists` requires a
boolean.

### Composition

```yaml
when:
  all:
    - ref: "{{item.file_extension}}"
      equals: .swift
    - any:
        - ref: "{{item.tags}}"
          contains: swiftui
        - ref: "{{item.tags}}"
          contains: uikit
    - not:
        ref: "{{item.unit_kind}}"
        equals: protocol
```

`all` and `any` require a non-empty condition list. `not` wraps exactly one
condition. Composition nodes cannot contain unrelated sibling fields.

## Reuse and composition

### Reusable step fragment with `uses`

Package layout:

```text
my-workflow/
  workflow.yaml
  steps/
    classify.yaml
```

`steps/classify.yaml` contains one step mapping:

```yaml
id: classify
prompt: Classify the input.
outputs:
  - name: category
    type: data
    schema:
      type: string
```

Use it from `workflow.yaml`:

```yaml
steps:
  - uses: classify.yaml
    depends_on: [prepare]
```

Fields declared beside `uses` overlay the fragment. A bare filename resolves
from `steps/`; an explicit relative path resolves from the declaring YAML file.

### Include a private subflow by path

```yaml
- include: review_unit.yaml
  as: unit_review
```

A bare filename resolves from the package's `subflows/` directory. Path-based
includes are private package composition.

### Include a public workflow by ID

```yaml
- include:
    workflow: solid-file-review
  as: file_review
```

Cross-package composition should use the stable public workflow ID rather than
`../` paths.

### Include every enabled review rule

```yaml
- include:
    rules: all
  as: rule_reviews
  depends_on: [prepare_review]
  for_each: "{{steps.prepare_review.outputs.units}}"
  with:
    review_file: "{{steps.prepare_review.outputs.review_file}}"
    review_unit: "{{item}}"
    source_context: "{{steps.prepare_review.outputs.source_context}}"
```

`rules: all` expands only catalog workflows with a root `rule` declaration. It
applies the project's review policy, compiles each rule's match declaration
into conditions, and orders members by workflow ID. It does not mean all
workflows in a folder.

Unit-scoped rules preserve the include fan-out. File-scoped rules remove the
unit fan-out and receive `review_file` as their `review_unit` input.

### Include runtime fields

Path, workflow-ID, and rule-set includes support:

```yaml
- include:
    workflow: child-workflow
  as: child
  depends_on: [prepare]
  for_each: "{{steps.prepare.outputs.items}}"
  with:
    child_input: "{{item}}"
    shared_value: "{{params.shared_value}}"
  when:
    ref: "{{item.enabled}}"
    equals: true
```

`as` is required and becomes the opaque DAG node used by downstream
`depends_on`. `with` maps child parameter names to parent-context expressions.
Each mapped value preserves its runtime type.

### Inline group

An inline group gives several local steps one opaque dependency name:

```yaml
- group: preparation
  steps:
    - id: load
      prompt: Load input.
    - id: normalize
      depends_on: [load]
      prompt: Normalize input.

- id: consume
  depends_on: [preparation]
  prompt: Consume the prepared input.
```

The group must contain at least one step. Callers depend on the group name, not
its internal step IDs.

## Reusable workflow outputs

A child workflow publishes selected internal outputs at its root:

```yaml
id: child-review
name: Child review
max_turns: 5

outputs:
  - name: report
    type: data
    value: "{{steps.finish.outputs.report}}"
    schema:
      type: string

steps:
  - id: finish
    prompt: Return the report.
    outputs:
      - name: report
        type: data
        schema:
          type: string
```

`value` must reference an internal step output using
`steps.<id>.outputs.<name>`. `schema` and `schema_file` follow the same rules as
step outputs.

The parent reads the included alias's ordered result collection:

```yaml
- include:
    workflow: child-review
  as: reviews
  for_each: "{{steps.prepare.outputs.items}}"
  depends_on: [prepare]
  with:
    review_item: "{{item}}"

- id: aggregate
  depends_on: [reviews]
  prompt: |
    Aggregate these results: {{workflows.reviews.results}}
```

Each result envelope has this shape:

```json
{
  "instance_id": "reviews-1",
  "item": {},
  "outputs": {
    "report": "..."
  }
}
```

The collection is ordered by the include source order. Skipped child instances
are omitted. A non-iterated include uses the same zero-or-one-item collection
shape.

## Package resources

All resource folders are optional. Files load only when referenced.

```text
workflow-package/
  workflow.yaml
  prompts/
  schemas/
  steps/
  subflows/
  scripts/
```

Bare filenames use the conventional folder for their field:

| Field | Bare filename base |
|---|---|
| `prompt_file` | `prompts/` |
| `schema_file` | `schemas/` |
| `uses` | `steps/` |
| path `include` | `subflows/` |
| script `file` | `scripts/` |

Other reference forms:

| Form | Resolution |
|---|---|
| `review.md` | Conventional folder for that field. |
| `prompts/special/review.md` | Relative to the YAML file that declares it. |
| `$package/shared/review.md` | Relative to the owning package root. |
| `/absolute/path` | Absolute, but a packaged reference must still remain inside its package root. |

Packaged resources may not escape the nearest directory owning a
`workflow.yaml`.

## Review rule workflows

A root `rule` declaration enrolls a workflow for `rules: all` expansion.

```yaml
id: example-rule
name: Example rule
max_turns: 10

rule:
  scope: unit
  match:
    file_extensions:
      included: [.swift]
      excluded: []
    unit_kinds:
      included: [class, struct]
      excluded: [protocol]
    tags:
      included: [swiftui]
      excluded: [tests]

steps:
  - id: complexity
    type: metric
    metric_id: EXAMPLE-1
    prompt: Measure the unit's complexity.
    value:
      type: integer
      minimum: 0
    scoring:
      minor:
        operator: greater_than_or_equal
        value: 5
      severe:
        operator: greater_than_or_equal
        value: 10

  - id: classify_exception
    type: exception
    depends_on: [complexity]
    prompt: Decide whether the documented exception applies.
```

### Rule fields

| Field | Values | Default |
|---|---|---|
| `scope` | `unit`, `file` | `unit` |
| `match.file_extensions` | `included` / `excluded` lowercase suffixes beginning with `.` | unrestricted |
| `match.unit_kinds` | `class`, `struct`, `enum`, `protocol`, `extension`, `actor`, `function`, `document` | unrestricted |
| `match.tags` | `included` / `excluded` normalized lowercase single-word tags | unrestricted |

Missing `included` means all values are eligible except `excluded`. A value may
not appear in both lists, and duplicates are rejected.

Every rule workflow must contain at least one `metric` step and exactly one
`exception` step. Metric and exception steps may not author `outputs`; the
engine generates their audited contracts.

### Metric declaration

```yaml
- id: dependency_count
  type: metric
  metric_id: OCP-1
  observation_id: value       # optional; defaults to value
  prompt: Count dependencies.
  value:
    type: integer
    minimum: 0
    maximum: 100
  scoring:
    minor:
      operator: greater_than_or_equal
      value: 2
    severe:
      operator: greater_than
      value: 5
```

Metric value types are `integer`, `number`, `string`, and `boolean`. Only
numeric types accept `minimum` and `maximum`.

Scoring must define at least one of `minor` and `severe`. Operators are:

- `greater_than`
- `greater_than_or_equal`
- `less_than`
- `less_than_or_equal`
- `equals`
- `not_equals`

String and boolean metrics support only `equals` and `not_equals`. Threshold
values must have the metric's corresponding type.

### Unavailable metric evidence

An explicitly guarded metric can declare `unavailable_reason` when its condition
means required evidence is insufficient:

```yaml
- id: coverage
  type: metric
  metric_id: EXAMPLE-2
  depends_on: [classify]
  when:
    ref: "{{steps.classify.outputs.available}}"
    equals: true
  unavailable_reason: Required implementation evidence could not be verified.
  value: {type: integer, minimum: 0}
  scoring:
    source: "{{steps.classify.outputs.observations}}"
    severe: {operator: greater_than_or_equal, value: 1}
```

If the condition skips this metric, its rule result records an entry in
`unavailable_metrics`: `metric_id`, `observation_id`, `status: unavailable`, and
`additional_info` containing the authored reasoning and persisted condition
evidence. That entry has **no value or severity**. Ordinary skipped metrics
without `unavailable_reason` retain ordinary skip semantics.

Measured siblings keep their actual scores, including known SEVERE findings.
An entirely unavailable rule has `severity: null`, not COMPLIANT; a review with
no measured rule severity also has `severity: null`. The enclosing rule result
retains rule-instance and reviewed-unit provenance. Replay restores the same
condition evidence and result without rerunning discovery.

Missing or invalid submissions remain pending/rejected; operation failures remain
failures. Neither becomes an unavailable measurement. This field does not define
a universal allow/block policy for the write gate.

### Collection-backed deterministic metric

An ordinary metric asks the model to submit its scalar `value`. When the model
instead returns a typed collection of observations, MCP can derive an integer
metric by counting entries:

```yaml
- id: analyze_task_sites
  type: agent
  prompt: Classify every task creation site.
  outputs:
    - name: task_sites
      type: data
      schema:
        type: array
        items:
          type: object
          additionalProperties: false
          required: [classification, is_exception, reasoning, evidence]
          properties:
            classification:
              type: string
              enum: [DETACHED, UNSTRUCTURED, STRUCTURED]
            is_exception: {type: boolean}
            reasoning: {type: string, minLength: 1}
            evidence: {type: string, minLength: 1}

- id: detached_task_count
  type: metric
  metric_id: DT-1
  depends_on: [analyze_task_sites]
  value:
    type: integer
    minimum: 0
  scoring:
    source: "{{steps.analyze_task_sites.outputs.task_sites}}"
    when:
      all:
        - ref: "{{item.classification}}"
          equals: DETACHED
        - ref: "{{item.is_exception}}"
          equals: false
    severe:
      operator: greater_than_or_equal
      value: 1
```

Here the model classifies and supplies evidence; MCP performs the count and
severity decision. The metric itself causes no model turn.

| Field | Meaning |
|---|---|
| `scoring.source` | A visible upstream array output. The source step must be a dependency. |
| `scoring.when` | Optional existing condition grammar evaluated once per source entry with that entry bound as `item`. Omit it to count every entry. |
| `value` | Must be `type: integer` because the deterministic operation is a count. |
| `minor` / `severe` | Existing scalar severity bands applied to the derived count. |

Collection-backed metric restrictions:

- the source output schema must declare `type: array`;
- condition fields such as `item.classification` must exist in the array item
  schema;
- the metric must not declare `prompt`, `prompt_file`, authored `outputs`,
  `for_each`, a command/script, an operation, or a delegate mode;
- source order is preserved and equal entries at different indexes are each
  counted;
- an empty collection produces zero;
- a missing or unresolvable source is an error, not zero;
- step-level `when` decides whether the metric node runs, whereas
  `scoring.when` decides which source entries contribute to its count.

Without `scoring.reducer`, this is a filtered count, not a general expression language. It
does not perform sums, joins, averages, custom code, or inferred arithmetic.
If a metric needs fields from two analyses, first make an upstream step publish
one typed collection containing every field required by the filter.

### Co-located deterministic metrics

When a metric reads one data output from the same agent step, it may be authored
beside that output instead of as a repetitive sibling step:

```yaml
- id: analyze_task_sites
  type: agent
  prompt: Classify every task creation site.
  outputs:
    - name: task_sites
      type: data
      schema:
        type: array
        items:
          type: object
          additionalProperties: false
          required: [classification, is_exception]
          properties:
            classification: {type: string}
            is_exception: {type: boolean}
  metrics:
    - id: detached_task_count
      metric_id: DT-1
      value: {type: integer, minimum: 0}
      scoring:
        source: task_sites
        when:
          all:
            - ref: "{{item.classification}}"
              equals: DETACHED
            - ref: "{{item.is_exception}}"
              equals: false
        severe: {operator: greater_than_or_equal, value: 1}
```

`metrics[].scoring.source` is the exact name of a data output on the owning
agent step. It is not a template expression. The engine normalizes each entry
into an ordinary engine-owned `type: metric` step, so filtering, reducers,
severity, policy, events, replay, results, and audit use the same runtime path.
The model submits `task_sites` once and never submits the derived count.

Use an explicit `type: metric` step when the metric reads another step, depends
on multiple steps, needs step-level `when`, has independent `for_each` or
scheduling, or asks the model for a scalar measurement. Direct `for_each` on an
agent that declares `metrics` is rejected in the initial contract; put the
agent and compact metric inside an included workflow that is fanned out, or use
an explicit metric step.

The generated metric submission is:

```json
{
  "value": 3,
  "additional_info": {
    "reasoning": "Why this measurement is correct.",
    "evidence": "Precise source evidence or line reference."
  }
}
```

The generated exception submission is:

```json
{
  "is_exception": false,
  "additional_info": {
    "reasoning": "Why the exception does or does not apply.",
    "evidence": "Precise source evidence or line reference."
  }
}
```

`additional_info.reasoning` and `additional_info.evidence` are required,
non-empty strings for auditability.

### Connected-component metrics

Use `component_count` when collection items form groups through shared scalar
values. The model supplies facts; MCP filters the items, finds intersections,
merges transitive connections, and scores the number of groups.

```yaml
- id: analyze_resources
  type: agent
  prompt: Classify the resources used by every item and whether that item is excluded.
  outputs:
    - name: items
      type: data
      schema:
        type: array
        items:
          type: object
          required: [resources, excluded]
          properties:
            resources:
              type: array
              items: {type: string}
            excluded: {type: boolean}
  metrics:
    - id: groups
      metric_id: RESOURCE-GROUPS
      value: {type: integer, minimum: 0}
      scoring:
        source: items
        when:
          ref: "{{item.excluded}}"
          equals: false
        reducer:
          type: component_count
          relation:
            operator: intersects
            left: "{{left.resources}}"
            right: "{{right.resources}}"
        severe: {operator: greater_than_or_equal, value: 2}
```

The same reducer works on an explicit `type: metric` step with its ordinary
`scoring.source` reference, including projected child-workflow outputs.

- `left` and `right` refer to the two compared items. Their fields must be
  declared arrays with a scalar item schema (`string`, `integer`, `number`,
  `boolean`, or `null`). They are references, not executable expressions.
- `scoring.when` filters first. An excluded item cannot bridge two groups.
- `{cache}`, `{cache, storage}`, and `{storage}` form one transitive group.
- Empty selected input produces zero. Each isolated item, including an item
  with an empty set, contributes one group.
- Equal names or equal item contents do not collapse source items. Repeated
  set members do not add groups. Comparisons use strict scalar identity.
- With different projection paths, either directional intersection connects
  the pair. Reordering input therefore does not change the grouping.
- The metric must be an integer. No `value` projection, `empty_value`, or
  additional reducer fields are accepted for `component_count`.
- `left` and `right` are local to this relation, not new roots for ordinary
  workflow `when` conditions.

Events retain `metric_derivation.component_evidence`: projected sets, matching
source-index pairs, and ordered component indexes. Final rule results retain
the same data at `metrics[].derivation.component_evidence`, along with the
relation at `metrics[].derivation.reducer.relation`. Replay restores completed
evidence without recomputing it. This reducer adds no model counting turn.

For SRP-2, a workflow can publish method-to-variable facts and filter lifecycle
and orchestrator methods using `scoring.when`. Those meanings stay in the
workflow; the engine only sees generic sets and source indexes.

## Project review policy

The optional project override file is singular:

```text
{project}/.solid-coder/policies/review.yaml
```

```yaml
version: 1
rules:
  - workflow_id: example-rule
    enabled: true
    reason: Use the project-specific scoring thresholds.
    metrics:
      - id: EXAMPLE-1
        enabled: true
        reason: Raise the severe threshold for generated sources.
        scoring:
          minor:
            operator: greater_than_or_equal
            value: 8
          severe:
            operator: greater_than_or_equal
            value: 15
```

Rule overrides support `enabled`, `reason`, and metric overrides. Metric
overrides support `enabled`, `reason`, and a complete replacement `scoring`
declaration. The policy affects `rules: all`; it does not redefine workflow
discovery or allow project workflows to replace bundled IDs.

The engine persists the effective rule plan, policy source, hashes, enablement
decisions, scoring replacements, condition evidence, step outputs, skips, and
retries in run artifacts for audit and replay.

### Current SPEC-039 policy limitation

Rule enablement from the project policy is active. The effective plan also
records metric enablement and replacement scoring bands. However, the current
runtime does not yet apply replacement scoring bands from that plan while
materializing executable rule steps. This limitation affects ordinary scalar
metrics and collection-backed metrics equally.

Until SPEC-039's effective-policy runtime integration is completed, put the
thresholds you need to execute directly in the rule workflow's `scoring`
declaration. A project policy is still the intended client override surface;
do not fork or replace a bundled workflow ID to work around this limitation.

## Editing the bundled OCP workflow

The bundled OCP package is:

```text
workflows/review/rules/ocp/workflow.yaml
```

Its public workflow ID and policy coordinate are both `ocp`. It is a rule
workflow, so keep its root `rule: {}` marker, at least one metric, and exactly
one exception step.

The current OCP flow uses one shared `analyze_dependencies` agent step, then
asks the model to submit scalar counts for OCP-1, OCP-2, and OCP-3. That remains
valid. To experiment with deterministic MCP counting, migrate one metric at a
time and keep its stable `metric_id`.

### OCP-1: expose the collection, then convert

The current `analyze_dependencies` step wraps `dependencies` inside an
`analysis` object. `scoring.source` selects a declared output and does not
traverse nested JSON properties. First publish `dependencies` and
`has_hardcoded_behavior_selection` as separate outputs while preserving their
existing schemas:

```yaml
outputs:
  - name: dependencies
    type: data
    schema:
      type: array
      items:
        # Keep the current dependency item schema here.

  - name: has_hardcoded_behavior_selection
    type: data
    schema:
      type: boolean
```

Then OCP-1 can become:

```yaml
- id: sealed_variation_points
  type: metric
  metric_id: OCP-1
  depends_on: [analyze_dependencies]
  value:
    type: integer
    minimum: 0
  scoring:
    source: "{{steps.analyze_dependencies.outputs.dependencies}}"
    when:
      all:
        - ref: "{{item.classification}}"
          equals: DIRECT_NON_INJECTED
        - ref: "{{item.is_exception}}"
          equals: false
    severe:
      operator: greater_than_or_equal
      value: 1
```

Remove the old OCP-1 `prompt`. Leaving it in place mixes model-owned and
MCP-owned metric execution and is rejected during workflow loading.

### OCP-2: direct conversion after classification

The `analyze_testability.outputs.testability` array already publishes a
`classification`. Count its `UNTESTABLE` entries:

```yaml
- id: untestable_dependencies
  type: metric
  metric_id: OCP-2
  depends_on: [analyze_testability]
  value:
    type: integer
    minimum: 0
  scoring:
    source: "{{steps.analyze_testability.outputs.testability}}"
    when:
      ref: "{{item.classification}}"
      equals: UNTESTABLE
    severe:
      operator: greater_than_or_equal
      value: 1
```

Again, remove the metric prompt. The upstream model still owns the semantic
testability classification and its reasoning/evidence; MCP owns only counting
and scoring.

### OCP-3: reshape before converting

OCP-3 currently needs three facts about the same dependency:

- dependency classification is `DIRECT_INJECTED`;
- the dependency is not an exception;
- its testability classification is `TESTABLE`.

Those facts currently live across the dependency analysis and testability
analysis. Collection-backed scoring does not join arrays. First change the
`testability` item schema and its agent instructions so every returned entry
also carries the original dependency classification and exception flag. Then
OCP-3 can filter one array:

```yaml
scoring:
  source: "{{steps.analyze_testability.outputs.testability}}"
  when:
    all:
      - ref: "{{item.dependency_classification}}"
        equals: DIRECT_INJECTED
      - ref: "{{item.classification}}"
        equals: TESTABLE
      - ref: "{{item.is_exception}}"
        equals: false
  minor:
    operator: greater_than_or_equal
    value: 1
```

Do not make MCP understand OCP-specific names. `classification`,
`dependency_classification`, and `is_exception` are authored fields validated
from this workflow's own JSON Schema.

### Whole-unit OCP exception

Keep `classify_exception` as a separate `type: exception` step. Per-dependency
`is_exception` filters individual observations before counting; the rule's
exception step decides whether the entire reviewed unit is exempt. MCP keeps
the raw measurements and derivation audit, then applies the whole-rule
exception during finalization.

### Safe OCP edit checklist

- keep `id: ocp`, `metric_id: OCP-1|OCP-2|OCP-3`, and the exception step stable;
- change only one metric and its supporting analysis schema at a time;
- declare every condition field in the source array's item schema;
- make the source-producing step a transitive dependency of the metric;
- remove `prompt` from every collection-backed metric;
- retain non-empty reasoning and evidence on the upstream classifications;
- run the focused OCP parsing/scoring tests before live tests;
- run all non-live tests, then the locked Codex and Claude OCP flow tests;
- remember that policy scoring overrides are auditable but not yet active at
  runtime until the remaining SPEC-039 integration is completed.

## Flow-engine configuration

Process permissions and delegate concurrency come from the solid-coder TOML
configuration:

```toml
[flow_engine]
permitted_executables = ["python3", "bash", "sh"]
max_parallel_sessions = 4
```

`permitted_executables` is checked when a workflow loads. An empty allowlist
means command and script executors are rejected. `max_parallel_sessions` must
be at least `1`.

## Author checklist

Before starting a workflow, verify:

- the package entrypoint is named `workflow.yaml`;
- `id`, `name`, `max_turns`, and non-empty `steps` are present;
- all public and local IDs are unique and dependencies are acyclic;
- sequential steps have explicit `depends_on` edges;
- step outputs use `type: data` or `type: file`;
- JSON value types are nested under `schema`;
- every `for_each` source is an array output from a dependency;
- include callers depend on the alias, not a child step;
- operation `with` keys match the registered operation contract;
- command/script executors are allowlisted and print exactly one JSON object;
- rule workflows have at least one metric and exactly one exception;
- client overrides live in `.solid-coder/policies/review.yaml`.

`flow_start` performs the authoritative load-time validation. Runtime values are
then schema-validated as their steps complete.
