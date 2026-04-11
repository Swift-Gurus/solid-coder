---
name: plan
description: Architecture decomposition — reads a feature spec and produces a high-level component breakdown with protocols, wiring, and composition root.
argument-hint: <spec> --output <output-path>
allowed-tools: Read, Glob, Write, Bash, Skill
user-invocable: true
---

# Architecture Decomposition

Reads a feature spec (prompt string or markdown file) and produces `arch.json` — a high-level architecture decomposition of components, protocols, wiring, and composition root. Designs the ideal solution from the spec alone — no codebase reconciliation.

## Input

- SPEC: $ARGUMENTS[0] — a prompt string OR a filepath to a markdown spec file. If a filepath is provided (ends in `.md`), read the file. Otherwise use the string directly.
- OUTPUT_PATH: value after `--output` flag — filepath where `arch.json` will be written (e.g., `./arch.json`). Parent directories are created automatically.
- RULES_PATH: ${CLAUDE_PLUGIN_ROOT}/references

## Phase 1: Parse Spec & Load Context

- [ ] 1.1 Determine if SPEC is a filepath or prompt string
  - If filepath (ends in `.md` and file exists) → read the file contents
  - Otherwise → use the string as-is

- [ ] 1.2 **Load ancestors and dependencies** (only if SPEC is a filepath with frontmatter containing a `parent` or `blocked-by` field):
  - Use skill **solid-coder:parse-frontmatter** on the spec file to extract `number` and `blocked-by`
  - Use skill **solid-coder:find-spec** with `ancestors <current-SPEC-NNN> --blocked`. The script walks up from the current spec to root (ancestor chain) and appends blocked-by specs. Read each file in the returned `path` fields. Hold all content as context — ancestors provide scope, blocked-by specs provide components and patterns to reference.
  - After loading ancestor/blocked-by spec files, run the search script for each spec number in the ancestor/blocked-by chain:
    ```
    python3 ${CLAUDE_PLUGIN_ROOT}/skills/validate-plan/scripts/search-codebase.py --sources . --spec <SPEC-NNN>
    ```
    Each match is a type already created for that spec. Read the matched files' full source and frontmatter (`solid-name`, `solid-category`, `solid-description`) to understand what exists. For each matched type, verify whether it satisfies the current spec's requirements (user stories, acceptance criteria, technical requirements). If it fully satisfies a requirement → reference it as a dependency, do not redesign it. If it partially satisfies → reference it and note what gaps remain so validate-plan can classify it as `adjust`. If it does not satisfy → design a new component.
  - Ancestor and blocked-by context provides knowledge of what was built by prior specs — components, capabilities, and patterns that already exist. Reference these in the architecture rather than proposing duplicates.
     For example, if a blocked-by spec built a reusable view component, the plan should reference that component as a dependency, not design a new one

- [ ] 1.2.5 **Extract architectural constraints from loaded context** — From any CLAUDE.md instructions already in context, identify and hold as hard constraints:
  - **Available packages / modules** — local packages, libraries, or shared modules the project provides. Use these as dependencies rather than re-implementing them.
  - **Required patterns** — architectural patterns the project enforces (e.g., coordinator pattern, specific DI approach, mandatory base classes).
  - **Forbidden approaches** — things explicitly prohibited (e.g., "do not use singletons", "no direct URLSession usage").
  - **Test infrastructure** — test frameworks, helpers, or base classes that all tests must use.
  These override free architectural choices during decomposition.

- [ ] 1.3 Extract from the spec:
  - **User stories / features** — what the user can do
  - **Data models** — nouns/entities mentioned
  - **Behaviors** — actions, transformations, side effects
  - **Requirements** — flows, constraints
  - **Technical Requirements** — APIs, libraries, patterns, constraints (if present)
  - **Definition of Done** — the authoritative "done means done" checklist. Can contain both verification checks and code artifact requirements.

