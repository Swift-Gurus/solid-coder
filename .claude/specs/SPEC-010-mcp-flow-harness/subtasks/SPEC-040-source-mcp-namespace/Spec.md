---
number: SPEC-040
feature: source-mcp-namespace
type: subtask
status: in-progress
parent: SPEC-010
blocked-by: []
blocking: [SPEC-039]
---

# Source MCP Namespace and Typed Code Analysis

## Implementation Progress

Completed:

- Internal `source.collect_changes` and `source.analyze` operations use typed Pydantic inputs and outputs.
- Working-tree collection distinguishes added, modified, deleted, and renamed files and reports destination-coordinate changed ranges.
- File and in-memory text sources are sealed input variants.
- Swift analysis uses parser output rather than line-oriented declaration regular expressions and returns typed units plus recoverable diagnostics.
- Engine-owned `type: operation` steps resolve logical operation names, validate inputs/outputs, drain without a model turn, and participate in fan-out, conditions, retries, events, and replay.
- Internal `source.search` and `source.read_candidates` operations accept immutable typed Pydantic contracts, share repository traversal with legacy health search, preserve stable query/match provenance, exclude exact reviewed-unit identities, prefer complete proposed-source context over stale disk paths, validate candidate paths against the engine-owned canonical root, detect changed content through the shared SHA-256 capability, and persist bounded exact unit content plus candidate origin for replay.
- Focused source and workflow tests prove deterministic ranking, exact-unit exclusion, same-file sibling retention, prospective-buffer self-exclusion, `.solid-coder` artifact exclusion, exact bounded unit reads, escaped-root and changed-source outcomes, operation engine ownership, and replay without search or filesystem rereads.
- `source.prepare_search_targets` and `source.prepare_search_query` keep source slicing, target/query/unit identities, deterministic terms, exact self-exclusion, and query assembly MCP-owned.
- The bundled unit-scoped DRY workflow invokes one reusable target-search workflow for its normalized review unit. The model supplies only individual lexical semantic terms and independent per-candidate reuse and implementation-duplication decisions with reasoning and evidence; MCP expands identifier components, performs query assembly, searches sibling/external repository sources, and loads exact candidate units.
- Nested candidate fan-out preserves the parent target input and the inner candidate item, records conditional skips with their item evidence, publishes ordered target result envelopes, and emits an empty classification collection when every candidate is unavailable or ineligible.

Remaining:

- Produce exact file-extension identity and a whole-document unit for readable files or buffers without a registered parser.
- Implement MCP-owned tag detectors, unit tag inheritance, evidence, project detector configuration, and detector-catalog audit snapshots.
- Add immutable Git-range collection used by pull-request review.
- Register the public `source` MCP server and reuse the same application services as internal operations.
- Migrate callers from the legacy `prepare_review_input` tool and remove that duplicate path.

## Description

Add a dedicated `source` MCP namespace for deterministic source-code and working-tree analysis. It supplies general capabilities used by review, gate-on-write, refactor, test, and client-authored workflows without placing review-specific behavior in the flow engine.

The namespace collects Git changes or an immutable Git range, analyzes one file or text buffer into typed source units plus auditable tags, and searches project-owned source through typed queries whose candidates can be loaded for deterministic comparison. Exact file extension and typed unit kind remain first-class matcher inputs rather than being flattened into tags. The same application services are registered as internal workflow operations, allowing YAML to use stable names such as `source.analyze` without embedding generated MCP transport names or executable paths.

This work extracts useful behavior from the legacy pipeline `prepare_review_input` path. It does not preserve a second implementation or leave the legacy tool registered after its callers migrate.

## Input / Output

| | Detail |
|---|---|
| Input | Current project working tree, immutable base/head Git refs, one accessible file, one supplied text buffer with optional virtual path/extension, or typed repository-search queries and candidate identities; optional validated project tag-detector configuration |
| Output | Typed ordered change records, typed search candidates and bounded candidate sources, or a typed source analysis containing exact file extension, units, normalized tags, and source evidence |
| Consumers | Flow-engine operation steps, SPEC-039 rule activation, `solid-review`, `solid-gate-on-write`, `solid-refactor`, tests, and client workflows |

