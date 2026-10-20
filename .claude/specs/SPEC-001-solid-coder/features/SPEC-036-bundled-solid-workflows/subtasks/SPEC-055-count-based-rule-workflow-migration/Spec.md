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
| SRP | Actions, method-variable usage, and stakeholders as typed observations; MCP counts actions/stakeholders and derives cohesion components | Generic pairwise reduction is implemented by SPEC-059 |
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
| Upstream | SPEC-058 | Provides co-located metric declarations without additional model work |
| Upstream | SPEC-059 | Provides generic pairwise component reduction used for SRP cohesion |
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
- Submit the three independent SRP classification outputs together and assert
  MCP calculates every co-located metric from the corresponding accepted output;
  presentation alone is not sufficient evidence. Cover partial submissions,
  replay, nested rule ownership, and genuine dependencies that must wait for
  scoring.
- Preserve Codex transcripts and correlate actual successful `flow_start` and
  `flow_next` responses with their calls. Record tool discovery and recovered
  local-script failures as diagnostics, not rule-result failures; retain exact
  step, metric, exception, audit, and terminal-state assertions.
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

- [x] Every in-scope bundled metric is derived from typed observations by MCP.
- [x] The model submits no raw count for an in-scope metric.
- [x] Canonical detection, exceptions, IDs, thresholds, and applicability remain
      unchanged and are covered by tests.
- [x] Incomplete observations cannot trigger partial scoring.
- [ ] The shared Codex/Claude harness validates every migrated rule.
- [ ] All non-live suites and locked live rule scenarios pass after each migration.

## Implementation Status

### Current status — 2026-10-19

All in-scope count-based migrations are implemented. Keep `in-progress` for
rule-by-rule live-validation close-out, not missing scoring mechanics. The latest
full non-live checkpoint is 2,900 tests and 228 subtests passed, with four existing
skips. SPEC-057 records the later reducer/ISP migration; SPEC-064 records the
completed LSP provenance migration and its ten-case Codex/Claude live matrix,
including both real write-gate profiles.

The dated checkpoints below retain earlier rule shapes, expected values and
validation gaps as history. In particular, their old model-owned LSP and SwiftUI
reducer notes are superseded by SPEC-057/064. Do not reopen that completed work
or infer complete coverage of every migrated rule from the targeted LSP matrix.

### Migration checkpoints

OCP remains the reference collection-backed migration. The agreed SRP draft is
now the bundled `workflows/review/rules/srp/workflow.yaml`. It has three
independent typed classifiers: `classify_actions`, `classify_variable_usage`,
and `classify_stakeholders`, each with co-located MCP-owned metric declarations
and required reasoning/evidence. SRP-1 counts non-lifecycle action observations;
SRP-2 derives connected components from intersecting instance-variable sets,
excluding lifecycle methods and orchestrators; SRP-3 counts stakeholder
observations. The facade exception remains a separate step after scoring.

The runtime retains seven distinct steps: the three classifiers, `verb_count`,
`cohesion_groups`, `stakeholder_count`, and `classify_exception`. The calling
workflow controls sequential versus aggregate presentation; the rule itself
does not force either mode. Aggregate execution accepts the three independent
classification outputs together and MCP calculates their metrics before the
dependent exception step. Genuine dependencies on scored outputs still wait.

SRP validation preserves the unchanged fixture and exact `6 / 2 / 2` values,
MCP ownership, exception override, audit persistence, incomplete-observation
rejection, bundle execution, combined submissions, partial completion, replay,
and nested rule ownership. The SRP promotion and aggregate scoring coverage are
committed in `026231e`; the shared Codex protocol-evidence contract is committed
in `262f1e1`.

Latest SRP validation checkpoint (2026-10-02 UTC):

- All non-live groups: **2,470 passed, 4 skipped**.
- Fresh Codex sequential and aggregate SRP runs: **2 passed**, both with exact
  `6 / 2 / 2` metrics. Sequential run `20261002T015554Z-05693e2e` records one
  successful start and five successful next calls; aggregate run
  `20261002T015710Z-71d1e967` records one successful start and two successful
  next calls. Neither has failed or unanswered calls.
- The earlier completed Codex and Claude sequential/aggregate runs were
  revalidated against the full shared assertions: **4 passed**. The Claude
  evidence is from sequential run `20261002T005314Z-d2adebae` and aggregate run
  `20261002T005532Z-4b8979bd`; these were not fresh Claude reruns at this checkpoint.
- Codex evidence is preserved as `codex-protocol-evidence.json` beside each
  run's transcript and flow artifacts. Discovery and recovered script failures
  remain visible separately from successful MCP execution and exact scoring.

At the SRP checkpoint, the next rule under review was **OCP**, before Structured Concurrency. Initial
inspection confirms one dependency classifier, four MCP-owned metric outputs,
and a separate whole-unit exception step. Its focused deterministic workflow
and legacy exception-prompt checks pass: **9 tests**. The shared live OCP
expectations still name the old three metric steps and omit the dependency
classifier and hardcoded-selection metric; these expectations must be aligned
with the current contract before claiming current live validation. Existing
OCP fixtures 2 (abstract injection) and 3 (pure-data construction) are not wired
into the focused workflow scenarios. Coverage must also exercise injected and
indirect testability filters and nonzero hardcoded-selection observations.
No OCP workflow, fixture, or test was changed during this inspection.

