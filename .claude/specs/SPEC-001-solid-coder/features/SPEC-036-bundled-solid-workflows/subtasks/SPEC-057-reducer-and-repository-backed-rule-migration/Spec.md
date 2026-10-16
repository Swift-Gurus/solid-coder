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

Current follow-up status (2026-10-16): the full bundled ISP workflow and explicit
metric-level unavailable outcomes are implemented. Tests load the bundled rule,
not a separately maintained ISP policy fixture. The latest validation and
remaining gate-policy boundary are recorded at the end of this document;
earlier dated progress entries are historical.

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
The extension policy was subsequently agreed in the 2026-10-15 decision below:
combined interface width extends ISP-1, while mixing independent responsibilities
is a separate SEVERE signal. Implementation and evidence-outcome binding remain
pending; this decision does not activate the discussion draft.

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
   members, explicitly typed properties, and associated types. Typed declaration
   headers now preserve inherited references, extension targets, generic
   parameters, constraints, and modifiers (see the 2026-10-07 progress entries).
   Remaining signature forms and resolved declaration relationships are still
   pending; extraction does not prove conformance.
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

### Declaration-header facts — 2026-10-07

`source.analyze` now publishes a discriminated declaration signature on each
supported top-level type or extension. The signature retains the declared name,
ordered inherited type references, generic parameters, constraints, and modifiers.
Type references include their original source-line evidence. Unsupported or
incomplete declaration signatures remain explicitly unresolved rather than
claiming an empty, successfully analyzed header.

The extraction uses the existing syntax tree and parser contract. Type-reference
conversion is a separate injected parser from declaration-header extraction;
both remain inside `source/analysis/signatures/`. No new protocol, search path,
public MCP operation, or ISP-specific scoring behavior was added.

The 11 new source-analysis integration tests establish these cases:

- Given ordered, module-qualified inherited names or generic arguments, when
  analysis runs, then their tokens and source evidence remain available without
  declaring that the referenced symbols have been resolved.
- Given a protocol inherits another protocol, when its direct members are
  inventoried, then inherited requirements are not fabricated or mixed into that
  direct-member inventory.
- Given a qualified extension target, conformance clause, or generic constraint,
  when analysis runs, then target and inherited references remain distinct and
  the authored constraints are preserved.
- Given declaration attributes, access modifiers, or comments, when analysis
  runs, then modifiers remain syntax facts and supported comment trivia does not
  alter type tokens. Attributes do not themselves apply rule exceptions.
- Given nested declarations, recovered malformed syntax, or a free function,
  when header analysis runs, then child inheritance does not leak into its parent,
  malformed declarations stay unresolved with partial-analysis diagnostics, and
  functions do not acquire a fabricated nominal header.
- Given persisted analysis JSON, when it is decoded, then the typed declaration
  facts and their evidence are restored unchanged.

Validation: **11 new integration tests passed**; the complete non-live sweep
passed with **2,552 tests and four skips**. The locked Codex `gpt-5.6-terra` and
Claude `claude-opus-4-5` workflow-catalog E2E checks passed: **two tests in 55.68
seconds**. These live checks cover the existing nested workflow, process-step,
and completion contract, not the unfinished ISP workflow.

This supplies declared relationship inputs, not a resolved relationship graph.
Nested declaration ownership, cross-file symbol resolution, inherited or
conditional conformance, and requirement-to-implementation matching remain
pending. The existing inventory is still top-level; no nested type is silently
promoted into that inventory. Remaining member-signature forms and ISP workflow
bindings, including aggregate result/scoring/recovery scenarios, still need to be
completed before the discussion draft is activated. Candidate search, bundled
workflows, local TOML, and the user's global Python were unchanged.

### Subscripts and bounded declaration links — 2026-10-07

The first cross-file resolver follows the approved choice: **bounded links;
preserve uncertainty**. Verified module ownership is not a prerequisite for
returning these candidate links, and those links are not proof of conformance.

`source.analyze` now retains typed subscript signatures, including external
parameter labels, result types, generic constraints, and accessor effects.
Subscripts reuse the existing callable extraction; properties and subscripts
share accessor extraction. Empty, incomplete, or unsupported accessor shapes
remain unresolved rather than acquiring fabricated capabilities.

The reusable `source/analysis/relationships/` capability consumes already
analyzed sources. It retains the supplied analyses and diagnostics alongside
ordered inheritance-reference and extension-target results. Its scope is
explicitly `supplied_top_level_sources`, with `unverified_candidates` verification:

