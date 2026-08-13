---
number: SPEC-035
feature: workflow-packages-and-discovery
type: subtask
status: ready
parent: SPEC-010
blocked-by: [SPEC-027, SPEC-030, SPEC-031]
blocking: [SPEC-036]
---

# Workflow Packages, Discovery, and Composition

## Description

Replace the public flat `harness/flows` layout with discoverable workflow packages. A package may live under any client-chosen category folder, carries its own prompts, schemas, step fragments, and private files, and declares a stable workflow ID that does not change when the package is moved. Client and plugin packages share one collision-checked catalog; neither source overrides the other. Workflows compose other workflows by ID while the existing relative-file include syntax and legacy flat flow locations remain supported during migration.

## Input / Output

| | Detail |
|---|---|
| Input | A workflow ID or explicit YAML path plus ordered project/plugin workflow roots |
| Output | One fully resolved and validated `FlowDef`, with package-relative resources and included workflows inlined before the run starts |
| Consumer | `flow_start`, bundled solid-coder workflows, and client-authored workflows |

## User Stories

### US-1: Organize workflows without changing their identity

As a client, I want to group workflow packages under folders such as `review`, `brainstorm`, `release`, and `test` without coupling callers to those folder names.

**Acceptance Criteria:**
- The public project root is `{project}/.solid-coder/workflows/`.
- Each package is a directory containing `workflow.yaml`; it may also contain `prompts/`, `schemas/`, `steps/`, and other package-private files.
- `workflow.yaml` declares a required stable `id` matching `^[a-z0-9]+(?:[-/][a-z0-9]+)*$`.
- Package discovery is recursive, so category-folder depth is not prescribed.
- Moving a package within the same workflow root does not change its ID or break `flow_start(<id>)` and workflow-to-workflow references.
- Duplicate IDs within one root fail discovery with an error naming every conflicting package; filesystem traversal order never decides the winner.

### US-2: Discover client and bundled workflows without overrides

As a client, I want my workflows and bundled workflows available through the same catalog without one silently replacing the other.

**Acceptance Criteria:**
- The package roots are `{project}/.solid-coder/workflows/` and `{plugin}/workflows/`.
- The compatibility roots are `{project}/.solid-coder/harness/flows/` and the plugin's existing harness flow directory.
- All package and compatibility roots contribute to one catalog; root order never selects a winner.
- A duplicate workflow ID across any client, bundled, or legacy source fails catalog construction with an error naming every conflicting source.
- Bundled public workflow IDs use the `solid-` prefix to minimize accidental collisions; the prefix does not grant override semantics.
- An explicit YAML path remains supported and bypasses catalog lookup.
- Legacy flat files retain their filename-derived IDs and must also be unique across the combined catalog.

### US-3: Reuse one workflow inside another

As a workflow author, I want to include a workflow by stable ID so reusable review, test, or release flows can be assembled into larger workflows.

**Acceptance Criteria:**
- A step-list entry may declare `include: { workflow: <id> }` plus the existing required `as` alias.
- Workflow-ID includes resolve through the same catalog and precedence rules as `flow_start`.
- Included steps keep the existing `<alias>.<step_id>` qualification, opaque group dependency, repeated-inclusion, and cycle-validation behavior from SPEC-027.
- Circular-reference errors report the workflow-ID chain, not only resolved filesystem paths.
- Existing `include: <relative-path>` remains supported for package-private subflows.
- Cross-package composition uses workflow IDs; it does not depend on `../` paths or basename-only lookup.

### US-4: Resolve package resources predictably

As a workflow author, I want prompts, schemas, fragments, and relative subflows to resolve from the package that declares them.