## User Stories

### US-1: Use a dedicated source namespace

As an agent or workflow, I want source analysis separated from pipeline and flow lifecycle tools so its purpose and contracts are stable and reusable.

**Acceptance Criteria:**

- The plugin registers one MCP server named `source`; it does not repeat the plugin name in the server name.
- The server entrypoint lives beneath `mcp-server/source/` and is exposed by both Codex and Claude plugin manifests.
- The initial model-facing tools are `collect_changes`, `collect_range`, `analyze`, `search`, and `read_candidates`.
- The namespace contains no review scoring, rule selection, flow lifecycle, build, or documentation operations.
- Application logic consumes and returns typed models. Raw mappings exist only at the MCP JSON boundary and are decoded immediately.
- Tool descriptions state that analysis is deterministic and MCP-owned; the model does not supply detected tags as facts.
- After migration, the pipeline server no longer registers `prepare_review_input`.

### US-2: Collect current Git changes

As a workflow, I want a deterministic collection of current changes so I can fan out over affected files without asking the model to parse Git output.

**Acceptance Criteria:**

- `source.collect_changes` reads staged, unstaged, and untracked changes from the resolved current project.
- Results distinguish added, modified, deleted, and renamed paths and retain old/new identity when Git provides both.
- Added-line ranges are computed in the destination file coordinate space and coalesced deterministically.
- Untracked files are represented as added files with their complete readable line range.
- Deleted files remain auditable change records but are not sent to current-source analysis unless historical content is explicitly supplied by a future contract.
- Files are returned in stable canonical project-relative path order.
- The operation is read-only and does not stage, restore, reset, or otherwise mutate Git state.
- Git failures return a typed failure with the project identity and command purpose; they do not silently produce an empty change set.

### US-3: Analyze a file or text buffer

As a workflow author, I want one deterministic source analysis operation so I can obtain units and technology signals without prompting an LLM.

**Acceptance Criteria:**

- `source.analyze` accepts exactly one typed source variant: an accessible file path or text with an optional virtual path or explicit file extension.
- File and text variants produce the same typed analysis shape.
- The analysis records the normalized exact file extension and ordered top-level source units with stable identity, name, declaration kind, and inclusive line span.
- Unit extraction adapters are selected internally by exact file extension. Workflow rule matching does not introduce a separate language dimension or language tag.
- The first required parser adapter handles `.swift`.
- Swift unit extraction covers classes, structs, enums, protocols, actors, extensions, and top-level functions without depending on brittle line-oriented regular expressions.
- The source text is parsed once per analysis request and shared by unit extraction and technology detectors.
- Malformed or partially edited source returns recoverable typed parse diagnostics and every unit that can be identified safely; it never invents missing spans.
- A readable file or buffer without a registered parser produces one typed `document` unit spanning its complete content. Unsupported extension never silently produces an empty unit collection.
- A buffer supplied by gate-on-write has a required virtual path. A pasted code block may supply a virtual path or explicit extension; when neither exists, the extension is empty and only rules without extension requirements are eligible.

### US-4: Detect review tags with evidence

As a workflow, I want MCP-owned tags so semantic applicability beyond file extension and unit kind is repeatable and auditable.

**Acceptance Criteria:**

- File extension and unit kind are emitted as dedicated typed fields and are never duplicated as tags.
- Built-in tags include `ui`, `swiftui`, `uikit`, `tca`, `concurrency`, `gcd`, `test`, `test-double`, `generated`, and `spec` where supported by exact path or parsed-source evidence.
- `view`, `reducer`, and similar semantic traits are tags; `class`, `struct`, `actor`, `protocol`, `extension`, `function`, and `document` are unit kinds.
- Tag evidence may include an exact path rule, import, parsed symbol, conformance, call, type, attribute, or structured file metadata.
- Every detection records its normalized lowercase tag, detector identity, scope, and one or more source evidence records with line identity and the matched parsed fact.
- File-scoped tags may be inherited by contained units. Unit-scoped tags apply only to the unit that supplied their evidence.
- Model output and caller-provided arbitrary strings cannot add, remove, or override detected tags.
- Detection order is deterministic and duplicate tag/evidence records are coalesced without losing provenance.