- One exact eligible declaration-name match produces a candidate, not a verified
  conformance. Unrelated identical members do not create a relationship.
- Multiple matching declarations remain ambiguous with every candidate identity.
- Missing declarations, qualified or compound references, and unevaluated generic
  or conditional applicability remain unresolved with a reason. Possible targets
  are retained when available; constraints and source evidence are not erased.
- Separate extension targets and their inheritance clauses remain distinct links.
  Existing typed source/unit identities are reused without parsing identity strings.
- Duplicate snapshots for one source identity are rejected. Empty, partial, and
  unsupported inputs never establish repository completeness; their bounded scope
  and available diagnostics survive JSON round-trip persistence.

The new service does not search, read files, or parse source again. It is not yet
exposed as a workflow operation, and the inactive ISP draft is unchanged. Semantic
module ownership, nested ownership, transitive conformance, and requirement-to-
implementation matching are not supplied by this slice. The remaining ISP work
still includes member matching, operation/workflow bindings, unable-to-verify
results, and aggregate submission/scoring/recovery validation before activation.

Validation: **10 subscript and 15 relationship integration tests passed**; all
**148 source tests passed**. The complete 19-root non-live sweep passed with
**2,577 tests and four skips**. The existing locked Codex `gpt-5.6-terra` and Claude
`claude-opus-4-5` workflow-catalog E2E checks passed: **two tests in 66.43 seconds**.
Those live checks cover the existing nested workflow, process-step, and completion
contract, not completion of the revised ISP workflow. Local TOML, candidate
search, bundled workflows, and the user's global Python remain unchanged.

### Bounded direct requirement matching — 2026-10-14

The reusable `source/analysis/matching/` package now consumes an existing source
relationship inventory and one recorded inherited-type relationship. It produces
ordered matches for the candidate interface's direct requirements, retaining the
original inspected analyses, relationship uncertainty, member identities,
visibility, signatures, and source-line evidence. It does not search, read source
files, parse again, calculate coverage, or classify implementation behavior.

Implemented and verified cases:

- Direct members, separate conformer extensions, extension-declared conformance,
  and protocol-extension defaults retain their declaring owners. Unrelated types
  with identical signatures are not included.
- Supported callable matching distinguishes external labels, parameter types,
  result types, and modifiers without depending on internal parameter names.
  Property and subscript candidates account for required accessor capabilities.
- Multiple possible implementations or ambiguous extension owners remain
  ambiguous; generic or conditional owner links retain their unresolved status.
  Matching syntax is a candidate signal, never verified conformance or dispatch.
- Missing supported matches remain unresolved. Associated-type requirements are
  retained, but type-alias witnesses, inferred associated types, and generic
  substitution/constraint satisfaction are not resolved by this slice.
- Protocol inheritance is not treated as implementation, and inherited
  requirements are not silently added to the direct-member inventory. Partial
  analysis diagnostics remain attached to the supplied source snapshot.
- JSON round trips preserve the result and its evidence. Matching a restored
  inventory needs no source analysis; a relationship from another snapshot is
  rejected rather than combined with current evidence.

All signature comparisons use one generic behavioral contract; the first
implementation owns that contract. The service and typed result models remain
inside the source-analysis package, with mirrored tests under
`tests/mcp-server/source/analysis/matching/`.

This is not yet a public workflow operation or activation of the revised ISP
draft. Visibility facts are retained for the pending workflow's private and
fileprivate filtering. Discovery completeness, semantic and inherited matching,
operation/workflow bindings, metric-level unable-to-verify results, and the ISP
aggregate submission/scoring/recovery scenarios remain outstanding.

Validation: **25 new integration tests passed**. The complete 19-root non-live
sweep passed with **2,616 tests and four existing abstract-base skips**. On
2026-10-15, the existing workflow-catalog live contract passed for both locked
profiles, Codex `gpt-5.6-terra` and Claude `claude-opus-4-5`: **2 passed in
193.03 seconds**. It verifies nested workflow-ID resolution, ordered engine-owned
script/command execution, model submissions, completed outputs, and session
identity; it does not establish the pending ISP workflow integration.

The earlier sandboxed Codex attempt timed out before any model response, and
Claude was interrupted after both model API hosts failed sandbox DNS checks.
Following explicit user approval, the same tests passed with network access.
No test assertions, model profiles, or production behavior changed for the
retry. Codex still performed extra tool-discovery calls before starting the
workflow; discovery efficiency is not asserted by this passing contract.

