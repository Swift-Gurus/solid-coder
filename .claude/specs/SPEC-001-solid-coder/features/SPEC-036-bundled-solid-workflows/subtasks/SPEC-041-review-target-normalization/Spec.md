---
number: SPEC-041
feature: review-target-normalization
type: subtask
status: draft
parent: SPEC-036
blocked-by: [SPEC-035, SPEC-037, SPEC-040]
blocking: [SPEC-036, SPEC-039]
---

# Typed Review Target Normalization

## Description

Define one review-domain boundary that converts every supported review request into the same ordered, typed collection of files and units consumed by `solid-review`, `solid-gate-on-write`, `solid-refactor`, and executable rule workflows.

The boundary accepts current working-tree changes, one file, selected files, a folder, an immutable Git range, a resolved pull request, a prospective write buffer, or a pasted code block. Each request is a sealed Pydantic variant containing only fields meaningful to that source. Normalization composes the source services from SPEC-040; it does not duplicate Git parsing, file analysis, unit extraction, or tag detection.

Target interpretation is deterministic and MCP-owned. The model selects the target variant implied by the user's request but does not classify files, create units, assert tags, choose rules, or decide applicability.

## Input / Output

| | Detail |
|---|---|
| Input | One sealed review target plus the resolved project identity and optional request/session metadata |
| Output | An ordered normalized review input containing file identity, exact extension, selected ranges, typed units, MCP tags/evidence, target provenance, and immutable Git identities where applicable |
| Consumers | `solid-review`, `solid-gate-on-write`, `solid-refactor`, SPEC-039 rule materialization, direct review integrations, and tests |

## User Stories

### US-1: Select one explicit review target

As a caller, I want the requested review scope represented unambiguously so the engine never guesses between a path, source buffer, folder, or change set.

**Acceptance Criteria:**

- The target is a discriminated union of `working_tree`, `file`, `files`, `folder`, `git_range`, `pull_request`, `buffer`, and `code_block` variants.
- A variant contains no unrelated optional fields. File targets do not carry text; text targets do not masquerade as existing files.
- Mixed, unknown, or incomplete variants fail before source collection or any model call.
- Relative filesystem paths resolve from the canonical project root, and resolved paths cannot escape that root unless an explicit future external-file contract permits it.
- Target type, authored identity, canonical identity, and selection decisions are persisted before rule execution.

### US-2: Review current working-tree changes

As a developer, I want a default review request to cover my current staged, unstaged, and untracked work through the deterministic source collector.

**Acceptance Criteria:**

- `working_tree` delegates to `source.collect_changes` exactly once for a new run.
- Added, modified, deleted, and renamed records retain the SPEC-040 contract.
- Deleted files remain in audit evidence but produce no current-content review unit.
- Changed ranges select overlapping units; an untracked file selects every unit.
- An empty working tree completes with an empty normalized review input and no model session.

### US-3: Review files or a folder

As a developer, I want explicit file and folder requests normalized through the same analysis path as changed files.

**Acceptance Criteria:**

- `file` requires one readable file path.
- `files` requires a non-empty ordered list of unique readable file paths.
- `folder` recursively discovers readable files in stable project-relative path order.
- Folder traversal ignores version-control metadata, configured generated/vendor directories, and non-files according to typed source configuration; every exclusion is auditable.
- Explicit file targets are not silently removed by folder defaults. An explicitly requested unreadable, binary, or excluded file returns an actionable decision.
- Explicit file/files/folder requests select the complete content range of every accepted file.

### US-4: Review prospective writes and pasted code

As a gate or conversational caller, I want in-memory content reviewed without first writing it to the repository.

**Acceptance Criteria:**

- `buffer` requires prospective content and its target project-relative path. Gate-on-write always uses this variant.
- The target path supplies exact extension and file/path tag evidence while the supplied content is the only content analyzed.
- `code_block` requires content and may declare either a virtual path or an exact extension derived from an explicit fenced-code identity.
- A code block without virtual path or extension remains valid, produces an empty extension, and receives a whole-document unit.
- Text targets never create temporary repository files. Parser adapters may use engine-owned temporary storage that is removed after analysis.
- Equivalent file content and path-backed buffer content produce equivalent units and tags.

### US-5: Review an immutable Git range or pull request

As a developer, I want pull-request review to use immutable commits and the same normalized changed-file contract as local review.

**Acceptance Criteria:**

- `git_range` requires authored base and head refs and delegates to `source.collect_range`.
- Both refs resolve to commit hashes before diff collection; authored refs and resolved hashes are retained.
- `pull_request` carries provider/repository/request identity to an injected resolver that returns canonical project, base ref, head ref, and immutable commits.
- Provider resolution is outside the source namespace. Once resolved, pull-request normalization follows the `git_range` path without a second diff implementation.
- A local checkout with unavailable commits fails explicitly; the normalizer does not silently review the current working tree instead.
- Replay uses the persisted normalized input and resolved commit identities without contacting Git or the hosting provider again.

### US-6: Produce one normalized review collection

As a workflow, I want all target variants to converge before rule selection so downstream review behavior has one contract.

**Acceptance Criteria:**