### US-5: Configure additional project technologies safely

As a client, I want to register project-specific technology signals without replacing bundled detectors or writing source-analysis code.

**Acceptance Criteria:**

- Optional project configuration is loaded from the existing `.solid-coder/config.toml` under a typed `[source]` section.
- Bundled detector identities cannot be replaced by project configuration; collisions fail with the config path and detector identity.
- Project detectors declare a normalized tag, supported file extensions, and structured exact signals such as paths, imports, identifiers, conformances, calls, types, or attributes.
- Arbitrary regular expressions, shell commands, scripts, and model prompts are not accepted as detector configuration.
- Duplicate tags, malformed extensions, empty signal groups, and unsupported signal kinds fail configuration before analysis starts.
- Rule planning rejects required applicability tags that have no registered detector rather than silently making their rules permanently inapplicable.
- The effective detector catalog and project configuration hash are persisted with a consuming flow run so replay does not consult changed configuration.

Example project extension:

```toml
[[source.detectors]]
id = "acme-ui"
tag = "acmeui"
file_extensions = [".swift"]
imports_any = ["AcmeUI"]
conformances_any = ["AcmeView"]
```

### US-6: Invoke source operations from workflows without MCP transport names

As a workflow author, I want to call source capabilities by stable logical name so workflows work unchanged in Codex, Claude, and internal execution.

**Acceptance Criteria:**

- The flow engine supports an engine-owned `type: operation` step.
- An operation step declares a namespaced logical operation such as `source.collect_changes` or `source.analyze`.
- Workflow YAML never contains generated names such as `mcp__plugin_solid-coder_source__analyze`, server executable paths, or JSON-RPC routing details.
- The engine resolves operation names through a typed internal registry and invokes the same application service used by the public MCP tool without making an MCP loopback call.
- Unknown and duplicate operation names fail workflow loading deterministically.
- Operation inputs are declared through `with` bindings and validated against the registered operation input model before execution.
- Operation outputs come from the registered typed output model and are available through ordinary `steps.<id>.outputs.<name>` expressions without duplicating their schemas in every workflow.
- Operation steps support `depends_on`, conditions, `for_each`, instance-scoped attempts, replay, and ordered fan-in through the existing engine machinery.
- Operation execution consumes no model turn and is drained before agent-owned work is returned.
- Start, completion, failure, retry, skip, and replay retain the normal step and instance identities.

Example:

```yaml
steps:
  - id: changes
    type: operation
    operation: source.collect_changes

  - id: analyze_files
    type: operation
    operation: source.analyze
    depends_on: [changes]
    for_each: "{{steps.changes.outputs.files}}"
    with:
      source: "{{item}}"
```

### US-7: Collect an immutable Git range

As a review workflow, I want a deterministic base/head diff so pull-request review uses the same typed file-change contract as working-tree review.

**Acceptance Criteria:**

- `source.collect_range` requires a project root, base ref, and head ref and resolves both refs to immutable commit identities before reading the diff.
- The result uses the same added, modified, deleted, renamed, changed-range, and stable-order contracts as `source.collect_changes`.
- The operation records authored refs and resolved commits so audit/replay never reinterpret a moved branch name.
- Missing, ambiguous, or non-commit refs fail explicitly before producing a change collection.
- Pull-request URL/number lookup is an adapter concern owned by the review-target boundary; source collection receives resolved repository/ref input and does not call a hosting provider.

### US-8: Search and load source candidates for comparison

As a unit-scoped rule workflow, I want MCP-owned repository search and candidate loading so the model can classify concrete reuse and duplication evidence without choosing paths or parsing formatted search output.

**Acceptance Criteria:**

