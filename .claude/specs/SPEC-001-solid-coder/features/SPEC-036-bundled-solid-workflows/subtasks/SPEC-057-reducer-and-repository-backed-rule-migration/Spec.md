---
number: SPEC-057
feature: reducer-and-repository-backed-rule-migration
type: subtask
status: in-progress
parent: SPEC-036
blocked-by: [SPEC-054, SPEC-055, SPEC-056]
blocking: []
---

# Reducer and Repository-Backed Rule Migration

## Description

Finish migrating bundled rules whose metrics cannot be expressed as filtered
counts over one local classification output. The primary consumers are ISP,
which requires repository conformer discovery and ordered child fan-in, and
SwiftUI, which requires numeric extrema such as nesting depth and modifier-chain
length. Remaining LSP and SwiftUI relationship/categorical observations are also
migrated so the model classifies evidence while MCP calculates and scores values.

No rule-specific scoring code is added to the engine. Workflows compose the
generic source operations, child-output projection, collection filters, and
reducers defined by upstream specs.

## Migration Matrix

| Rule / metric | Model supplies | MCP supplies |
|---|---|---|
| ISP-1 width | Protocol requirement observations | Filtered requirement count |
| ISP-2 minimum coverage | Per-conformer implemented/required coverage facts | Ordered child fan-in and minimum reducer |
| ISP-3 cohesion groups | Requirement-to-client/group classifications | Distinct count or validated count, per canonical metric definition |
| SwiftUI SUI-1 nesting | Per-expression depth observations | Maximum depth and existing severity bands |
| SwiftUI SUI-3 modifier chain | Per-chain length observations | Maximum chain length and existing severity bands |
| SwiftUI remaining categorical metrics | Typed classifications and exception evidence | Filtered counts or existing scalar comparison, as appropriate |
| LSP repository/relationship evidence | Subtype/conformer contract classifications | Ordered fan-in, filtered counts, and deterministic final severity |

Count-only metrics already owned by SPEC-055 are not reimplemented here.

## User Stories and Acceptance Scenarios

### US-1: Measure protocols with complete conformer evidence

As a reviewer, I want ISP metrics based on all relevant conformers so one model
turn cannot silently ignore a low-coverage client.

#### Scenario 1.1 — Discover and account for conformers

**Given** the reviewed unit is a protocol or interface
**When** MCP searches for conformers and clients
**Then** every shown repository candidate receives an audited disposition
**And** every selected conformer is analyzed by one typed child workflow.

#### Scenario 1.2 — Project ordered conformer results

**Given** selected conformer analyses complete out of order
**When** ISP consumes their declared coverage outputs
**Then** the parent receives every output once in search-source order
**And** missing required child output prevents scoring.

#### Scenario 1.3 — Calculate minimum coverage

**Given** conformer coverage values are `1.0`, `0.75`, and `0.5`
**When** MCP evaluates ISP-2
**Then** the raw metric value is `0.5`
**And** policy bands determine severity without model arithmetic.

#### Scenario 1.4 — Skip nonprotocol units

**Given** the selected unit declares no protocol or interface contract
**When** ISP applicability is evaluated
**Then** repository search and conformer fan-out are skipped with an audited
decision
**And** no zero-valued ISP result is fabricated.

### US-2: Derive extrema from SwiftUI observations

As a reviewer, I want numeric SwiftUI measurements calculated from typed syntax
observations rather than model-submitted maxima.

#### Scenario 2.1 — Calculate body nesting depth

**Given** the model returns every relevant view-expression path and its depth
**When** MCP evaluates SUI-1
**Then** it records the maximum non-excepted depth
**And** audit evidence identifies the source observation that produced it.

#### Scenario 2.2 — Calculate maximum modifier chain

**Given** the model returns modifier-chain observations with lengths
**When** MCP evaluates SUI-3
**Then** it records the maximum non-excepted length
**And** duplicate lengths remain distinct evidence even though the raw maximum is
unchanged.

#### Scenario 2.3 — Handle an empty applicable collection explicitly

**Given** a valid SwiftUI unit contains no relevant chain or nested expression
**When** the workflow prepares observations
**Then** it supplies an authored zero baseline observation or an explicit
rule-defined zero path before maximum reduction
**And** the generic reducer never invents a maximum for an empty collection.

### US-3: Preserve LSP relationship evidence

As a reviewer, I want LSP findings grounded in actual base/subtype relationships
without making MCP understand inheritance semantics.

#### Scenario 3.1 — Analyze each selected relationship

**Given** source analysis identifies base/subtype or protocol/conformer
relationships relevant to the reviewed unit
**When** the LSP workflow fans out relationship classification
**Then** each selected relationship returns its trigger, contract evidence,
classification, exception decision, reasoning, and evidence.

#### Scenario 3.2 — Avoid independent reinference

**Given** the LSP trigger and relationship analysis are complete
**When** LSP metrics become ready
**Then** they consume the durable typed observations
**And** no metric prompt asks the model to rediscover the relationship or count
violations.

#### Scenario 3.3 — Preserve not-applicable behavior

**Given** there is no substitutable relationship to evaluate
**When** the LSP workflow runs
**Then** the repository relationship branch is skipped with an audited condition
decision
**And** locally applicable type-check and unsupported-contract metrics still run
**And** repository absence is not reported as compliance evidence.

### US-4: Preserve policy, aggregation, and audit