Live evidence is retained under `.solid-coder/.artifacts/test/`:

- Codex: `codex/e2e/flow-engine/workflow-catalog/20261015T124055Z-6db754c8/`.
- Claude: `claude/e2e/flow-engine/workflow-catalog/20261015T124329Z-f8dc063e/`.

### Engine-owned source relationship operations — 2026-10-15

The existing analysis, relationship resolution, and requirement matching services
are now connected through typed internal workflow operations. Source parsing and
matching remain in the dedicated source-analysis package; the engine does not
interpret source syntax or introduce an ISP-specific execution path.

The workflow-boundary contracts are:

| Operation | Inputs | Named outputs |
|---|---|---|
| `source.analyze` | `source` | `result`: one complete source analysis |
| `source.resolve_relationships` | `analyses`: ordered complete analyses | `result`: complete bounded inventory; `relationships`: its ordered links |
| `source.match_requirements` | `inventory`, `relationship` | `inventory`, `relationship`, `matches` |

The workflow-facing analysis contract now exposes the complete analysis as one
named `result`, rather than exposing its fields as independent step outputs.
Direct analysis-service consumers, including review preparation, are unchanged.
Existing workflow consumers must bind `steps.<analysis-step>.outputs.result`.
Ordinary `for_each` fan-in collects these complete objects in source order.
The relationship collection is also published as a named output so ordinary
`for_each` can iterate it while passing the complete inventory separately.

No whole-step reference syntax, nested-object construction in `with`, or
parameter-based `for_each` syntax was added. Existing named-output expressions,
child-workflow parameters, conditions, fan-out, and replay are reused. An
operation result adapter shares the existing generic operation contract; it does
not define another execution interface or duplicate the source-analysis service.

#### Acceptance and integration evidence

- **Given** file paths submitted at the workflow's selection boundary, **when**
  per-file analysis completes, **then** relationship resolution receives each
  complete snapshot once and in input order, including its identities and facts.
- **Given** a protocol, conformer, and separate extension, **when** engine-owned
  matching runs in an included workflow, **then** it persists the extension's
  member evidence before returning the combined model-owned classification work.
- **Given** an extension-target link rather than an inherited-type link, **when**
  the authored include condition is evaluated, **then** that child is skipped;
  the source operation does not embed a rule-specific selection policy.
- **Given** a combined classification submission, **when** all required values
  validate, **then** the workflow completes without asking the model to resubmit
  operation outputs.
- **Given** a missing or invalid sibling classification, **when** the model
  submits the remaining or corrected value, **then** accepted siblings and
  completed operation evidence are retained without re-executing analysis.
- **Given** completed operation evidence and subsequently deleted source files,
  **when** another orchestrator instance resumes the run, **then** the same
  matching evidence is restored and the workflow completes without rereading.
- **Given** no supported implementation match, **when** matching results are
  persisted, **then** the result remains unresolved rather than becoming a
  fabricated compliance result.

The fixture and child workflow live under
`tests/harness/flow_engine/fixtures/source_relationship_operations/`, not in the
distributed workflow catalog. Nine registered-operation tests, seven workflow
integration tests, and the two existing source-analysis workflow tests pass.
The complete 19-root non-live sweep passes with **2,632 tests and four existing
skips**. After explicit approval to transmit the test inputs, the existing locked
Codex/Claude workflow-catalog live checks passed: **2 tests in 66.87 seconds** on
2026-10-15. Retained artifact directories under `.solid-coder/.artifacts/test/`:

- Codex: `codex/e2e/flow-engine/workflow-catalog/20261015T193608Z-36a27afa/`.
- Claude: `claude/e2e/flow-engine/workflow-catalog/20261015T193644Z-a960c60e/`.

These checks validate the shared engine contract, not the revised ISP workflow.

This completes operation binding, not the ISP follow-up. Discovery completeness,
private/fileprivate workflow filtering, behavior classification, implementation
of the extension policy below, metric-level unable-to-verify outcomes, and the
ISP-specific aggregate scoring/recovery contract remain pending. Bundled review
workflows have not been activated or changed by this slice.

### Agreed interface-extension policy — 2026-10-15

The following decisions supersede the earlier open extension-scoring question.
They are requirements for the inactive ISP revision, not a claim of runtime
support or a change to the currently distributed ISP workflow.

