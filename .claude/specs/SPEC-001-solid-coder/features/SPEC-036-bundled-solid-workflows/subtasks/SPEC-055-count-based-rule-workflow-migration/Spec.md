---
number: SPEC-055
feature: count-based-rule-workflow-migration
type: subtask
status: in-progress
parent: SPEC-036
blocked-by: [SPEC-053]
blocking: []
---

# Count-Based Bundled Rule Workflow Migration

## Description

Migrate bundled review metrics that are filtered counts from model-submitted
numbers to the SPEC-053 observation contract. The model identifies and classifies
typed facts once; MCP filters those facts, calculates metric values, applies
effective severity bands, records evidence, and finalizes each rule.

This migration preserves the canonical meaning, exception criteria, thresholds,
applicability, and locked fixture expectations of every rule. It changes
ownership of arithmetic, not what constitutes a violation.

## Migration Boundary

| Rule | This spec migrates | Deferred |
|---|---|---|
| OCP | Dependency and behavior-selection observations; OCP-1/2/3 counts | Nothing; it is the reference migration |
| SRP | Actions, cohesion groups, and stakeholders as typed observations | No reducer work |
| Structured Concurrency | Countable task, isolation, await, bridge, and duration-literal sites | Any future aggregate numeric reducer |
| Code Smells | Static logic, concrete type, and inline type observations | Boundary inference bug remains SPEC-051 |
| Frontmatter | Missing, mismatched, invalid, and low-quality field observations | None |
| Unit Testing | Countable isolation, structure, naming, double, setup, and framework observations | None |
| UI Testing | Countable flow, base-class, grouping, synchronization, and identifier observations | None |
| LSP | Type checks, contract violations, fatal methods, and empty methods when expressible as filtered counts | Non-count repository/relationship analysis in SPEC-057 |
| SwiftUI | Impure expressions, preview-only types, missing previews, accessibility, fixed frames, and over-isolation observations | Nesting depth and maximum modifier chain in SPEC-057 |

ISP and DRY are excluded because their correct results depend on repository search,
child-workflow fan-in, or reducers beyond filtered count.

## Canonical Rule Shape

```yaml
steps:
  - id: classify_observations
    type: agent
    prompt: |
      Apply the canonical rule instructions to the named review target.
      Return every relevant observation exactly once with reasoning and evidence.
    outputs:
      - name: observations
        type: data
        schema:
          type: array
          items:
            type: object
            additionalProperties: false
            required: [classification, is_exception, reasoning, evidence]
            properties:
              classification: {type: string}
              is_exception: {type: boolean}
              reasoning: {type: string, minLength: 1}
              evidence: {type: string, minLength: 1}

  - id: violation_count
    type: metric
    metric_id: RULE-1
    depends_on: [classify_observations]
    value: {type: integer, minimum: 0}
    scoring:
      source: "{{steps.classify_observations.outputs.observations}}"
      when:
        all:
          - ref: "{{item.classification}}"
            equals: VIOLATION
          - ref: "{{item.is_exception}}"
            equals: false
      severe: {operator: greater_than_or_equal, value: 1}
```

The exact observation schema belongs to each rule. Production scoring code must
not contain rule field names, classification strings, thresholds, or exceptions.

## User Stories and Acceptance Scenarios

### US-1: Classify once and score deterministically

As a reviewer, I want the model to return source facts rather than metric totals
so omissions and arithmetic can be audited independently.

#### Scenario 1.1 — Derive every count from typed observations

**Given** an applicable bundled rule has count-based metrics
**When** its classification step completes
**Then** every count metric reads a declared collection output
**And** MCP calculates the value without a metric prompt or model arithmetic.

#### Scenario 1.2 — Reuse one observation across dependent metrics

**Given** one classified fact affects multiple metrics
**When** MCP scores those metrics
**Then** each metric filters the same durable observation collection
**And** the model is not asked to reclassify that fact.

#### Scenario 1.3 — Preserve explicit exceptions

**Given** an observation matches a canonical exception
**When** the model classifies it
**Then** it returns `is_exception: true` with nonempty reasoning and evidence
**And** MCP excludes it only where the authored metric condition requires that.

### US-2: Preserve rule meaning during migration

As a maintainer, I want migration results comparable with locked fixtures and the
legacy rule definitions.

#### Scenario 2.1 — Preserve canonical instructions

**Given** a bundled rule is migrated
**When** its classification prompt is authored
**Then** every detection requirement and exception from the current canonical
rule remains represented
**And** any wording change is documented with evidence that semantics are equal.

#### Scenario 2.2 — Preserve metric identities and thresholds

**Given** existing consumers expect stable metric and observation IDs
**When** the workflow is migrated
**Then** those IDs, value types, severity bands, and effective-policy coordinates
remain stable unless a separate approved spec changes them.

#### Scenario 2.3 — Preserve applicability and skip behavior

**Given** a rule does not apply to the selected file or unit
**When** the review bundle materializes rules
**Then** the rule is skipped with the existing audited applicability decision
**And** no classification prompt or fabricated zero result is produced.

### US-3: Validate every bundled migration independently

As a maintainer, I want one reusable validation harness so rule migrations do not
duplicate model-runner or assertion infrastructure.