**Acceptance Criteria:**
- Explicit relative `prompt_file`, `schema_file`, `uses`, and path-based `include` references resolve relative to the declaring YAML file before any search-root fallback.
- A bare resource filename in a package resolves from its field-specific conventional subfolder: `prompts/`, `schemas/`, `steps/`, `subflows/`, or `scripts/`.
- `./` and `../` explicitly select declaring-file-relative resolution; `$package/` explicitly selects package-root-relative resolution.
- A nested include retains its own declaring-file base directory; the parent package directory is not incorrectly reused.
- `uses` preserves the declared relative path and no longer strips it to a basename.
- A resource cannot escape its package root through `..` or a symlink unless it was supplied as an explicit top-level flow path.
- Script files are explicitly declared by `type: script`, `file`, optional `executor`, and optional `args`; inline commands are explicitly declared by `type: command`, `command`, and optional `executor`.
- The persisted `workflow.yaml` snapshot is fully resolved, while its metadata records the selected package IDs and source files for diagnosis.

## Technical Requirements

### Package contract

`workflow.yaml` is the fixed package entrypoint filename; it is not the workflow's public name. The public name used by `flow_start` and cross-workflow includes comes from its `id` field.

```yaml
id: solid-review
name: Solid Review
description: Review normalized input against the bundled SOLID principles.
max_turns: 60
steps:
  - id: prepare
    prompt_file: prepare.md
    outputs:
      - name: review_input
        type: data
        schema_file: review-input.schema.json
```

- Required entrypoint fields are `id`, `name`, `max_turns`, and a non-empty `steps` list; `description` is recommended metadata.
- `id` is the stable machine-facing contract. `name` is a human-facing label and need not be unique.
- Exactly one `workflow.yaml` marks one package root. YAML files below its reserved subfolders are resources, not independently discovered public workflows.
- A simple workflow still uses `<package-folder>/workflow.yaml`. Existing single-file `<name>.yaml` flows are supported only through the legacy compatibility roots.

### Package subfolders

All subfolders are optional. They provide default locations for bare resource filenames; resources are loaded only when a workflow explicitly references them:

| Subfolder | Contract |
|---|---|
| `prompts/` | Default location for a bare `prompt_file` filename |
| `schemas/` | Default location for a bare `schema_file` filename |
| `steps/` | Default location for a bare `uses` filename |
| `subflows/` | Default location for a bare string `include` filename |
| `scripts/` | Default location for a bare `type: script` `file` filename |

Category folders above the package—such as `review/`, `brainstorm/`, `release/`, and `test/`—are client-defined organization and have no runtime semantics.

### Resource reference grammar

Package resource fields use one shared path grammar:

| Form | Meaning | Example |
|---|---|---|
| Bare filename | Resolve from the field's conventional package subfolder | `schema_file: findings.schema.json` → `<package>/schemas/findings.schema.json` |
| `./` or `../` | Resolve relative to the YAML file declaring the reference | `prompt_file: ../shared/review.md` |
| `$package/` | Resolve relative to the owning package root | `uses: $package/custom/prepare.yaml` |
| Existing unprefixed relative path | Preserve declaring-file-relative behavior for legacy workflows | `prompt_file: prompts/review.md` |

- When no package owns the declaring YAML file, a bare filename remains declaring-file-relative for legacy compatibility.
- Package-relative and declaring-file-relative references are normalized before containment validation.
- `..` traversal and symlinks may move within a package but may not resolve outside its root.
- Cross-package composition uses `include: { workflow: <id> }`; path-based includes remain package-private.
- Resource subfolders are not scanned for implicit steps, prompts, schemas, subflows, or scripts.
- A `workflow.yaml` below a package's reserved resource subfolders is a private resource, not a separately discoverable public package.

### Execution step grammar

Script files and inline commands are different step types.

Package script file:

```yaml
- id: validate
  type: script
  file: validate.py
  executor: python3
  args: [--strict]
```

- `file` is required and follows the package resource-reference grammar; a bare filename resolves from `scripts/`.
- `executor` is an optional non-empty string and defaults to `bash`.
- `args` is an optional list of strings and defaults to an empty list.
- The engine executes `[executor, resolved_file, *args]` without shell-string reconstruction.
- `command` is invalid on `type: script`.

Inline command:

```yaml
- id: status
  type: command
  command: "git status --short"
```

- `command` is required and is the complete command text.
- `executor` is an optional non-empty string and defaults to `bash`.
- The engine executes `[executor, "-lc", command]`; the command text remains one argument and is not split into an engine-generated argument list.
- `file` and `args` are invalid on `type: command`.