- Every accepted current-content file is analyzed through `source.analyze`.
- The normalized file records canonical path or virtual identity, exact extension, selected ranges, file tags/evidence, and ordered units.
- Every unit records typed unit kind, span, content/reference required by review prompts, inherited file tags, unit tags, and tag evidence.
- Readable content without a registered parser produces one `document` unit rather than disappearing.
- Results preserve stable target order: authored order for `files`, canonical path order for folders and Git collections, and single identity for file/text targets.
- The normalizer neither discovers review rules nor applies policy. SPEC-039 consumes its result.

### US-7: Audit target preparation and replay

As a maintainer, I want to explain exactly what was reviewed and why files or units were omitted.

**Acceptance Criteria:**

- The run snapshots the authored target, canonical target resolution, normalized review input, source-operation outputs, detector catalog identity/hash, and relevant project configuration hash.
- Append-only events identify target resolution, file acceptance/exclusion, source analysis, selected ranges, unit creation, and preparation failure.
- Raw prospective buffer/code-block content is stored once in the canonical run snapshot and referenced from events rather than duplicated into every event.
- Resume/replay reads snapshots and events; it does not reread files, recollect Git state, re-resolve a pull request, or reanalyze completed inputs.
- Preparation failure cannot yield an allow result for gate-on-write.

## Technical Requirements

### Sealed target contract

Illustrative model-facing shapes are:

```yaml
target:
  kind: working_tree
```

```yaml
target:
  kind: file
  path: Sources/ProfileView.swift
```

```yaml
target:
  kind: files
  paths:
    - Sources/ProfileView.swift
    - Sources/ProfileStore.swift
```

```yaml
target:
  kind: folder
  path: Sources/Profile
```

```yaml
target:
  kind: buffer
  path: Sources/ProfileView.swift
  content: |
    struct ProfileView: View {
      var body: some View { Text("Profile") }
    }
```

```yaml
target:
  kind: code_block
  extension: .swift
  content: |
    final class ProfileStore {}
```

```yaml
target:
  kind: git_range
  base: origin/main
  head: HEAD
```

```yaml
target:
  kind: pull_request
  provider: github
  repository: Swift-Gurus/solid-coder
  number: 42
```

The exact Pydantic model names may follow repository conventions, but the variants and responsibilities are closed. Boundary JSON mappings decode immediately into these models; application logic does not pass dictionaries.

### Review operation boundary

Review normalization is a review-domain operation used internally by bundled workflows. It composes public source services but does not require an MCP loopback call. If exposed to agents, its tool accepts the same sealed target and returns the same typed normalized review input; it does not expose output directories or rule-selection controls.

### Relationship to workflow inputs

`solid-review` accepts one target and starts with normalization. `solid-gate-on-write` constructs a buffer target. `solid-refactor` accepts the same target and reuses its snapshotted normalized input for initial review, changes only the modified files during verification, and never translates back into the legacy `source_type` mapping.

## Connects To

| Direction | Target | Relationship |
|---|---|---|
| Parent | SPEC-036 Bundled SOLID Workflows | Supplies the shared input boundary for review, gate, and refactor |
| Upstream | SPEC-040 Source MCP Namespace | Supplies working-tree/range collection, file/text analysis, units, tags, and evidence |
| Upstream | SPEC-035 Workflow Packages | Supplies bundled and client workflow discovery after normalization |
| Downstream | SPEC-039 Executable Rule Workflows | Receives normalized files/units for policy and applicability matching |
| Replaces | `prepare-review-input` skill and pipeline tool | Removes model-authored target detection, tag matching, and duplicate JSON assembly |

## Test Plan

- Decode every target variant and reject mixed, unknown, missing, duplicate, escaping, and unreadable inputs.
- Normalize equivalent file and buffer inputs and assert identical extension, units, tags, and evidence.
- Normalize files and folders and assert ordering, deduplication, configured exclusions, and complete ranges.
- Normalize staged, unstaged, untracked, renamed, and deleted working-tree fixtures.
- Normalize a base/head range and an equivalent resolved pull request and assert identical change/unit results plus immutable commit audit.
- Normalize Markdown, YAML, unknown text, and unpathed code blocks into whole-document units.
- Assert gate buffer preparation never reads stale on-disk content and fails closed on invalid input.
- Replay every target variant after mutating files/refs/provider state and prove no external reread occurs.
- Run the same normalized target through Codex and Claude composite review workflows and assert backend-independent preparation artifacts.

## Definition of Done

- [ ] Every supported review request decodes into one sealed target variant.
- [ ] Working tree, file, files, folder, Git range, pull request, buffer, and code block normalize into one typed review collection.
- [ ] Exact extension, unit kind, tags, evidence, ranges, and provenance are retained without model classification.
- [ ] Unsupported readable content produces a whole-document unit.
- [ ] Gate-on-write uses the buffer variant and never reads stale target content.
- [ ] PR review resolves immutable commits and shares Git-range normalization.
- [ ] Snapshots/events make preparation replayable without filesystem, Git, provider, or parser re-execution.
- [ ] The legacy `prepare_review_input` skill/tool path is removed after all callers migrate.
- [ ] Focused, full non-live, and Codex/Claude review-flow tests pass.
