---
number: SPEC-057
feature: reducer-and-repository-backed-rule-migration
type: subtask
status: complete
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
| SwiftUI SUI-1 nesting | Ordered View-expression paths | Per-path count, ordered fan-in, maximum, and existing severity bands |
| SwiftUI SUI-1 expression count | Ordered View-expression occurrences per property | Per-property count, ordered fan-in, maximum, and existing severity bands |
| SwiftUI SUI-3 modifier chain | Ordered modifier occurrences per chain | Per-chain count, ordered fan-in, maximum, and existing severity bands |
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

**Given** the model returns every relevant ordered view-expression path
**When** MCP evaluates SUI-1
**Then** a `collection.count` operation measures each non-excepted path during
ordered `for_each` execution
**And** the metric records the maximum aggregated count
**And** audit evidence identifies the source observation that produced it.

#### Scenario 2.2 — Calculate view-expression count

**Given** the model returns every View-expression occurrence for each
view-returning property
**When** MCP evaluates the SUI-1 expression-count observation
**Then** a `collection.count` operation measures each non-excepted property
**And** the metric records the maximum aggregated count
**And** repeated View types remain separate occurrences.

#### Scenario 2.3 — Calculate maximum modifier chain

**Given** the model returns ordered modifier occurrences for each chain
**When** MCP evaluates SUI-3
**Then** a `collection.count` operation measures each non-excepted chain
**And** the metric records the maximum aggregated count
**And** duplicate lengths remain distinct evidence even though the raw maximum is
unchanged.

#### Scenario 2.4 — Handle an empty applicable collection explicitly

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
- Numeric extrema and distinct counts use SPEC-054 reducers. Nested evidence
  collections are counted through the generic engine-owned `collection.count`
  operation during ordinary `for_each`; existing step-output fan-in aggregates
  the counts in source order before the maximum reducer consumes them. No model
  submits a derived total, collection length, minimum, or maximum.
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
3. Add generic intermediate collection counting, preserve ordered `for_each`
fan-in schemas, and migrate SwiftUI maximum-depth and maximum-chain metrics;
then migrate remaining categorical observations not completed by SPEC-055.
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
- [x] All non-live and locked Codex/Claude fixture tests pass.

## Implementation Status

ISP now discovers repository candidates through typed source operations, validates
complete candidate dispositions, runs one child review per selected candidate,
calculates child coverage through the generic `collection.ratio` operation, and
derives width, minimum coverage, and cohesion through MCP-owned metrics.

SwiftUI now submits ordered deepest-path, View-expression, and modifier-call
evidence collections without numeric lengths. The generic `collection.count`
operation measures every non-excepted collection during `for_each`; existing
ordered step-output fan-in publishes those counts, and the maximum reducer
derives the three extrema with complete projection evidence. Load-time schema
validation now reflects the array output that ordinary `for_each` already
publishes at runtime.

LSP now gates repository discovery on a durable concrete-inheritance trigger,
validates candidate coverage, records child relationship classifications, and
uses one schema-gated normalization step before MCP counts contract violations.
The false-trigger path records skipped repository work without suppressing the
other LSP metrics.

Focused reducer, operation-composition, fan-in-schema, and rule tests pass. The
complete non-live flow-engine, MCP server, harness, hook, dispatcher, and Apple
build suites pass with 1,827 tests, 4 intentional skips, and 1 known command-step
deselection.

Initial locked SwiftUI live validation produced the correct final metrics
through both Codex and Claude, but artifact inspection showed Claude omitted
compliant one-modifier observations before MCP reduction. The live contract now
requires complete ordered intermediate counts (`[3]`, `[8]`, and `[2, 1, 1]`)
in addition to final metrics. After clarifying that a nested container remains a
child even when it opens another builder closure, both locked model profiles
passed that strict contract. The preserved successful run IDs are
`20260924T134643Z-c94a3997` for Codex and
`20260924T134950Z-ef6634cc` for Claude.

An intervening Codex attempt failed before workflow execution because its
generated session did not expose the flow-engine function. An unchanged runner
configuration exposed the function on immediate rerun and completed the strict
contract, so this is recorded as a transient live-session registration failure,
not as workflow evidence.

## Approved ISP Follow-up — Unable to Verify

Recorded 2026-10-06 for the next ISP revision. This requirement is not implemented
by the completed migration above. The saved
[ISP discussion draft](resources/isp-workflow-draft.yaml) remains inactive.