- `source.search` accepts a typed ordered collection of queries. Every query has a stable identity and one or more normalized, non-empty search terms; raw query mappings are decoded at the MCP boundary and are not passed through application logic.
- Each search term is one explicit term, not a shell fragment, regular expression, or delimiter-encoded list. Duplicate terms within a query are rejected or normalized deterministically before search.
- The project root comes from the resolved run or MCP request context. A bundled workflow does not allow the model to substitute another search root.
- Search reuses the repository search service shared with existing health-check behavior, while the flow operation returns typed results and never writes or consumes a health-check completion marker.
- Search considers structured frontmatter plus exact filename, symbol, import, and source-content evidence. Every returned candidate identifies the originating query, canonical project-relative source identity, matched terms, match kinds, and stable rank/order.
- Exact reviewed-unit identities are derived from MCP-owned targets and removed before results are published. Sibling units in the same source remain eligible; an agent cannot author or widen exclusions.
- Candidate identities are deduplicated and ordered deterministically. Search limits are explicit typed inputs with bounded defaults rather than prompt conventions.
- `source.read_candidates` accepts typed candidate identities produced by search, verifies that every resolved path remains within the canonical project root, verifies the search-time file hash, and returns the exact bounded candidate-unit slice with canonical unit/source identity and truncation metadata.
- Missing, unreadable, escaped-root, oversized, or changed candidate sources produce typed per-candidate outcomes; they do not silently disappear or cause unrelated candidates to lose their results.
- Search results and loaded candidate sources are ordinary typed operation outputs. Completion events persist the effective queries, exclusions, provenance, source identities, bounded content, and failures required for audit and replay.
- Replay reconstructs both operation outputs from persisted run evidence and does not search the repository or reread candidate files.

### US-9: Prepare model-ready source-search tasks deterministically

As a workflow author, I want MCP to prepare immutable search targets and assemble validated queries so model steps provide only semantic synonyms and candidate classifications for code already present in their context.

**Acceptance Criteria:**

- `source.prepare_search_targets` accepts one typed file or text source plus a typed `file | unit` granularity and reuses `source.analyze`; it does not implement a second parser or source-discovery path.
- File granularity returns one target containing the complete supplied source. Unit granularity returns one target per ordered analyzed unit containing the exact source slice identified by its parser offsets.
- Every target carries an MCP-owned stable identity, canonical source identity, local unit identity, exact code, name, unit kind, source span, and deterministic name/symbol/tag terms.
- The model never discovers files, reads paths, chooses source spans, creates target/query identities, or reports detected tags. A model step receives the already-scoped target code and returns only a non-empty array of dynamically generated individual lexical synonyms or name components; delimiter-packed or compound identifier values are not the authored contract.
- `source.prepare_search_query` accepts one MCP-owned target and the corresponding model-generated term array. It validates single-term values, deterministically expands underscore and camel-case identifier components from both generated and target terms, normalizes and deduplicates the effective terms, preserves the target identity as the query identity, and derives the exact typed unit exclusion accepted by `source.search`.
- A unit-scoped rule invokes one nested search workflow for its normalized target. Candidate `for_each` identity and ordered fan-in associate every classification with that target without asking the model to echo an identity.
- The model selects promising candidates from the bounded `source.search` summaries. `source.validate_candidate_selection` rejects any identity that was not present in that exact search result and returns only the validated selections for classification fan-out.
- Each classification prompt supplies the immutable reviewed target, validated candidate identity, frontmatter description, and absolute source path. The model reads that path with its normal file-reading tool; MCP does not load candidate source into the prompt or classify unselected candidates.
- Each selected-candidate instance requires independent closed reuse (`EXACT | EXTENSIBLE | PARTIAL | NOT_SUITABLE`) and implementation-duplication (`IDENTICAL | STRUCTURAL | SIMILAR | NOT_DUPLICATE`) decisions with non-empty reasoning and source evidence. A conformer is not a reusable replacement for its protocol, and a protocol/conformer relationship without duplicated implementation is not duplication. Target and candidate identities come from engine-owned instance input rather than model output.
- Empty candidate collections complete through existing empty fan-in behavior and remain auditable through the persisted search output; the model is not asked to fabricate a no-candidate assessment.
- Step completion and nested fan-in persist generated terms, effective queries, shown candidates, validated selections, and classifications for downstream metrics and replay. Replay performs no source analysis, repository search, file read, or model call for completed instances.
- Prompt wording is replaceable workflow content. Stable correctness comes from typed MCP preparation, operation validation, instance association, output schemas, and persisted events rather than relying on a prompt to preserve identities or claim coverage.