#### Scenario 3.1 — Assert exact step/output progression

**Given** a locked principle fixture and model profile
**When** the migrated rule runs
**Then** the shared harness asserts every presented classification step, typed
output, MCP-owned metric completion, exception decision, final result, and
terminal state.

#### Scenario 3.2 — Compare Codex and Claude through one base

**Given** the same test-owned fixture and expected observations
**When** Codex and Claude execute the rule
**Then** both model adapters use the same workflow assertion contract
**And** only backend/profile configuration differs.

#### Scenario 3.3 — Reject incomplete observations

**Given** a model omits a required field, evidence, expected batch item, or
declared observation output
**When** it submits the step
**Then** schema or batch coverage validation rejects the submission with an
actionable retry message
**And** no dependent metric is calculated from partial data.

## Technical Requirements

- Each rule has one authoritative typed observation schema per classification
  responsibility; duplicate metric prompts that re-infer the same facts are
  removed.
- Observation entries carry stable classification fields plus required reasoning
  and evidence. Exceptions are explicit when the canonical rule defines them.
- MCP owns filtering, counts, severity, worst-severity selection, effective
  policy, whole-rule exceptions, and normalized results.
- Rule applicability, file/unit scope, tags, extensions, unit kinds, exclusions,
  aggregate presentation, batching, replay, and Stop behavior remain unchanged.
- A migrated workflow may keep more than one classification step when those steps
  require genuinely different evidence. It must not split solely to preserve old
  metric-owned prompts.
- File-scoped rules execute once per file; unit-scoped rules execute once per
  selected unit. Migration must not multiply model turns.
- Production workflows never depend on test fixtures or experimental bundles.

## Connects To

| Direction | Spec | Relationship |
|---|---|---|
| Parent | SPEC-036 | Owns bundled rule and review workflows |
| Upstream | SPEC-053 | Provides filtered collection counts and audit |
| Upstream | SPEC-039 | Provides executable rule declarations, policy, and results |
| Fixtures | SPEC-014 through SPEC-025 | Provide principle-specific locked cases |
| Adjacent | SPEC-051 | Owns the code-smells effective-boundary defect |
| Follow-up | SPEC-057 | Migrates reducer and repository-backed metrics |

## Test Plan

- Add one contract test per migrated YAML proving every MCP-owned metric source,
  filter, value type, threshold, dependency, and observation field.
- Reuse principle fixture bases and model adapters; do not create per-rule copies
  of live runner infrastructure.
- Assert compliant, violating, excepted, and not-applicable cases where fixtures
  already exist; add focused fixtures only when a rule lacks one of those states.
- Assert exact locked raw values and severities before and after migration.
- Assert aggregate file review exposes classification work but never MCP-owned
  metric steps in its model submission schema.
- Run all non-live suites after each rule, then the rule's Codex and Claude live
  scenario before moving to the next rule.

## Implementation Plan

1. Treat the migrated OCP workflow and tests as the reference contract; close its
   remaining effective-policy and lifecycle coverage under SPEC-053.
2. Migrate SRP and validate its locked 6/2/2 fixture expectations.
3. Migrate Structured Concurrency, Code Smells, and Frontmatter one workflow at a
   time, preserving file/unit scope and canonical exceptions.
4. Migrate Unit Testing and UI Testing with their existing conditional tags and
   test-code applicability.
5. Migrate countable LSP and SwiftUI metrics without pulling reducer-owned metrics
   into this spec.
6. After every workflow: run focused parser/execution tests, all non-live tests,
   and its shared Codex/Claude live validation before starting the next workflow.
7. Update bundled-review assertions and documentation only after all migrated
   workflows preserve their locked results.

## Definition of Done

- [ ] Every in-scope bundled metric is derived from typed observations by MCP.
- [ ] The model submits no raw count for an in-scope metric.
- [ ] Canonical detection, exceptions, IDs, thresholds, and applicability remain
      unchanged and are covered by tests.
- [ ] Incomplete observations cannot trigger partial scoring.
- [ ] The shared Codex/Claude harness validates every migrated rule.
- [ ] All non-live suites and locked live rule scenarios pass after each migration.

## Implementation Status

OCP remains the reference collection-backed migration. SRP now uses one typed
`analyze_responsibilities` model step to return actions, cohesion groups, and
stakeholders with required reasoning and evidence. MCP derives SRP-1, SRP-2,
and SRP-3 as filtered collection counts, applies the existing thresholds,
records derivation evidence, and runs the existing rule-wide facade exception.
The retained single-prompt experiment shares output-shape-neutral canonical
detection wording for valid comparison.

SRP validation covers exact `6 / 2 / 2` values, MCP ownership, exception
override, audit persistence, incomplete-observation rejection, bundle execution,
and aggregate presentation with one analysis prompt per unit. Current non-live
results are 764 flow-engine tests passing (with the one host-Xcode wrapper case
deselected), 852 MCP-server tests passing with 4 intentional skips, 95 harness
tests, 62 hook tests, and 36 Apple-build tests. Locked live execution remains
blocked by the host-integration issues recorded in SPEC-054 rather than an SRP
assertion.