As a reviewer, I want insufficient evidence reported as **unable to verify** so
missing conformer evidence cannot appear to prove compliance.

### Outcome contract

- **Unable to verify** is an evidence outcome, not a severity, a whole-rule
  exception, or a successful measurement. It must not manufacture a numeric
  value, such as 100% coverage or zero cohesion groups.
- Apply the outcome only to metrics whose required evidence is unavailable.
  Independently measurable interface width still receives its normal score;
  known violations are retained in the combined review result.
- MCP derives the outcome from recorded discovery/analysis limitations and
  validated classifications. Persist the affected unit and metric identities,
  reason, available evidence, and missing evidence in the normal run audit.
  The review summary exposes the outcome and a concise explanation; detailed
  evidence remains in the audit rather than the gate's model-facing message.
- An empty search result does not prove that no conformers exist. A bounded
  search returning one conformer does not prove that it is the only conformer.
  Discovered evidence and discovery completeness must remain distinguishable.
- Missing, duplicate, unknown, or invalid required model submissions remain
  validation errors with retry instructions. They are not converted into
  unable-to-verify results. A timeout or failed source operation remains an
  execution failure, not an evidence outcome.

### Acceptance scenarios for the follow-up

1. **Given** discovery completes without usable non-test conformer evidence,
   **when** ISP evaluates coverage and conformer-based cohesion,
   **then** those metrics report unable to verify, with the evidence limitation,
   and neither 100% coverage nor zero-group compliance is fabricated.
2. **Given** every discovered conformer is excluded as test code,
   **when** no eligible evidence remains,
   **then** the affected metrics report unable to verify and the audit retains
   the exclusions that explain the empty eligible set.
3. **Given** an interface declares nine requirements but conformer evidence is
   unavailable, **when** ISP finalizes its result,
   **then** ISP-1 remains SEVERE while the evidence-dependent metrics report
   unable to verify; the interface is not exempted as a whole.
4. **Given** complete eligible conformer evidence establishes coverages of
   1.0, 0.75, and 0.5, **when** MCP scores ISP-2,
   **then** the measured minimum remains 0.5 and existing severity bands apply.
5. **Given** a required classification is omitted from an aggregate submission,
   **when** MCP validates it, **then** the missing work remains pending and the
   response identifies what to resubmit; unable to verify cannot satisfy it.
6. **Given** an unable-to-verify result and its supporting audit are persisted,
   **when** the run is replayed, **then** the same outcome and explanation are
   reconstructed without searching again or converting the outcome to COMPLIANT.

### Pending implementation decisions

The next ISP/source-analysis specs must define the typed outcome representation,
discovery-completeness signals, and workflow binding. Gate handling must depend
on review context rather than treating every unable-to-verify result identically.
A newly introduced interface with no conformers is warning-eligible: retain the
unable-to-verify outcome without claiming compliance. The evidence needed to
establish that context and the policy for other cases still need definition;
zero search hits alone do not establish a first interface. Missing submissions
and failed operations remain errors rather than warning-eligible outcomes.

SPEC-062 implements the source-member inventory prerequisite. It does not activate
the ISP draft or choose the remaining gate policy. Do not claim
runtime support until those contracts and the scenarios above are implemented.
The scoring policy for the separate extension metric is still undecided and is
not changed by this requirement.

### Source-analysis module boundary and discovery contract

The next ISP revision must keep code parsing and structural analysis in a
dedicated, reusable source-analysis package within `mcp-server/source/`. Reuse
the existing parser pipeline and SPEC-062 member inventory rather than adding
an ISP-specific parser or copying their implementations.

- The source-analysis package owns declaration/member extraction, normalized
  signatures, conformance and extension relationships, visibility facts, source
  identities/ranges, and explicit unresolved or unsupported-analysis diagnostics.
  Language-specific parsing stays behind that package's typed contracts.
- MCP operation handlers adapt typed inputs and outputs to those capabilities.
  The workflow engine, gate, prompt renderers, and scoring components must not
  parse source code or interpret language-specific declaration syntax.
- Search remains candidate discovery, not structural proof. The initial ISP
  query contains only the full interface identifier: no generated synonyms,
  tags, or expanded name fragments. Reuse the existing typed search machinery;
  a new `name` shorthand or operation name shown in a discussion draft is not
  an implemented or required public contract.