#### Combined exposed width — ISP-1

- Extend the existing width metric rather than adding another width metric.
- Count requirements declared directly by the interface together with additional
  non-private members introduced by its extensions. Retain the existing exclusion
  of inherited requirements.
- Exclude private/fileprivate extension members before model presentation and
  width calculation. Members belonging only to conformers or their extensions
  do not increase the interface's width.
- A default implementation of an existing requirement does not add another
  width entry. Preserve distinct overloads using structural member identities
  and supported signatures, not names alone.
- MCP derives the unique member count from source-analysis facts. The model does
  not count members or choose severity.
- Preserve the existing inclusive bands: 0–5 COMPLIANT, 6–8 MINOR, and 9 or more
  SEVERE. Unknown ownership or extension applicability remains an evidence
  limitation rather than a fabricated exact count.

#### Independent responsibilities introduced through extensions

- Flag mixing independent responsibilities through the interface's exposed
  extension behavior as SEVERE, even when combined width is below six.
- This is separate from ISP-1 width and ISP-3's conformer-based cohesion signal.
- The model classifies member responsibilities and their relationship to the
  interface's existing behavior, retaining reasoning and evidence. The mere
  presence of an extension, default implementation, or several methods does
  not establish independent responsibilities.
- Workflow-authored scoring applies the SEVERE policy from the validated
  classification. Do not hardcode an ISP-specific scorer in source analysis or
  the engine, and do not treat missing classifications as compliance.

#### Acceptance and test cases

1. **Given** six directly declared requirements and three additional eligible
   interface-extension members, **when** MCP calculates width, **then** ISP-1 is
   9 and SEVERE.
2. **Given** six requirements and defaults for those same six requirements,
   **when** MCP calculates width, **then** ISP-1 is 6 and MINOR, not 12.
3. **Given** three requirements and two additional eligible extension members,
   **when** MCP calculates width, **then** ISP-1 is 5 and COMPLIANT for width.
4. **Given** combined eligible counts of 5, 6, 8, and 9, **when** MCP scores width,
   **then** severities are COMPLIANT, MINOR, MINOR, and SEVERE respectively.
5. **Given** private/fileprivate extension helpers and conformer-only members,
   **when** the workflow prepares interface members, **then** those members do
   not increase ISP-1 and private/fileprivate helpers are not sent for judgment.
6. **Given** distinct overloads and a matching default implementation,
   **when** MCP identifies unique exposed members, **then** overloads remain
   separate and the matching requirement/default pair contributes once.
7. **Given** combined width of five and validated evidence of mixed independent
   responsibilities through extensions, **when** scoring completes, **then**
   ISP-1 remains COMPLIANT and the separate responsibility finding is SEVERE.
8. **Given** several extension members serving one responsibility, **when** their
   classifications are evaluated, **then** member count alone does not create a
   mixed-responsibility finding; ISP-1 still applies independently.
9. **Given** ambiguous ownership or conditional applicability, **when** it
   prevents establishing the relevant member set, **then** the affected result
   preserves its evidence limitation instead of claiming an exact compliant
   width; independently established findings are retained.
10. **Given** a combined submission with a missing or invalid responsibility
    classification, **when** the model corrects only the pending work, **then**
    accepted siblings and completed operations remain recorded and dependent
    scoring waits for valid evidence.
11. **Given** persisted member facts, classifications, exclusions, and scores,
    **when** the run replays, **then** the same values and evidence are restored
    without repeating completed search or analysis.

#### Implementation sequence

1. Wire the existing source operations into a test-owned ISP workflow fixture;
   cover interface-name discovery, separate extensions, and visibility filtering.
2. Add failing integration assertions for the combined-width and responsibility
   cases above, including actual scoring after aggregate submissions.
3. Implement the remaining reusable bindings and evidence outcomes as needed;
   keep ISP policy in YAML and semantic classification in model-owned steps.
4. Update the inactive draft to use the validated contracts, then run all non-live
   tests and locked ISP-specific Codex/Claude live checks before activation.

### Interface-extension member contributions and scoring integration — 2026-10-16

The registered `source.declaration_members` operation accepts a bounded source
`inventory` and one prepared `declaration` identity. It returns `inventory`,
`declaration`, and ordered `members`. Each contribution retains its owner, member
signature, visibility, source evidence, matching declarations, and a typed role:
`declared`, `implementation`, `additional`, or `unresolved`.

