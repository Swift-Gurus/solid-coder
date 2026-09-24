---
number: SPEC-054
feature: deterministic-metric-reducers
type: subtask
status: in-progress
parent: SPEC-010
blocked-by: [SPEC-053]
blocking: [SPEC-057]
---

# Deterministic Metric Reducers

## Description

Extend collection-backed metric scoring with four bounded, typed reducers:
`maximum`, `minimum`, `distinct_count`, and `ratio`. The model remains
responsible only for returning schema-validated observations. MCP filters,
projects, reduces, scores, audits, and replays those observations without model
arithmetic.

This specification extends SPEC-053; it does not create an expression language.
Omitting `scoring.reducer` preserves SPEC-053 filtered-count behavior.

## Proposed YAML Contract

```yaml
- id: maximum_nesting_depth
  type: metric
  metric_id: SUI-1
  value: {type: integer, minimum: 0}
  scoring:
    source: "{{steps.analyze_views.outputs.views}}"
    when:
      ref: "{{item.is_exception}}"
      equals: false
    reducer:
      type: maximum
      value: "{{item.nesting_depth}}"
    severe: {operator: greater_than_or_equal, value: 5}
```

```yaml
- id: unsafe_ratio
  type: metric
  metric_id: CUSTOM-2
  value: {type: number, minimum: 0, maximum: 1}
  scoring:
    source: "{{steps.classify.outputs.items}}"
    reducer:
      type: ratio
      numerator_when:
        ref: "{{item.classification}}"
        equals: UNSAFE
      denominator_when:
        ref: "{{item.is_exception}}"
        equals: false
    severe: {operator: greater_than_or_equal, value: 0.5}
```

Reducer contracts:

- `maximum` and `minimum` require a numeric `value` reference into each selected
  source item.
- `distinct_count` requires a scalar `value` reference and counts distinct JSON
  scalar values after the ordinary `scoring.when` filter.
- `ratio` counts entries matching `numerator_when` and divides by entries
  matching `denominator_when`. A zero denominator produces `0.0` and is recorded
  explicitly in derivation evidence.
- The outer `scoring.when`, when present, limits entries before any reducer is
  evaluated. Ratio conditions operate only on that filtered collection.

## User Stories and Acceptance Scenarios

### US-1: Reduce typed observations without model arithmetic

As a workflow author, I want MCP to reduce typed observation collections so the
model only classifies source facts.

#### Scenario 1.1 — Calculate a maximum

**Given** selected entries contain depths `2`, `5`, and `3`
**When** a `maximum` reducer projects `item.depth`
**Then** MCP records the metric value `5`
**And** no model-owned metric step is presented.

#### Scenario 1.2 — Calculate a minimum

**Given** selected entries contain coverage values `0.8`, `0.5`, and `1.0`
**When** a `minimum` reducer projects `item.coverage`
**Then** MCP records `0.5` as a number.

#### Scenario 1.3 — Count distinct scalar values

**Given** selected entries project `A`, `B`, `A`, and `C`
**When** MCP applies `distinct_count`
**Then** the metric value is `3`
**And** audit evidence preserves the first source index for each distinct value.

#### Scenario 1.4 — Calculate a ratio

**Given** four denominator entries and two numerator entries
**When** MCP applies the ratio reducer
**Then** the metric value is `0.5`
**And** audit evidence identifies numerator and denominator indexes.

### US-2: Keep reduction typed and deterministic

As the flow engine, I want reducer declarations validated against source schemas
so malformed workflows fail before a model session starts.

#### Scenario 2.1 — Reject a missing projection

**Given** a maximum, minimum, or distinct-count reducer references an undeclared
item field
**When** the workflow is loaded
**Then** validation reports the metric step, reducer, and missing field.

#### Scenario 2.2 — Reject incompatible projection types

**Given** a maximum reducer projects a string or object field
**When** the workflow is loaded
**Then** validation rejects the reducer as nonnumeric.

#### Scenario 2.3 — Reject incompatible metric value types

**Given** a ratio reducer declares an integer metric or a distinct-count reducer
declares a string metric
**When** the workflow is loaded
**Then** validation rejects the incompatible value declaration.

#### Scenario 2.4 — Preserve empty-source semantics

**Given** no selected entries remain
**When** MCP evaluates maximum, minimum, or distinct count
**Then** distinct count returns zero
**And** maximum and minimum fail with an explicit empty-reduction diagnostic
instead of fabricating a value.

### US-3: Preserve filtering, policy, audit, and replay

As a maintainer, I want reducers to behave like ordinary deterministic metrics
through the rest of the engine.

#### Scenario 3.1 — Filter before reducing

**Given** an outer `scoring.when` excludes exception entries
**When** MCP evaluates any reducer
**Then** excluded entries cannot affect the projection or result.

#### Scenario 3.2 — Apply effective severity bands

