---
number: SPEC-040
feature: source-mcp-namespace
type: subtask
status: draft
parent: SPEC-010
blocked-by: []
blocking: [SPEC-039]
---

# Source MCP Namespace and Typed Code Analysis

## Description

Add a dedicated `source` MCP namespace for deterministic source-code and working-tree analysis. It supplies general capabilities used by review, gate-on-write, refactor, test, and client-authored workflows without placing review-specific behavior in the flow engine.

The namespace collects Git changes and analyzes one file or text buffer into typed source units plus auditable technology detections. The same application services are registered as internal workflow operations, allowing YAML to use stable names such as `source.analyze` without embedding generated MCP transport names or executable paths.

This work extracts useful behavior from the legacy pipeline `prepare_review_input` path. It does not preserve a second implementation or leave the legacy tool registered after its callers migrate.

## Input / Output

| | Detail |
|---|---|
| Input | Current project working tree, one accessible source file, or one supplied text buffer; optional validated project source-detector configuration |
| Output | Typed ordered change records or a typed source analysis containing language, units, technology/capability detections, normalized tags, and source evidence |
| Consumers | Flow-engine operation steps, SPEC-039 rule activation, `solid-review`, `solid-gate-on-write`, `solid-refactor`, tests, and client workflows |

## User Stories

### US-1: Use a dedicated source namespace

As an agent or workflow, I want source analysis separated from pipeline and flow lifecycle tools so its purpose and contracts are stable and reusable.

**Acceptance Criteria:**

- The plugin registers one MCP server named `source`; it does not repeat the plugin name in the server name.
- The server entrypoint lives beneath `mcp-server/source/` and is exposed by both Codex and Claude plugin manifests.
- The initial model-facing tools are `collect_changes` and `analyze`.
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

- `source.analyze` accepts exactly one typed source variant: an accessible file path or text with an optional virtual path and language hint.
- File and text variants produce the same typed analysis shape.
- The analysis records the detected language and ordered top-level source units with stable identity, name, declaration kind, and inclusive line span.
- Unit extraction is adapter-based by language. Unsupported languages return an explicit unsupported or whole-file analysis decision rather than guessed declarations.
- The first required language adapter is Swift.
- Swift unit extraction covers classes, structs, enums, protocols, actors, extensions, and top-level functions without depending on brittle line-oriented regular expressions.
- The source text is parsed once per analysis request and shared by unit extraction and technology detectors.
- Malformed or partially edited source returns recoverable typed parse diagnostics and every unit that can be identified safely; it never invents missing spans.

### US-4: Detect stacks and capabilities with evidence

As a workflow, I want MCP-owned technology detections so applicability tags are repeatable and auditable.

**Acceptance Criteria:**

- Detections have a typed category: language, framework, capability, or unit trait.
- Built-in Swift detections include `swift`, `swiftui`, `uikit`, `tca`, `concurrency`, and `gcd`.
- Built-in unit traits include at least `view`, `reducer`, `actor`, `extension`, `protocol`, and `test` where supported by parsed source evidence.
- Framework evidence may include an exact import plus relevant parsed symbols or conformances. Capability evidence may include parsed language constructs, calls, types, conformances, or attributes.
- Every detection records its normalized lowercase tag, detector identity, scope, and one or more source evidence records with line identity and the matched parsed fact.
- File-scoped detections such as language and imports may be inherited by contained units. Unit-scoped traits apply only to the unit that supplied their evidence.
- A rule requiring multiple tags matches only a unit containing every required normalized tag.
- Model output and caller-provided arbitrary strings cannot add, remove, or override detected tags.
- Detection order is deterministic and duplicate tag/evidence records are coalesced without losing provenance.

### US-5: Configure additional project technologies safely

As a client, I want to register project-specific technology signals without replacing bundled detectors or writing source-analysis code.

**Acceptance Criteria:**