- After analysis establishes conformer identities, discovery may search their
  exact names to locate separate extensions that do not mention the interface.
  Do not repeat discovery when those extensions are already known. Preserve
  search bounds and unresolved inherited or conditional relationships instead
  of claiming that every conformer or extension has been found.
- Match members to requirements using parsed signatures and established owner
  relationships, not textual signature equality or matching names alone.
  Account for overloads and supported generic constraints, and include property
  and associated-type requirements rather than limiting analysis to functions.
  Unsupported or ambiguous matches remain explicit analysis limitations.
- Analyze relevant candidate sources and prospective buffers through the shared
  source context. Do not require parsing every searched file merely to return
  candidate metadata, and do not ask the LLM to reconstruct structural links.
- Workflow YAML owns `for_each`/`when` filtering, classification instructions,
  exception policy, and scoring declarations. Exclude `private`/`fileprivate`
  members before LLM presentation. The LLM classifies implementation behavior
  and extension responsibilities with reasoning/evidence; MCP calculates metrics
  through generic workflow mechanics. The analysis package must not embed ISP
  thresholds, severity decisions, or rule-specific exception policy.

### Additional acceptance scenarios — discovery and aggregate execution

1. **Given** a conformer declares its interface in one file and implements a
   requirement in a separate extension that mentions only the conformer's name,
   **when** discovery and source analysis run, **then** the exact interface-name
   query locates the conformance and an exact conformer-name lookup locates the
   extension when needed; no synonyms or tags broaden either query.
2. **Given** an unrelated type has an identical method signature and a real
   conformer has overloaded members or different internal parameter names,
   **when** source analysis matches requirements, **then** owner relationships
   and normalized signatures identify the supported matches without including
   the unrelated type or relying on raw declaration-string equality.
3. **Given** generic constraints, inherited relationships, or missing source
   prevent a reliable match, **when** analysis finishes, **then** typed diagnostics
   retain the ambiguity and affected identities; downstream evidence-dependent
   metrics follow the unable-to-verify contract rather than assuming completeness.
4. **Given** an aggregate ISP workflow has inventory, search, and relationship
   operations plus eligible and private/fileprivate members, **when** it advances,
   **then** MCP executes and persists the prerequisite operations before dependent
   agent work, records visibility-based skips, and presents only eligible members.
   Engine-owned operations are not converted into LLM instructions or absorbed
   into a combined prompt.
5. **Given** all eligible classifications arrive in a combined submission,
   **when** MCP advances the workflow, **then** it maps every classification to
   its original member/step instance, executes the ready scoring steps, and
   persists the fixture's expected metric values and evidence. Assertions cover
   calculated results and operation outputs, not just rendered prompt contents.
6. **Given** a combined submission omits or invalidates one member assessment,
   **when** MCP validates it, **then** accepted sibling work remains completed,
   missing or rejected work remains pending, and dependent calculations wait.
   Independently ready calculations may complete without reopening valid work.
7. **Given** completed operation outputs, classifications, skips, and metric
   results are persisted, **when** the run resumes or replays, **then** it restores
   those results and pending identities without repeating completed search,
   parsing, or scoring. This does not promise exactly-once execution across a
   crash before an operation's completion was persisted.

These scenarios remain pending for the ISP follow-up. Existing generic aggregate
tests do not establish that the proposed ISP workflow or its unfinished scoring
and outcome bindings are implemented.

### Approved shared parser direction — Tree-sitter

Use Tree-sitter behind the dedicated source-analysis package, with injected
language grammars. This replaces the proposed Swift-only syntax-library approach,
not the lightweight candidate search. Tree-sitter supplies concrete syntax trees;
it does not by itself resolve symbols, prove conformance, or establish semantic
equivalence. Language adapters must publish the existing typed source facts and
explicit limitations rather than exposing grammar node names to workflow logic.

The first parser qualification covers these cases in
`tests/mcp-server/source/analysis/test_tree_sitter_syntax_parser.py`:

1. **Given** overloaded Swift requirements, **when** their syntax is parsed,
   **then** external parameter labels and declared types remain distinguishable.
2. **Given** a conformance and a separate extension, **when** both are parsed,
   **then** the inherited name and extension owner are preserved for subsequent
   relationship resolution; parsing alone does not claim a resolved relationship.
3. **Given** associated types, property requirements, and private/fileprivate
   members, **when** they are parsed, **then** member kinds and explicit visibility
   modifiers remain available to the typed member inventory.