- [ ] 1.4 **Extract carry-forward fields** (verbatim, not summarized):
  - **Acceptance criteria** — from each user story, extract the story text and its criteria list. Store as `acceptance_criteria[]` array of `{story, criteria[]}` objects. Then extract all Definition of Done items and append as an additional entry: `{story: "Definition of Done", criteria: [<each DoD item verbatim>]}`. This ensures DoD items flow through the pipeline alongside user story criteria.
  - **Design references** — collected from two sources:
    1. **Spec content** — from `## UI / Mockup` section: if ASCII mockup exists, store as `{type: "inline", content: <markdown>, label: <description>}`. From `## Diagrams` section: store Mermaid diagrams as `{type: "inline", content: <mermaid>, label: <description>}`.
    2. **Resources directory** — if the spec is a filepath, check for a sibling `resources/` directory (same parent as the spec file). If it exists, Glob all files inside it and add each as `{type: "file", content: <absolute-path>, label: <filename>}`. These may include screenshots, mockups, JSON schemas, or other reference materials that the code agent should read before writing code.
  - **Technical requirements** — from `## Technical Requirements` section (if present): extract each subsection as a `{section, content}` object. `section` is the subsection heading (e.g., "Package Structure", "Type Definitions"). `content` is the full markdown including code blocks — verbatim, not summarized. Store as `technical_requirements[]`.
  - **Test plan** — from `## Test Plan` section: extract test cases and classify by type. Store as `test_plan[]` array of `{type, description, given, when, expect, component}` objects:
    - `type`: `"unit"` | `"ui"` | `"integration"` — inferred from prefix ("Unit test:", "UI test:") or section grouping
    - `description`: the test case verbatim (e.g., "WindowManager dedup logic — opening same project path twice returns the same window")
    - `given`: preconditions — what state exists before the action (e.g., "WindowManager has one tracked project at /path/to/project")
    - `when`: action — what is performed (e.g., "open the same project URL again")
    - `expect`: expected outcome (e.g., "existing window is brought to front, no new window created, tracked count remains 1")
    - `component`: name of the component this test targets (e.g., "WindowManager"). Set to `null` if the test spans multiple components.
    If the spec provides given/when/expect explicitly, use them verbatim. If the spec only has a description, decompose it into given/when/expect.
    Non-test DoD items (e.g., "Visual design matches reference screenshots", "Services remain alive") stay in `acceptance_criteria` as before. Only items that describe specific test cases to implement go into `test_plan`.

- [ ] 1.5 **Extract mode** — if the spec frontmatter contains a `mode` field (e.g., `mode: rewrite`), store it. Otherwise default to `"default"`. This is passed through to arch.json unchanged.
- [ ] 1.5.1 **Extract spec_number** — if the spec frontmatter contains a `number` field (e.g., `SPEC-016`), store it as `spec_number`. Otherwise leave empty. This is carried through the pipeline so created types can be tagged with `solid-spec` frontmatter.

- [ ] 1.6 Write a one-line `spec_summary` of what's being built

## Phase 2: Decompose into Components

For each identified behavior or capability, define a component. Respect acceptance criteria and technical requirements — if a criterion says "uses coordinator pattern" or "prefer value types", or a technical requirement specifies API signatures, type definitions, or patterns, the decomposition must follow them.

- [ ] 2.1 Use skill **solid-coder:create-type** skill for naming conventions and solid-category vocabulary - Don't create files
- [ ] 2.2 Identify all types needed — services, ViewModels, views, data models, protocols, unit tests, UI tests
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

- [ ] 3.1 **Derive matched tags from components** — collect all unique `category` and `stack` values across all components. Both are tags directly (e.g., `unit-test`, `screen`, `swiftui`, `combine`). Deduplicate.
- [ ] 3.2 **Discover active principles** — use skill **solid-coder:discover-principles** to discover active principles with `--refs-root {RULES_PATH}` and `--matched-tags <comma-separated tags from 3.1>`. If no tags derived, omit `--matched-tags` to get only always-active (tagless) principles.
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
  - `spec_number` — from Phase 1.5.1 (e.g., `"SPEC-016"`, or omit if not available)
  - `mode` — from Phase 1.5 (`"default"` or `"rewrite"`)
  - `spec_summary`, `components`, `wiring`, `composition_root` (existing)
  - `acceptance_criteria[]` — verbatim from Phase 1.4
  - `design_references[]` — from Phase 1.4 (inline mockups, diagrams, resource paths)
  - `technical_requirements[]` — verbatim from Phase 1.4 (subsections with code blocks preserved)
  - `test_plan[]` — from Phase 1.4 (test cases classified by type, associated with components where possible)
- [ ] 5.2 Validate by running:
  ```
  python3 ${CLAUDE_PLUGIN_ROOT}/skills/plan/scripts/validate-arch.py <OUTPUT_PATH> --schema ${CLAUDE_PLUGIN_ROOT}/skills/plan/arch.schema.json
  ```
  If the script exits non-zero, fix the arch.json and re-run before proceeding.

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