- Optional project configuration is loaded from the existing `.solid-coder/config.toml` under a typed `[source]` section.
- Bundled detector identities cannot be replaced by project configuration; collisions fail with the config path and detector identity.
- Project detectors declare a normalized tag, category, supported language, and structured exact signals such as imports, identifiers, conformances, calls, types, or attributes.
- Arbitrary regular expressions, shell commands, scripts, and model prompts are not accepted as detector configuration.
- Invalid categories, duplicate tags, unknown languages, empty signal groups, and unsupported signal kinds fail configuration before analysis starts.
- Rule planning rejects required applicability tags that have no registered detector rather than silently making their rules permanently inapplicable.
- The effective detector catalog and project configuration hash are persisted with a consuming flow run so replay does not consult changed configuration.

Example project extension:

```toml
[[source.detectors]]
id = "acme-ui"
tag = "acmeui"
category = "framework"
language = "swift"
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

- A sealed file-or-text analysis source.
- A change-set model with ordered typed file changes and line ranges.
- A source analysis with language, parse diagnostics, units, and detections.
- A source unit with stable identity, declaration kind, name, and line span.
- A technology detection with category, normalized tag, scope, detector identity, and evidence.
- A source evidence record identifying the parsed fact and source span.
- A typed detector catalog and project detector declarations.

Models must not drag unrelated optional fields across source variants. File and text inputs are distinct variants under one discriminated boundary.

### Detection and rule activation

Source detection establishes facts; SPEC-039 owns review policy, rule enablement, and rule-instance materialization. The integration is:

```text
source.collect_changes
        ↓
flow-engine for_each changed file
        ↓
source.analyze
        ↓
flow-engine for_each normalized unit
        ↓
SPEC-039 selects policy-enabled rules whose required tags all match
```

The source namespace does not discover or execute rule workflows. It publishes typed evidence that other domains consume.

### Audit and replay

- Direct MCP calls return typed JSON responses and do not mutate source files.
- When invoked as an operation step, normalized inputs, detector-catalog identity/hash, outputs, and failures are recorded through the flow engine's event/snapshot contracts.
- Replay reconstructs completed operation outputs from persisted run evidence and does not rerun Git or source analysis.
- Configuration or source changes after operation completion affect new runs only.
- Raw source content is not duplicated into every event; persisted snapshots retain the minimum canonical input needed by the owning run contract.

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

- File and equivalent text inputs produce equivalent unit and detection results.
- Swift fixtures identify all required declaration kinds and safe spans, including partially edited source.
- Fixtures detect SwiftUI, UIKit, TCA, structured concurrency, and GCD with exact evidence.
- A mixed Swift file demonstrates inherited file tags and unit-only traits without tagging unrelated units as views or reducers.
- A configured project detector adds a new tag; collision, regex, script, and malformed detector declarations fail before analysis.
- Unknown rule tags fail plan preparation rather than silently skipping forever.

### Workflow integration

- A workflow loads `source.collect_changes` and `source.analyze` by logical operation name.
- The engine rejects transport-qualified MCP names and unknown logical operations.
- A `for_each` operation step analyzes multiple files, drains internally, publishes outputs in source order, and returns only downstream agent work.
- Replay uses persisted operation outputs and does not recollect Git changes or reparse source.
- Codex and Claude run the same workflow YAML without backend-specific tool names.

## Definition of Done

- [ ] The `source` MCP namespace is registered for Codex and Claude with typed `collect_changes` and `analyze` tools.
- [ ] Git changes are collected deterministically without mutation.
- [ ] File/text analysis produces typed units, technologies, normalized tags, and evidence.
- [ ] Built-in Swift detection covers SwiftUI, UIKit, TCA, structured concurrency, and GCD.
- [ ] Typed `[source]` configuration supports safe additional detectors and rejects bundled collisions or executable/regex definitions.
- [ ] Workflows invoke source services through internal logical operation names without MCP loopback or full transport paths.
- [ ] Operation steps support validation, conditions, fan-out, retries, audit, and replay through the existing engine.
- [ ] SPEC-039 receives per-unit tags and evidence for deterministic rule applicability.
- [ ] The legacy pipeline `prepare_review_input` registration and duplicate implementation are removed after migration.
- [ ] Focused, full non-live, and Codex/Claude flow-engine E2E tests pass.