4. **Given** constrained extensions and generic methods, **when** they are parsed,
   **then** their declared constraints are retained rather than silently erased.
5. **Given** an incomplete prospective buffer, **when** parsing recovers a partial
   tree, **then** the parse error remains visible and is not an empty success.
6. **Given** non-ASCII source, **when** declaration ranges are read,
   **then** UTF-8 byte ranges identify the original source text correctly.
7. **Given** a TypeScript grammar instead of Swift, **when** the same parser adapter
   is used, **then** interface and class declarations parse without Swift-specific
   behavior in that adapter.

All seven checks passed on 2026-10-06 in each of two isolated environments:

- Python 3.9.6, Tree-sitter 0.23.2, Swift grammar 0.0.1, TypeScript grammar 0.23.2.
- Python 3.12.14, Tree-sitter 0.26.0, Swift grammar 0.7.4, TypeScript grammar 0.23.2.

The current Swift grammar uses language ABI 15, which Tree-sitter 0.23.2 cannot
load. Python 3.10 or newer was approved as the minimum on 2026-10-06. The supported
configuration pins Tree-sitter 0.26.0, Swift grammar 0.7.4, and TypeScript grammar
0.23.2 in `requirements.txt`; do not retain an older-grammar fallback for Python
3.9. The earlier Python 3.9 results are historical qualification evidence only.
These checks qualify the listed syntax cases, not the completeness of either
grammar. They preceded the production parser integration recorded below. No
global interpreter change has been made.

MCP servers and hooks currently invoke `python3` through the host process's PATH.
That interpreter must be Python 3.10+ with the declared dependencies installed;
installing them under another Python does not change the plugin's launch path.
The README documents this setup. Dependency resolution against Python 3.10 wheels
passes; the qualification tests execute under isolated Python 3.12.14, not an
actual Python 3.10 interpreter.

Verification on 2026-10-06: all 83 source tests passed in both qualification
environments. After approving the new baseline, the complete non-live sweep under
Python 3.12 also passed with 2,512 tests and four skips, including the new parser
checks and mocked hook E2E tests. The earlier Python 3.9 sweep reached the same
result after eight tests were rerun unchanged with access to their expected
`~/.solid-coder` test directories.

The existing shared live catalog contract also passed for both locked profiles
(Codex `gpt-5.6-terra` and Claude `claude-opus-4-5`): two tests in 59.14 seconds.
The test process and its child-process PATH used the isolated Python 3.12
environment. These checks verify existing engine behavior under that runtime;
they do not establish production integration of Tree-sitter or the ISP draft.
The approved dependencies are declared in the repository and installed only in
the isolated qualification environment; the user's global Python and local
configuration remain unchanged.

Implementation sequence:

1. Completed: declare compatible runtime/grammar dependencies, resolve Python
   3.10 wheels, and verify installation and parser checks under Python 3.12.
2. Partially completed: the existing source/member inventory, direct ownership,
   effective visibility, source ranges, incomplete/unsupported diagnostics, and
   technology tags now use the shared parser. Grammar-specific traversal stays
   inside the source-analysis package and the existing analyzer registry is
   reused. Initial typed signatures are now published for methods, lifecycle
   members, explicitly typed properties, and associated types (see the
   2026-10-07 progress entry). Remaining signature forms and structural
   relationship facts are still pending; extraction does not prove conformance.
3. Implement bounded relationship resolution, including separate extensions,
   overloads, unrelated same-signature members, and unresolved constraints; do not
   substitute identifier matches for semantic proof.
4. Connect the thin source operations and inactive ISP draft, then implement the
   discovery, aggregate submission/scoring, partial recovery, and replay scenarios
   above before activating it.
5. Run all non-live tests and the locked Codex/Claude flow-engine checks after
   production integration. Parser qualification alone is not end-to-end evidence.

### Production parser integration — 2026-10-06

`SourceAnalysisOperationFactory` now routes Swift file and buffer analysis through
Tree-sitter. One syntax parse produces a typed inventory consumed by the existing
source analyzer and tag detectors. `SourceUnit`, `SourceMember`, source evidence,
the language registry, and the public `source.analyze` result contract are reused.
No compiler subprocess or temporary Swift source file is needed for analysis.

The dedicated `source/analysis/` package owns grammar traversal and member-name,
access, range, import, syntax-signal, and diagnostic extraction. The existing
visibility policy consumes typed access levels rather than compiler JSON.
The unused compiler-JSON adapters, subprocess runner, and tag-evidence path were
removed; search remains parser-free.