As a maintainer, I want repository-backed and reduced metrics to remain ordinary
rule results throughout the review engine.

#### Scenario 4.1 — Apply effective policy

**Given** project policy changes only severity bands or disables a metric
**When** MCP scores projected/reduced observations
**Then** the effective policy applies without changing discovery, classification,
projection, or reducer declarations.

#### Scenario 4.2 — Run through aggregate review

**Given** ISP, LSP, or SwiftUI is selected by the aggregate file-review bundle
**When** model-owned analysis is presented
**Then** compatible prompts may be combined
**And** operations, child fan-out, reducers, metrics, events, and retries retain
their independent execution identities.

#### Scenario 4.3 — Replay without repository drift

**Given** search results, child outputs, reducer events, and rule results are
durable
**When** a completed run is replayed
**Then** it does not search the current repository or reread modified files
**And** it reconstructs the original ordered evidence and severity.

## Technical Requirements

- ISP and LSP repository discovery reuse typed `source.*` operations and complete
candidate coverage validation; neither rule parses human-readable search text.
- Selected repository entries run as child workflow instances with declared typed
outputs and ordered completion. When a nested observation array must be flattened,
a schema-gated normalization step may copy completed child classifications but
must not reread source, infer new facts, calculate metrics, or choose severity.
- Numeric extrema and distinct counts use SPEC-054 reducers. Filtered counts use
SPEC-053. No model submits a derived total, minimum, or maximum.
- Rule-specific classification enums, exception signals, thresholds, and evidence
remain in workflow YAML and output schemas.
- Metric and observation IDs, applicability selectors, tags, extensions, unit
kind filters, effective-policy coordinates, and canonical exceptions remain
stable through migration.
- A repository search with no candidates is audited separately from a rule that
is not applicable and from a completed compliant analysis.
- Every persisted metric identifies its source output/projection, selected source
indexes, reducer, raw value, effective band, and scoring authority.

## Connects To

| Direction | Spec | Relationship |
|---|---|---|
| Parent | SPEC-036 | Owns bundled rule workflows and aggregate review |
| Upstream | SPEC-054 | Supplies maximum, minimum, distinct-count, and ratio reducers |
| Upstream | SPEC-055 | Migrates all count-only metrics and shared observation patterns |
| Upstream | SPEC-056 | Supplies complete candidate handling and child-output projection |
| Upstream | SPEC-040 | Supplies source discovery and typed search results |
| Fixtures | SPEC-017, SPEC-018, SPEC-022 | Supply ISP, LSP, and SwiftUI locked cases |

## Test Plan

- ISP fixtures for multiple conformers, partial coverage, no conformers,
  nonprotocol units, excluded test conformers, empty fan-out, and out-of-order
  child completion.
- SwiftUI fixtures for maximum depth, equal maxima, no relevant expressions,
  maximum modifier chains, exceptions, non-SwiftUI units, and policy overrides.
- LSP fixtures for base/subtype, protocol/conformer, no relationship, exceptions,
  selected/rejected repository candidates, and missing relationship evidence.
- Projection/reducer tests for missing child outputs, replay, resume, nested
  instance isolation, aggregate boundaries, and Stop draining.
- Locked Codex and Claude live runs through shared principle-test bases, followed
  by a composite review run proving every applicable migrated rule finalizes.

## Implementation Plan

1. Complete SPEC-054 reducer tests and SPEC-056 ordered child-output projection.
2. Rewrite ISP analysis into protocol facts plus per-conformer child outputs;
   derive ISP-1/2/3 through generic count/minimum/distinct-count operations.
3. Migrate SwiftUI maximum-depth and maximum-chain metrics, then remaining
   categorical observations not completed by SPEC-055.
4. Migrate LSP repository/relationship analysis so downstream metrics consume one
   durable trigger and complete relationship classifications.
5. Add policy, exception, audit, replay, aggregate, Stop, and applicability tests
   after each workflow.
6. Run all non-live tests and locked Codex/Claude rule tests before the composite
   review validation.

## Definition of Done

- [x] ISP metrics use complete repository-backed conformer evidence and MCP
      scoring.
- [x] SwiftUI extrema are reducer-owned and source-auditable.
- [x] LSP relationship evidence is durable and never independently re-inferred by
      metric prompts.
- [x] No migrated rule requires a rule-specific production scorer or parser.
- [x] Policy, exceptions, applicability, aggregation, replay, and Stop behavior
      are covered.
- [ ] All non-live and locked Codex/Claude fixture tests pass.

## Implementation Status

ISP now discovers repository candidates through typed source operations, validates
complete candidate dispositions, runs one child review per selected candidate,
calculates child coverage through the generic `collection.ratio` operation, and
derives width, minimum coverage, and cohesion through MCP-owned metrics.

SwiftUI now submits per-property and per-chain observations. MCP applies maximum
reducers with explicit zero empty-collection values while preserving every
projected source index, including duplicate maxima.

LSP now gates repository discovery on a durable concrete-inheritance trigger,
validates candidate coverage, records child relationship classifications, and
uses one schema-gated normalization step before MCP counts contract violations.
The false-trigger path records skipped repository work without suppressing the
other LSP metrics.

Focused reducer and rule tests pass, together with the complete non-live flow
engine, MCP server, harness, hook, dispatcher, and Apple build suites. Locked
live Codex/Claude fixture runs remain before this spec can be marked complete.