## Technical Requirements

### Namespace boundary

```text
mcp-server/
└── source/
    ├── server.py
    ├── changes/
    ├── analysis/
    ├── detectors/
    └── config/
```

Folder organization may follow existing production/test mirroring conventions; these labels describe responsibilities rather than requiring one class per folder.

The public MCP adapter, internal operation adapter, and workflow consumers share the same typed application services. MCP registration is a transport concern and must not leak into source analysis or flow execution.

### Typed source contracts

The boundary models include, at minimum:

- A sealed file-or-text analysis source whose text variant carries virtual path or explicit extension identity without unrelated optionals on file input.
- A change-set model with ordered typed file changes and line ranges.
- A source analysis with exact file extension, parse diagnostics, units, and tag detections.
- A source unit with stable identity, typed declaration/document kind, name, line span, inherited file tags, and unit tags.
- A tag detection with normalized tag, scope, detector identity, and evidence.
- A source evidence record identifying the parsed fact and source span.
- A typed detector catalog and project detector declarations.
- A typed repository-search request containing stable query identities, normalized terms, exclusions, and bounded limits.
- Typed search candidates carrying project-relative source identity and match provenance, plus typed candidate-source read results carrying bounded content or a typed failure.

Models must not drag unrelated optional fields across source variants. File and text inputs are distinct variants under one discriminated boundary.

### Detection and rule activation

Source detection establishes facts; SPEC-039 owns review policy, rule enablement, and rule-instance materialization. The integration is:

```text
source.collect_changes or source.collect_range
        ↓
flow-engine for_each changed file
        ↓
source.analyze
        ↓
flow-engine for_each normalized unit
        ↓
SPEC-039 applies included/excluded file-extension, unit-kind, and tag matchers
```

The source namespace does not discover or execute rule workflows. It publishes typed evidence that other domains consume.

Unit-scoped rules may add repository comparison after analysis without changing that boundary:

```text
normalized review unit
        ↓
agent generates semantic synonyms from supplied target code
        ↓
source.prepare_search_query
        ↓
source.search typed queries, excluding only the reviewed unit
        ↓
source.read_candidates typed candidate identities
        ↓
flow-engine for_each loaded candidate
        ↓
agent classifies supplied target/candidate code
```

### Audit and replay

- Direct MCP calls return typed JSON responses and do not mutate source files.
- When invoked as an operation step, normalized inputs, detector-catalog identity/hash, outputs, and failures are recorded through the flow engine's event/snapshot contracts.
- Replay reconstructs completed operation outputs from persisted run evidence and does not rerun Git or source analysis.
- Configuration or source changes after operation completion affect new runs only.
- Raw source content is not duplicated into every event; persisted snapshots retain the minimum canonical input needed by the owning run contract.
- Candidate content is bounded once by `source.read_candidates` and persisted with that completed operation output, so downstream audit and replay observe the exact compared bytes without rereading the working tree.

## Connects To

| Direction | Target | Relationship |
|---|---|---|
| Parent | SPEC-010 MCP-Driven Flow Orchestration | Supplies operation-step lifecycle, replay, fan-out, conditions, and audit |
| Upstream | SPEC-037 Conditional Routing and Result Aggregation | Supplies conditions, typed `with` bindings, `for_each`, and ordered fan-in |
| Downstream | SPEC-039 Executable Rule Workflows and Review Policy | Consumes normalized units and detected tags for rule activation |
| Replaces | Pipeline `prepare_review_input` | Extracts useful change preparation and removes the broad legacy registration after migration |

## Test Plan

### Namespace and contracts

- Both plugin manifests register `source`, and the pipeline server does not retain `prepare_review_input` after migration.
- MCP JSON inputs decode immediately into the correct file or text source variant; mixed/unknown variants fail.
- Application services and the internal operation registry exchange typed models.