This spec remains `in-progress` because the remaining migration validation and
rule-by-rule review are not complete.

Structured Concurrency now uses one typed
`classify_concurrency_observations` model step for model mixing, unmanaged task
lifecycle, safety bypasses, independent sequential awaits, blocking bridges,
and raw durations. MCP derives SC-1 through SC-6 from that shared collection,
preserves the existing thresholds, and excludes an excepted observation only
from its matching metric. Bundle coverage confirms the migration reduces the
selected rule from fourteen model-facing steps to two while retaining internal
metric execution.

The locked Structured Concurrency fixture now passes through both Codex and
Claude with exact values `1 / 1 / 1 / 3 / 1 / 1`. Live validation exposed and
corrected one prompt ambiguity: SC-4 counts each independent await call once,
not each adjacent pair. That historical non-live checkpoint had 1,822 passing tests,
4 intentional skips, and the known host-Xcode command case deselected.

Code Smells now uses one file-scoped `classify_smell_observations` model step
for static logic, effective top-level type boundaries, and inline types. MCP
derives CS-1 through CS-3, preserves metric-specific exclusions independently,
and retains the explicit no-rule-wide-exception decision. Bundle coverage
confirms that initial model presentation drops from four simultaneous rule
steps to one classification step. The deeper effective-boundary validation
described by SPEC-051 remains separate from this arithmetic-ownership migration.

The locked Code Smells fixture passes through Codex and Claude with exact values
`1 / 2 / 1`, audited MCP derivations, the file-scoped result, and terminal run
completion validated by the shared live rule harness.

Frontmatter now uses one file-scoped `classify_frontmatter_observations` model
step for missing metadata, name mismatch, invalid category, incorrect stack, and
bad description observations. MCP derives FM-1 through FM-5, retains all
metric-specific exclusions and thresholds, and reduces initial rule presentation
from six simultaneous model steps to one classification step.

The locked missing-frontmatter fixture passes through Codex and Claude with
exact values `1 / 0 / 0 / 0 / 0`; focused non-live Frontmatter coverage remains
green at 8 tests.

Unit Testing now uses one file-scoped `classify_test_observations` model step
for isolation, structure, naming, test-double, setup, and framework findings.
MCP derives TEST-1 through TEST-6, preserves the TEST-3 minor/severe bands,
applies observation-level exceptions independently, and keeps the existing
unit-test tag and Swift-file applicability. Gate-on-write coverage confirms the
prospective buffer now presents one classifier instead of seven simultaneous
rule steps.

The locked Unit Testing fixture passes through Codex and Claude with exact
values `1 / 2 / 3 / 1 / 1 / 1`. Live validation clarified two canonical
counting boundaries without changing the fixture contract: multiple symptoms
of one test-double or framework remediation produce one observation, while a
`static var` declaration is itself shared mutable test state even when the
reviewed snapshot does not show a read or mutation. Codex completed in 45.85s
and Claude completed in 79.64s.

UI Testing now uses one file-scoped `classify_ui_test_observations` model step
for flow encapsulation, base-class structure, assertion grouping,
synchronization, and typed-identifier findings. MCP derives UITEST-1 through
UITEST-5, preserves UITEST-5's minor/severe thresholds, applies authored
exceptions per observation, and retains the Swift UI-test applicability gate.

The locked UI Testing fixture passes through Codex and Claude with exact values
`2 / 1 / 1 / 9 / 8`. Live validation made each metric's observation identity
explicit: inline flows are counted per offending test method, overlapping
base-class symptoms form one suite observation, assertion fragmentation is
counted per group, synchronization is counted per wait or unguarded access
site, and typed identifiers are counted per raw query occurrence. Final Codex
and Claude runs completed in 54.21s and 79.32s respectively.

LSP now derives LSP-1 developer-owned type-check count plus LSP-3/LSP-4 fatal
and empty implementation counts directly from its existing typed shared
analysis. External type checks remain explicit non-counted observations. LSP-2
contract-violation summation remains model-owned because it traverses nested
inheritance relationships and override fields; SPEC-057 owns that reducer-backed
follow-up. The shared rule test contract now completes the same hybrid run after
an intentional malformed model-metric submission instead of attempting a second
run against the active session lock.

SwiftUI now uses one typed `classify_countable_observations` model step for
impure view members, preview-only types, views without previews, invalid
container accessibility, fixed frames, and over-isolation. MCP derives SUI-2
and SUI-5 through SUI-9 from that collection and applies exceptions per
observation. SUI-1 nesting/expression maxima, SUI-3 maximum modifier chain, and
SUI-4 categorical injection style remain model-owned; reducer-backed maxima
belong to SPEC-057. Bundle startup presents six SwiftUI steps instead of eleven.

All count-based workflow migrations named by this spec are implemented and
non-live validated. The spec remains `in-progress` while the remaining locked
Codex/Claude rule scenarios are completed one workflow at a time.

At the earlier Unit Testing checkpoint, the complete non-live suite was green at
1,822 passing tests, 4 intentional skips, and the one known host-Xcode dynamic
command case explicitly deselected. Structured Concurrency, Code Smells,
Frontmatter, Unit Testing, and UI Testing now have locked live evidence from
both Codex and Claude.