**Given** project policy overrides only a metric's severity bands
**When** a reducer produces its raw value
**Then** MCP applies the effective bands without changing the authored source,
filter, projection, or reducer.

#### Scenario 3.3 — Replay a completed reducer

**Given** the reducer completion event is durable
**When** a run is replayed
**Then** the same raw value, indexes, projection evidence, and severity are
restored without reevaluation or a model call.

#### Scenario 3.4 — Resume an incomplete reducer

**Given** the source output is durable but the reducer event is absent
**When** the run resumes
**Then** MCP evaluates and records the reducer exactly once before presenting
more model-owned work.

## Technical Requirements

- Reducers are a sealed typed declaration, not arbitrary operation names.
- Existing `scoring.source` and `scoring.when` retain their SPEC-053 meaning.
- All item references are validated from the source array's declared item schema.
- Projection values remain scalar; nested object construction and executable
  expressions are not supported.
- Numeric reducers preserve integer output only when both the metric declaration
  and all projected values are integers; ratio always produces a number.
- Distinctness uses canonical JSON scalar equality and preserves source order in
  audit evidence.
- Derived events identify reducer type, filtered indexes, projected values or
  their compact evidence, numerator/denominator indexes when applicable, raw
  result, selected band, and scoring authority.
- Whole-rule exceptions, aggregate execution, nested instances, Stop draining,
  and result persistence reuse existing deterministic metric behavior.

## Non-Goals

- Sum, average, median, percentile, joins, grouping, sorting, mapping, and unions.
- User-authored Python, Swift, JavaScript, shell, or expression evaluation.
- Inferring reducer behavior from severity operators or output field names.
- Migrating bundled rule workflows; migration belongs to SPEC-055 and SPEC-057.

## Connects To

| Direction | Spec | Relationship |
|---|---|---|
| Parent | SPEC-010 | Owns parsing, execution, events, replay, and Stop behavior |
| Upstream | SPEC-053 | Supplies typed collection sources, filtering, counting, and audit |
| Downstream | SPEC-057 | Uses reducers for bundled metrics that are not filtered counts |

## Test Plan

- Parser tests for every reducer shape, required fields, forbidden fields, and
  compatibility with the metric value type.
- Schema tests for missing item fields, nonnumeric projections, and invalid ratio
  conditions.
- Evaluator tests for ordinary values, duplicates, filters, empty collections,
  zero denominators, stable ordering, and strict numeric behavior.
- Execution tests proving reducers drain internally after agent and aggregate
  submissions and remain scoped under nested workflows and `for_each`.
- Event/replay tests proving audit fields reconstruct without reevaluation.
- Policy and whole-rule-exception tests proving only final severity changes.
- Test-owned Codex and Claude E2E fixtures with locked observation collections
  and identical reducer results.

## Implementation Plan

1. Add failing typed-decoding and schema-compatibility tests for the four reducer
   declarations.
2. Introduce a sealed reducer model and typed projection references while keeping
   omitted reducer equivalent to SPEC-053 count.
3. Add failing evaluator tests for maximum, minimum, distinct count, and ratio.
4. Implement reducer-specific evaluators behind the existing deterministic
   metric-evaluation boundary.
5. Extend derivation events and normalized audit projections with reducer-specific
   evidence.
6. Prove replay, resume, nested scoping, aggregate boundaries, Stop draining,
   effective policy, and whole-rule exceptions.
7. Run all non-live tests, then locked Codex and Claude test-owned workflows.

## Definition of Done

- [x] All four reducers parse into sealed typed declarations.
- [x] Invalid projections and output types fail before execution.
- [x] Reducers execute without model arithmetic or model-owned metric turns.
- [x] Filtering, policy, exceptions, audit, replay, and Stop behavior are covered.
- [x] Existing omitted-reducer count behavior is unchanged.
- [ ] All non-live and locked live flow-engine tests pass.

## Implementation Status

The four sealed reducers, typed load-time validation, strategy-based execution,
durable derivation evidence, replay, aggregate draining, nested rebasing, and
effective-policy behavior are implemented. Focused reducer and integration
coverage passes, and the complete non-live flow-engine suite passed before the
host Xcode license entered an unaccepted state. A current direct-binary rerun
passes 763 tests; the sole remaining command-step test invokes the blocked
`python3` Xcode wrapper from a login shell.

Locked live validation remains open for host-integration reasons rather than a
reducer assertion. Codex completes the reducer workflow, but the plugin-owned
MCP process persists its run under the temporary plugin-cache project slug, so
the live harness cannot collect the authoritative event log from the requested
project root. Claude Code 2.1.216 rejects the pinned `claude-opus-4-5` profile:
without advisor support it exits before inference, while enabling advisor
support produces an API incompatibility for that model. Neither live backend
reached a failing reducer-value, severity, audit, replay, or terminal-state
assertion.