Member collection is shared with requirement matching; signature matching reuses
the same callable, modifier, and accessor capabilities. The operation does not
search, reread files, classify responsibilities, or calculate ISP scores.
Conditional or ambiguous extension ownership and unsupported signatures remain
unresolved. Inherited requirements are not expanded into the direct inventory;
an unmatched extension member on an inheriting declaration remains unresolved
until inherited-member identity can be established. File-granularity identities
and declarations absent from the supplied snapshot are rejected.

The test-owned workflow at
`tests/harness/flow_engine/fixtures/isp_extension_review/workflow.yaml` now
executes source analysis, relationship resolution, and member analysis inside MCP
before returning batched model classifications. YAML owns visibility filtering,
the existing ISP-1 width bands, and an ISP-4 independent-extension-responsibility
signal with a SEVERE threshold of one. This fixture receives explicit prepared
source snapshots; it does not establish repository-discovery completeness or
model-classification accuracy.

Verified cases:

- **Given** six direct requirements and three additional exposed extension
  members, **when** the workflow completes, **then** MCP records width nine and
  SEVERE. Counts five, six, eight, and nine exercise the inclusive bands.
- **Given** matching defaults, supported overloads, properties, or subscripts,
  **when** member contributions are resolved, **then** supported defaults do not
  add width and distinct overloads remain separate.
- **Given** private/fileprivate or conformer-only members, **when** the workflow
  prepares judgment work and scores width, **then** those members are excluded.
  Empty and private-only extension collections need no member-classification
  submission and produce zero independent-responsibility observations.
- **Given** a narrow interface with independently classified extension
  responsibilities, **when** the model submits its classifications, **then** MCP
  records ISP-4 as SEVERE even though ISP-1 remains COMPLIANT.
- **Given** partial or invalid batched classifications, **when** the model
  corrects the pending subset, **then** accepted work is retained, scoring waits
  for complete valid classifications, and completed source operations do not
  rerun. Replay still completes after the original source files are removed.
- **Given** ambiguous or conditional ownership, generic signatures, or an
  unresolved inherited-member relationship, **when** the operation result is
  serialized and restored, **then** its uncertainty and original evidence remain
  available rather than becoming a fabricated additional-member count.

#### Shared operation-schema correction

Integration exposed an existing schema boundary gap: operation output extraction
dropped Pydantic definitions, leaving nested `$ref` fields unavailable to
`scoring.when` and producing dangling references during validation. Reference
expansion now sits behind the existing `StructuredModelDecoding` contract,
separate from typed schema decoding and output-spec construction. The JSON-schema
library identifies actual schema nodes; literal defaults/examples are not
interpreted as references, and properties named like schema keywords still work.
Original references and definitions remain available so recursive schemas and
constraints alongside `$ref` retain their validation semantics. `referencing`
is declared directly in `requirements.txt`; it was already installed as a
dependency of JSON Schema validation.

Coverage resides in:

- `tests/harness/flow_engine/test_isp_extension_review_flow.py`: ten workflow
  tests and six boundary/empty-collection subtests.
- `tests/mcp-server/source/analysis/operations/test_source_declaration_members_operation.py`:
  ten source-operation tests.
- `tests/harness/flow_engine/test_pydantic_operation_output_specs_resolver.py`:
  nine schema-boundary tests.

The final complete 19-root non-live sweep passed with **2,661 tests, four existing
skips, and 175 subtests**. The existing locked Codex/Claude workflow-catalog E2E
checks passed: **two tests in 61.93 seconds**. Their retained test artifacts are
under `.solid-coder/.artifacts/test/`:

- Codex: `codex/e2e/flow-engine/workflow-catalog/20261016T150801Z-f0650e94/`.
- Claude: `claude/e2e/flow-engine/workflow-catalog/20261016T150833Z-f6d23260/`.

These live checks validate the shared flow engine, not the revised ISP policy or
the accuracy of its classifications. The spec remains in progress. Still required:
connect interface-name discovery and MCP-prepared target identity to the revised
ISP draft; finish coverage/cohesion and exception bindings; represent metric-level
unable-to-verify outcomes without turning missing evidence into compliance; and
run ISP-specific Codex/Claude live scenarios before activating the revised bundled
workflow. No distributed workflow or local TOML was changed by this slice.

### Full bundled ISP and explicit unavailable outcomes — 2026-10-16