Verified cases include:

- One shared parse supplies units, members, and technology tags.
- Direct member ownership, overload identities, associated types, lifecycle
  members, subscripts, property bindings, and effective access remain covered.
- Return types and associated-type constraints are not additional member names.
- Equivalent file and prospective-buffer analysis preserves Unicode evidence;
  incomplete buffers retain usable declarations and explicit diagnostics.
- Comments and string text, including raw strings, do not activate technology
  rules; executable string interpolation still can. Tag evidence identifies the
  actual code instead of an earlier matching comment.
- Workflow replay retains member facts without another parse, and both shared
  search entry points are guarded against invoking the new parser.

Validation under isolated Python 3.12.14: **90 source tests passed**; the complete
non-live sweep passed with **2,519 tests and four skips**. The existing shared live
catalog contract passed for Codex `gpt-5.6-terra` and Claude `claude-opus-4-5`:
**two tests in 64.34 seconds**, including nested workflow IDs, scripts, commands,
and completion. The child-process PATH used the same isolated Python runtime.
The user's global interpreter and local TOML were not changed.

This completes the existing-inventory parser replacement, not the ISP follow-up.
Normalized signature facts, bounded interface/conformer/extension resolution,
discovery-completeness outcomes, the inactive ISP draft's bindings, and its
aggregate submission/scoring/recovery scenarios remain pending. The live catalog
checks do not establish completion of those ISP scenarios. TypeScript remains a
parser qualification case, not a newly registered production language analyzer.

### Initial member-signature extraction — 2026-10-07

The existing `source.analyze` path now publishes a typed signature on each source
member. Extraction stays in `source/analysis/signatures/`, reuses the existing
syntax-parsing contract and member-decoder factory, and consumes the existing
syntax tree rather than parsing the file again. Search and candidate discovery
remain unchanged and parser-free. No new public MCP tool or ISP-specific scorer
was introduced, and the ISP discussion draft remains inactive.

Implemented facts and verified cases:

- Callable signatures preserve ordered external labels, parameter types,
  variadics, result types, declaration modifiers, generic parameters, and
  constraints. Typed throws retains its error type; failable initializers retain
  their failure marker.
- Internal parameter renaming, supported formatting/comment trivia, default
  expressions, and implementation bodies do not alter the extracted callable
  shape. Different external labels and overload parameter types remain distinct.
- Explicitly typed properties retain their own binding's type, getter/setter
  facts, async/throwing getter effects, and declared modifiers, including private
  setter restrictions. Associated types retain bounds, defaults, and constraints.
- Property and callable result types preserve type attributes such as `@Sendable`.
- Discriminated signature variants survive source-analysis JSON serialization
  and decoding without manual dictionary mapping.
- Inferred or destructured property types, unavailable accessor shapes,
  incomplete declarations, and currently unsupported subscript signatures remain
  explicitly unresolved. Existing member identity, kind, visibility, and source
  evidence are preserved even when a signature is unresolved.

The pinned Swift grammar rejects a comment between a property identifier and its
colon (for example `var count /* units */ : Int`). A test records the resulting
partial analysis and diagnostics rather than asserting fabricated signature
facts. Supported comments inside type annotations are covered separately.

These are syntax facts, not semantic type equivalence or conformance decisions.
Type aliases, generic substitution, constraint satisfaction, declaration-owner
relationships, and cross-file requirement matching are not inferred from equal
token sequences. An unresolved signature is also not yet the metric-level
**unable to verify** outcome described above; that workflow/result binding
remains pending.

Validation: **22 new signature integration tests passed**. The complete non-live
sweep passed with **2,541 tests and four skips**, including the non-live tests for
live-session runner infrastructure. The existing shared catalog E2E passed for
locked Codex `gpt-5.6-terra` and Claude `claude-opus-4-5`: **two tests in 70.04
seconds**. These live checks cover existing nested workflow, script, command, and
completion behavior; they do not establish completion of the ISP follow-up.

Next: complete the remaining signature forms and publish declaration relationship
facts, then implement bounded interface/conformer/extension resolution and its
workflow bindings. Aggregate submission/scoring/recovery and evidence-outcome
scenarios remain required before activating the revised ISP workflow. Local TOML,
global Python configuration, and bundled workflow YAML were not changed.