Both forms validate `executor` through the flow-engine permitted-executable allowlist. Runtime execution is represented by typed script-file and command models after YAML parsing; raw dictionaries and positional tuples are not execution-layer contracts.

For migration, the existing `type: script` plus command-array form remains accepted for legacy workflows. It cannot be mixed with `file`, `args`, or scalar `command`, and new packaged workflows use the structured forms above.

### Client layout

```text
{project}/.solid-coder/workflows/
  review/
    api-review/
      workflow.yaml          # id: api-review
      prompts/
      schemas/
      steps/
      subflows/
      scripts/
  brainstorm/
  release/
  test/
```

### Bundled layout

```text
{plugin}/workflows/
  review/solid-review/workflow.yaml
  gates/solid-gate-on-write/workflow.yaml
  refactor/solid-refactor/workflow.yaml
  internal/...
```

- Workflow discovery and selection belong to a catalog/resolver abstraction; the DAG runner must remain unaware of package roots and precedence.
- The catalog is built once per start operation and indexes only `workflow.yaml` files below package roots plus direct YAML files in legacy roots.
- Workflow IDs are the public API. Category directory names are presentation and ownership structure only.
- Workflow IDs are globally unique within the combined client/plugin catalog. This spec provides neither replacement nor merging for duplicate IDs.
- Existing `flow_start` and `flow_next` wire contracts remain compatible; only accepted flow identifiers and snapshot provenance expand.
- This collision-checked catalog supersedes SPEC-010/SPEC-030/SPEC-031's original flat, basename-based first-match resolution once package discovery is enabled.

## Connects To

| Direction | Target | Relationship |
|---|---|---|
| Upstream | SPEC-030 Core Flow Engine | Loads and validates the selected workflow definition |
| Upstream | SPEC-027 Flow Engine Extensions | Reuses aliased include semantics and file-backed prompts |
| Upstream | SPEC-031 Flow Harness MCP Tools | `flow_start` is the public ID-based entry point |
| Downstream | SPEC-036 Bundled SOLID Workflows | Supplies distribution, collision protection, and composition semantics |

## Test Plan

- Discover packages at multiple category depths and start each by declared ID.
- Move a package between category folders and prove its ID-based caller still resolves it.
- Reject duplicate IDs within one root with deterministic conflict details.
- Discover unique project-package, project-legacy, plugin-package, and plugin-legacy IDs in one catalog.
- Reject duplicate IDs across project/plugin and package/legacy boundaries; prove root ordering never hides the collision.
- Prove an explicit file path bypasses catalog selection.
- Include the same workflow twice under distinct aliases and complete both groups.
- Reject a direct and transitive workflow-ID include cycle with the ID chain in the error.
- Resolve nested prompts, schemas, fragments, and relative subflows from their declaring files.
- Resolve bare prompt, schema, fragment, subflow, and script filenames from their conventional package subfolders.
- Resolve explicit `./`, `../`, and `$package/` references according to the shared resource grammar.
- Reject package-resource traversal outside the package root.
- Reject symlink-based package-resource escape.
- Parse and execute structured script-file steps with default and explicit executors.
- Parse and execute inline command steps with the default `bash` executor and an explicit executor override.
- Reject mixed or malformed script/command declarations while retaining legacy command-array compatibility.
- Load and run every existing legacy harness flow unchanged.
- Live-test a bare workflow ID from both Claude and Codex project sessions.

## Definition of Done

- [ ] Recursive package discovery and stable IDs are implemented.
- [ ] Client, bundled, and legacy sources share one collision-checked catalog with no override behavior.
- [ ] Workflow-ID composition reuses SPEC-027 alias and cycle semantics.
- [ ] Package-relative resources resolve from their declaring file and remain package-contained.
- [ ] Bare resource filenames resolve from conventional package subfolders, and explicit path forms follow the shared grammar.
- [ ] Script-file and inline-command steps use distinct structured contracts with typed runtime models and allowlisted executors.
- [ ] Run snapshots record selected workflow provenance.
- [ ] Existing legacy flow suites remain green and Claude/Codex bare-ID live tests pass.