The full rule now lives in `workflows/review/rules/isp/workflow.yaml`, with its
included conformer-evidence workflow in `candidate-review/workflow.yaml`.
Deterministic integration and locked-model tests resolve those actual packages.
The duplicate extension-policy YAML under the test harness and the unused old
candidate assessment schema have been removed. The discussion draft is historical,
not an additional executable policy to keep synchronized.

The bundled sequence composes these existing responsibilities:

1. MCP discovers related declarations using the exact interface name and, when
   necessary, discovered owner names for separate extensions. It preserves the
   prospective source snapshot, search bounds, source facts, and limitations.
2. MCP resolves member contributions and calculates combined exposed width;
   private/fileprivate members are filtered before extension judgment and width.
3. Included conformer workflows run structural requirement matching in MCP,
   request evidenced behavioral classifications, and calculate coverage ratios.
4. With at least two eligible, verifiable conformers and no discovery limitation,
   the workflow derives minimum coverage and observed usage groups. Otherwise
   those metrics explicitly report unavailable evidence.
5. The model classifies exposed extension responsibilities; MCP counts independent,
   non-excepted behavior and applies the agreed ISP-4 SEVERE threshold of one.
6. The existing whole-rule exception step and result publication retain the
   measured metrics and explicit unavailable siblings in one auditable result.

The shared authoring contract adds optional `unavailable_reason` to a guarded
metric. A skipped metric with that declaration becomes an `unavailable_metrics`
entry containing metric/observation identity, `status: unavailable`, and
reasoning/condition evidence. It has no numeric value or severity. Ordinary skips
without that declaration remain ordinary skips. An all-unavailable result has
null severity; known measured SEVERE siblings remain SEVERE. Snapshots,
co-located metric expansion, effective scoring policy, and replay preserve the
declaration and outcome. Missing/invalid submissions and operation failures are
not evidence-unavailable outcomes.

Verified integration cases use the real bundled rule:

- **Given** two exposed extension members in an aggregate wrapper, **when** both
  classifications arrive in one combined submission, **then** MCP records width
  six and two independent responsibilities, with ISP-4 SEVERE, and executes
  discovery/member collection only once.
- **Given** partial or invalid classifications, **when** pending work is corrected,
  **then** accepted siblings remain recorded and scoring waits for valid work.
- **Given** persisted source operations and subsequently deleted source files,
  **when** execution resumes, **then** it finishes from persisted source evidence.
- **Given** a first interface with no discovered conformer, **when** it finalizes,
  **then** width stays measured and ISP-2/ISP-3 are unavailable, not fabricated
  compliant measurements.
- **Given** measured width ten and unverifiable extension behavior, **when** the
  result is published, **then** ISP-1 remains SEVERE and ISP-4 is unavailable.
- **Given** an empty interface or only private extension helpers, **when** the
  rule executes, **then** empty fan-out and filtered fan-out both complete without
  requesting nonexistent member judgments or misclassifying known width.
- **Given** an ordinary conditional skip without an unavailable declaration,
  **when** results finalize, **then** no unavailable metric is invented.

Current non-live validation: **2,695 passed, four existing abstract-base skips,
and 175 subtests**, including script and Apple-build tests. The flow-engine slice
contains **893 passing tests**. A standalone health-input test also now initializes
its required gate-module path itself instead of depending on test collection
order. Live ISP expectations retain canonical values 10 / 0.5 / 2 and add ISP-4
zero for the fixture without exposed extensions. Both locked live ISP checks
passed: **two tests in 144.77 seconds**, using Codex `gpt-5.6-terra` and Claude
`claude-opus-4-5`. They execute `solid-review`, enable only ISP through project
policy, and preserve the real bundled rule's events and final metrics. Codex
recorded one successful start and five successful continuation calls, with no
failed or unanswered tool calls. Retained evidence under
`.solid-coder/.artifacts/test/`:

- Codex: `codex/e2e/review/isp/20261016T181857Z-f2749473/`.
- Claude: `claude/e2e/review/isp/20261016T181957Z-34fc4cda/`.

Remaining boundary: context-dependent gate handling for unavailable metrics is
not introduced here. A first-interface warning policy still needs explicit
context/policy binding; absence of search hits alone is not proof of that context.
Bounded syntax relationships are not compiler-verified conformance, and model
reasoning/evidence remains auditable classification, not independently proven
truth. Complete-requirement classification is requested by the output contract
and prompt; exact identity-set enforcement for every submitted requirement remains
follow-up work, distinct from required workflow-instance completion.