### Change collection

- A fixture repository containing staged, unstaged, untracked, deleted, and renamed files produces stable typed records and correct destination-coordinate ranges.
- Git failure is explicit and cannot look like an empty clean repository.
- Collection never mutates Git state.

### Source and technology analysis

- File and equivalent text inputs produce equivalent unit and tag results.
- Swift fixtures identify all required declaration kinds and safe spans, including partially edited source.
- Fixtures detect SwiftUI, UIKit, TCA, structured concurrency, and GCD with exact evidence.
- Markdown, YAML, JSON, unknown readable files, and unpathed buffers produce a deterministic whole-document unit rather than an empty collection.
- A mixed Swift file demonstrates inherited file tags and unit-only tags without tagging unrelated units as views or reducers.
- A configured project detector adds a new tag; collision, regex, script, and malformed detector declarations fail before analysis.
- Unknown rule tags fail plan preparation rather than silently skipping forever.
- Git-range fixtures resolve authored refs to commits and produce the same normalized change records as an equivalent working-tree diff.

### Repository search and candidate loading

- Multiple typed queries retain their query identities through stable candidate ordering and deduplication.
- Search proves exact filename, symbol/import, frontmatter, and source-content matches while rejecting regex, shell, empty-term, and escaped-root inputs.
- The exact reviewed unit is excluded without removing sibling units in the same source; absolute buffer identities and project-relative repository identities resolve to the same canonical source.
- Proposed sibling units and units from another file in the same multi-file patch replace stale repository snapshots, remain searchable before write authorization, and load their exact in-memory content with `proposed` provenance.
- Candidate loading rejects paths outside the canonical project root and returns typed outcomes for missing, unreadable, changed, oversized, and successfully loaded files.
- A DRY fixture containing only within-unit duplication still produces local evidence when search returns no candidates.
- Identifier tokenization expands compound deterministic or generated terms into searchable lexical components without discarding the original term.
- A temporary repository scenario containing a reviewed protocol and a conforming implementation is found through semantic terms; both Codex and Claude classify the conformer as `NOT_SUITABLE` for protocol reuse and `NOT_DUPLICATE` when it contains no duplicated implementation. MCP scores `DRY-1=0`, `DRY-2=0`, and `DRY-3=0` for that relationship.
- Replay returns the persisted candidates and exact bounded candidate content after repository files change, and the search/read services are not invoked again.

### Workflow integration

- A workflow loads `source.collect_changes`, `source.analyze`, `source.search`, and `source.read_candidates` by logical operation name.
- The engine rejects transport-qualified MCP names and unknown logical operations.
- A `for_each` operation step analyzes multiple files, drains internally, publishes outputs in source order, and returns only downstream agent work.
- Replay uses persisted operation outputs and does not recollect Git changes or reparse source.
- Codex and Claude run the same workflow YAML without backend-specific tool names.

## Definition of Done

- [ ] The `source` MCP namespace is registered for Codex and Claude with typed `collect_changes` and `analyze` tools.
- [ ] Git changes are collected deterministically without mutation.
- [x] Repository search and bounded candidate loading use typed inputs/outputs, stable provenance, self-exclusion, canonical-root validation, audit, and replay.
- [ ] File/text analysis produces exact extension, typed code/document units, normalized tags, and evidence.
- [ ] Built-in Swift detection covers SwiftUI, UIKit, TCA, structured concurrency, and GCD.
- [ ] Typed `[source]` configuration supports safe additional detectors and rejects bundled collisions or executable/regex definitions.
- [x] Workflows invoke source services through internal logical operation names without MCP loopback or full transport paths.
- [x] Operation steps support validation, conditions, fan-out, retries, audit, and replay through the existing engine.
- [ ] SPEC-039 receives file extension, unit kind, tags, and evidence for deterministic included/excluded rule applicability.
- [ ] The legacy pipeline `prepare_review_input` registration and duplicate implementation are removed after migration.
- [ ] Focused, full non-live, and Codex/Claude flow-engine E2E tests pass.
