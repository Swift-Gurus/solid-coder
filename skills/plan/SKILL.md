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

## Phase 1: Parse Spec & Load Context

- [ ] 1.1 Determine if SPEC is a filepath or prompt string
  - If filepath (ends in `.md` and file exists) → read the file contents
  - Otherwise → use the string as-is

- [ ] 1.2 **Load ancestors** (only if SPEC is a filepath with frontmatter containing a `parent` field):
  - Use skill **solid-coder:parse-frontmatter** on the spec file to extract `parent`
  - If `parent` exists (e.g., `SPEC-005`): use skill **solid-coder:find-spec** with `ancestors <parent-SPEC-NNN>`. Read each file in the returned `path` fields (root → leaf). Hold all content as ancestor context.
  - Ancestor context informs architectural decisions (scope boundaries, shared types, patterns established by parent features) but is NOT included in arch.json output.

- [ ] 1.3 Extract from the spec:
  - **User stories / features** — what the user can do
  - **Data models** — nouns/entities mentioned
  - **Behaviors** — actions, transformations, side effects
  - **Requirements** — flows, edge-cases
  - **Technical Requirements** — APIs, libraries, patterns, constraints (if present)
  - **Definition of Done** — the authoritative "done means done" checklist. Can contain both verification checks and code artifact requirements.

- [ ] 1.4 **Extract carry-forward fields** (verbatim, not summarized):
  - **Acceptance criteria** — from each user story, extract the story text and its criteria list. Store as `acceptance_criteria[]` array of `{story, criteria[]}` objects. Then extract all Definition of Done items and append as an additional entry: `{story: "Definition of Done", criteria: [<each DoD item verbatim>]}`. This ensures DoD items flow through the pipeline alongside user story criteria.
  - **Design references** — from `## UI / Mockup` section: if ASCII mockup exists, store as `{type: "inline", content: <markdown>, label: <description>}`. If `resources/` files are referenced, store as `{type: "file", content: <path>, label: <description>}`. From `## Diagrams` section: store Mermaid diagrams as `{type: "inline", content: <mermaid>, label: <description>}`.
  - **Design decisions** — from `## Design Decisions` section: extract each decision as a verbatim string. Store as `design_decisions[]` string array.
  - **Technical requirements** — from `## Technical Requirements` section (if present): extract each subsection as a `{section, content}` object. `section` is the subsection heading (e.g., "Package Structure", "Type Definitions"). `content` is the full markdown including code blocks — verbatim, not summarized. Store as `technical_requirements[]`.

- [ ] 1.5 Write a one-line `spec_summary` of what's being built

## Phase 2: Decompose into Components

For each identified behavior or capability, define a component. Respect `design_decisions[]` — if the spec prescribes a pattern (e.g., "use coordinator pattern", "prefer value types"), the decomposition must follow it.

- [ ] 2.1 Use skill **solid-coder:create-type** skill for naming conventions and solid-category vocabulary - Don't create files
- [ ] 2.2 Identify all types needed — services, ViewModels, views, data models, protocols
- [ ] 2.3 For each type (including data models), use skill **solid-coder:create-type** conventions to determine:
  - `name`
  - `category` — from `solid-category` vocabulary (see **solid-coder:create-type** SKILL.md Phase 3.2).
  - `stack` — from `solid-stack` vocabulary (see **solid-coder:create-type** SKILL.md Phase 3.3). Empty array `[]` if pure Swift with no framework dependencies.
  - `responsibility`
  - `interfaces` — empty array `[]` for data models
  - `dependencies` — empty array `[]` for data models
  - `produces` — empty array `[]` for data models
  - `fields` — populated for data models (`"name: Type"` strings), empty array `[]` for other types

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

## Phase 5: Output

- [ ] 5.1 Create structured output `arch.json` that corresponds to `${SKILL_DIR}/arch.schema.json`. Include:
  - `spec_summary`, `components`, `wiring`, `composition_root` (existing)
  - `acceptance_criteria[]` — verbatim from Phase 1.4
  - `design_references[]` — from Phase 1.4 (inline mockups, diagrams, resource paths)
  - `design_decisions[]` — verbatim from Phase 1.4
  - `technical_requirements[]` — verbatim from Phase 1.4 (subsections with code blocks preserved)
- [ ] 5.2 Validate:
  - Every component `dependencies[]` entry appears as some component's `interfaces[]` entry
  - Every wiring `to` matches an existing protocol in some component's `interfaces[]`
  - Every wiring `from` matches an existing component `name`
  - No concrete types in `dependencies[]` — only protocol names
  - All `category` values are from the solid-category vocabulary
  - All `stack` values are from the solid-stack vocabulary (see **solid-coder:create-type** Phase 3.3)
  - Data models (`category: "model"`) have populated `fields[]` and empty `interfaces[]`, `dependencies[]`, `produces[]`

- [ ] 5.3 Write `arch.json` to OUTPUT_PATH

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
