---
name: plan
description: Architecture decomposition — reads a feature spec and produces a high-level component breakdown with protocols, wiring, and composition root.
argument-hint: <spec> --output <output-path>
allowed-tools: Read, Glob, Write, Bash
user-invocable: true
---

# Architecture Decomposition

Reads a feature spec (prompt string or markdown file) and produces `arch.json` — a high-level architecture decomposition of components, protocols, wiring, and composition root. Designs the ideal solution from the spec alone — no codebase reconciliation.

## Input

- SPEC: $ARGUMENTS[0] — a prompt string OR a filepath to a markdown spec file. If a filepath is provided (ends in `.md`), read the file. Otherwise use the string directly.
- OUTPUT_PATH: value after `--output` flag — filepath where `arch.json` will be written (e.g., `./arch.json`). Parent directories are created automatically.

## Phase 1: Parse Spec

- [ ] 1.1 Determine if SPEC is a filepath or prompt string
  - If filepath (ends in `.md` and file exists) → read the file contents
  - Otherwise → use the string as-is
- [ ] 1.2 Extract from the spec:
  - **User stories / features** — what the user can do
  - **Data models** — nouns/entities mentioned
  - **Behaviors** — actions, transformations, side effects
  - **Requirements** - flows, edge-cases
  - **Definition of done** - check list to see if the arch will resolve them
- [ ] 1.3 Write a one-line `spec_summary` of what's being built

## Phase 2: Decompose into Components

For each identified behavior or capability, define a component.

- [ ] 2.1 Use skill **solid-coder:create-type** skill for naming conventions and solid-category vocabulary - Don't create files
- [ ] 2.2 Identify all types needed — services, ViewModels, views, models, protocols
- [ ] 2.3 For each component, use  skill **solid-coder:create-type** conventions to determine:
  - `name`
  - `category`
  - `stack` — from `solid-stack` vocabulary (see **solid-coder:create-type** SKILL.md Phase 3.3). Omit or use empty array `[]` if pure Swift with no framework dependencies.
  - `responsibility`
  - `interfaces`
  - `dependencies`
  - `produces`

## Phase 3: Load Principle Rules

Load principle rules as architectural constraints. Reuse existing skills for discovery and loading.

- [ ] 3.1 **Derive matched tags from components** — map component categories to tags for filtering:
  - `screen`, `view-component`, `modifier`, `viewmodel` → tag `swiftui`
  - (extend mapping as new framework principles are added)
- [ ] 3.2 **Discover active principles** — use skill **solid-coder:discover-principles** to discover active principles with `--refs-root references/` and `--matched-tags <comma-separated tags from 3.1>`. If no UI components, omit `--matched-tags` to get only always-active (tagless) principles.
- [ ] 3.3 **Load active principle rules** — use skill **solid-coder:load-reference** to load the `rule_path` from each `active_principles[]` entry.
- [ ] 3.4 **Apply loaded rules as constraints** — verify the decomposition from Phase 2 against the loaded principles. Adjust components if violations are found (e.g., a component with too many responsibilities per SRP, a sealed dependency per OCP, a fat protocol per ISP).

## Phase 4: Define Wiring

- [ ] 4.1 For each component that has `dependencies`, create a wiring entry:
  - `from` — the consumer component name
  - `to` — the protocol it depends on
  - `via` — injection method:
    - `init` — constructor injection (default for services, ViewModels)
    - `environment` — SwiftUI environment injection (for views consuming shared state)
    - `closure` — factory closures (for lazy/conditional creation)
- [ ] 4.2 Identify the **composition root** — the factory or assembly point where concrete types are created and injected. Name it `{Feature}Factory` or `{Feature}Assembly`.

## Phase 5: Define Data Models

- [ ] 5.1 For each data entity identified in Phase 1, create a data model entry:
  - `name` — the model name
  - `category` — always `model`
  - `fields` — list of fields as `"name: Type"` strings

## Phase 6: Output

- [ ] 6.1 Create structured output `arch.json` that corresponds to `${SKILL_DIR}/arch.schema.json`
- [ ] 6.2 Validate:
  - Every component `dependencies[]` entry appears as some component's `interfaces[]` entry
  - Every wiring `to` matches an existing protocol in some component's `interfaces[]`
  - Every wiring `from` matches an existing component `name`
  - No concrete types in `dependencies[]` — only protocol names
  - All `category` values are from the solid-category vocabulary
  - All `stack` values are from the solid-stack vocabulary (see **solid-coder:create-type** Phase 3.3)

- [ ] 6.3 Write `arch.json` to OUTPUT_PATH

## Edge Cases

- **EC-1**: Spec mentions UI but no data layer → still propose ViewModel + protocol boundary, even if the data source is TBD. Use a placeholder protocol (e.g., `DataProviding`) and note it.
- **EC-2**: Spec is a single sentence → produce minimal decomposition (may be just one component + one protocol).
- **EC-3**: Spec references external SDKs → list them as dependencies but do not design their internals. Use a wrapper protocol.

## Constraints

- This skill is a **black box** — it designs from the spec alone. Do NOT read the codebase or check for existing types.
- Do NOT generate implementation code — only the architecture decomposition.
- Do NOT add extra components "just in case" — only what the spec requires.
- Keep `responsibility` to one sentence per component.
- When in doubt about injection method, default to `init`.
