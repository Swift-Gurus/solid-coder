---
name: build-spec-from-code
description: Analyze existing code and produce a rewrite spec with subtasks — extracts functionalities as user stories, builds integration map, interviews about target state.
argument-hint: <file-or-directory-path>
allowed-tools: Read, Grep, Glob, Write, Bash, Skill, AskUserQuestion
user-invocable: true
---

# build-spec-from-code — Code-to-Spec Generator
Analyzes existing code and produces a rewrite spec. Extracts functionalities as user stories with edge cases and acceptance criteria. For UI code: requests screenshots/designs, extracts colors, fonts, spacing. For non-UI code: captures API contracts, performance constraints, threading model. Builds an integration map of consumers, dependencies, and connection points.
## Execution Rules

- **Sub-skill returns are internal values** — when a skill invocation produces JSON output, capture it silently and proceed immediately. Do NOT present the result to the user or pause for confirmation.
- **Only pause for user input at explicit `AskUserQuestion` steps** — all other steps run to completion without stopping.

## Interview Rules

- Mark the inferred default with `[default]`.
- For choice questions, always include a free-text fallback as the last option (e.g. `other: <describe>`).

---

## Phase 0: Validate Input

- [ ] 0.1 Parse `$ARGUMENTS` — extract file paths or directory path. If no argument provided, fail with: "Usage: `/build-spec-from-code <file-or-directory-path>`"
- [ ] 0.2 Verify the path(s) exist. If directory, collect all source files within it (recursive). If the target has 50+ files, ask using AskUserQuestion: "This target has N files. Consider narrowing to a specific module or type. Continue anyway or provide a narrower path?"
- [ ] 0.3 Read all target files. Hold contents in context as `code_context`.

---

## Phase 1: Analyze Code

- [ ] 1.1 **Extract functionalities as user stories** — read the code and identify what it does (not how it's structured):
  - User-facing behaviors → `As a [user], I want [goal] so that [reason]`
  - System behaviors → `As the system, when [trigger], [outcome]`
  - For each story, derive acceptance criteria from observable code behavior
  - Extract edge cases (error paths, guard statements, fallbacks, boundary conditions) as acceptance criteria within the relevant stories

- [ ] 1.2 **Build integration map** — extract how the code connects to the rest of the codebase:
  - **Protocols it conforms to** — which protocols, where they're defined
  - **Protocols it exposes** — public APIs other code depends on
  - **Dependencies it consumes** — injected or constructed, concrete or abstract
  - **Consumers** — use Grep to find callers of public methods/types across the codebase. Record: who calls, via what mechanism (direct, protocol, environment)
  - **Integration points** — delegates, notifications, closures, environment values
  All this information will be used to connect the new rewritten component with the rest of the code.

- [ ] 1.3 **Generate diagrams** — treat the current component as a **black box**. The component is a single opaque node. Diagrams show ONLY what crosses the boundary.
  - [ ] 1.3.1 **Generate diagrams of the component** - abstract diagrams for the component as **black box**
    - **What to show**: abstraction it requires (what capability the component requires — described by purpose, not by type name)
    - **Dependencies as abstract needs**: name the capability the component needs, not the type that currently provides it. The rewrite decides concrete types — the spec captures what is needed, not how it was solved.
    - **Flow diagram**: Entry points → [Component] → Outputs. One box for the component, labeled arrows for what goes in and what comes out.
    - **Sequence diagram**: Consumer ↔ Component boundary only. Consumer calls component, component returns results/callbacks. No internal sequences between sub-components.
    - **Connection diagram**: Consumers on one side, abstract needs on the other, component in the middle.
    - **What to EXCLUDE**: internal types, internal method calls, internal architecture patterns, concrete dependency names, singletons, anything that happens inside the component.
    - Generate as Mermaid markdown.
  - [ ] 1.3.2 **Generate diagrams of the current state** — concrete diagrams showing how the code actually works today. These go into the **Current State** section and are used to build the bridge subtask.
    - **What to show**: actual type names, concrete dependencies, real call chains, singletons, internal architecture patterns — everything the bridge needs to know to wire old ↔ new.
    - **Flow diagram**: How data flows through the current implementation — which types create which, what calls what internally.
    - **Connection diagram**: Concrete dependency graph — actual type names, how they're obtained (injected, singleton, constructed), who consumes what.
    - **These are the opposite of 1.3.1** — 1.3.1 abstracts away the implementation for the rewrite spec. 1.3.2 documents it for the bridge.
    - Generate as Mermaid markdown.

- [ ] 1.4 **Detect mixed concerns** — if the code has multiple unrelated responsibilities, note them. These may become separate rewrite specs.

---

## Phase 2: Present Analysis

- [ ] 2.1 Present extracted user stories to the user. Ask using AskUserQuestion: "Here's what the code does. Confirm, adjust, or add stories?"

- [ ] 2.2 Present generated diagrams. Ask using AskUserQuestion: "Here's how the code works. Keep, revise, or describe what to change?"

- [ ] 2.3 Present integration map summary: "Found N consumers, M dependencies, K integration points." If mixed concerns detected, ask: "This code has multiple unrelated responsibilities. Should we create one rewrite spec or split into multiple?"

---

## Phase 3: Interview — Target State
- [ ] 3.1 **UI requirements** — if code includes UI elements, request design or screenshots for every UI element you need using AskUserQuestion.
    - You will move those into resources folder later.
- [ ] 3.2 **What to keep vs change** — ask using AskUserQuestion: "What should stay the same and what needs to change? Think about: behaviors to preserve, pain points to fix, patterns to adopt or drop." Free-text.

- [ ] 3.3 **Subtask decision** — if consumers were found in Phase 1.2, present them and ask using AskUserQuestion:
  ```
  Found N consumers of this code's public APIs:
  <list top consumers>

  Which subtasks do you need?
  1. Rebuild only (consumers handle their own migration)
  2. Rebuild + bridge (adapter between old and new interface)
  3. Rebuild + bridge + migrate consumers
  ```
  If no consumers found, default to rebuild only.

---

## Phase 4: Hierarchy Placement

- [ ] 4.1 **Where does it belong?** — use skill **solid-coder:find-spec** with `--status draft,ready --action Select as parent`. Returns selected spec. Store as `parent_spec` (or none if root).

- [ ] 4.2 "Give it a short title." — ask using AskUserQuestion free-text only. This becomes the `epic` slug.

- [ ] 4.3 Get next spec number — use skill **solid-coder:find-spec** with `next-number`. Store as `parent_number`.

---

## Phase 5: Generate Draft Specs

### 5.1 Parent Spec (Rewrite)

- **Frontmatter**: `number`, `feature`, `type: epic`, `status: draft`, `mode: rewrite`, `parent` (if non-root), `blocked-by: []`, `blocking: []`
- **Description**: what this rewrite achieves
- **Input / Output**: from interview answers
- **User Stories**: confirmed/adjusted stories from Phase 2.1 (these describe the TARGET behavior, carried forward from the existing code's functionalities)
- **Current State**: summary from Phase 1 — types, responsibilities, integration map. This is a snapshot, not the target.
- **Technical Requirements**: External/boundary constraints only — what the component must satisfy, not how the old code satisfied it. For UI code: colors, fonts, spacing, padding, links to design files/screenshots. For non-UI code: API contracts, performance constraints, threading model, platform requirements. Do NOT carry forward internal implementation details — capture the underlying need, not the concrete type that currently provides it.
- **Diagrams**: current state diagrams from Phase 1.3 + target state diagrams generated from interview answers
- **Connects To**: from integration map
- **Definition of Done**: verifiable checklist

### 5.2 Rebuild Feature (scaffold)

- **Frontmatter**: `number` (next from find-spec), `feature`, `type: feature`, `status: draft`, `mode: rewrite`, `parent: <parent_number>`, `blocked-by: []`, `blocking: []`


### 5.3 Bridge Feature (conditional, scaffold)

- **Frontmatter**: `number` (next from find-spec), `feature`, `type: feature`, `status: draft`, `parent: <parent_number>`, `blocked-by: [<rebuild_number>]`, `blocking: []`
- No `mode: rewrite` — runs normal `/implement` (validator finds both old and new types)

### 5.4 Migrate Feature (conditional, scaffold)

- **Frontmatter**: `number` (next from find-spec), `feature`, `type: feature`, `status: draft`, `parent: <parent_number>`, `blocked-by: [<bridge_number>]`, `blocking: []`
- No `mode: rewrite` — runs normal `/implement`
- User stories describe updating consumers to use the new interface directly (removing the bridge)

---

## Phase 6: Buildability Gate (max 3 rounds)

Use skill **solid-coder:validate-spec** with `--interactive` on each generated spec.

- [ ] 6.1 Run validate-spec on the parent spec. Incorporate user answers.

---

## Phase 7: User Review (max 2 rounds)

- [ ] 7.1 Present the draft specs (parent)
- [ ] 7.2 Ask using AskUserQuestion:
  ```
  1. Yes, write all specs
  2. Needs changes
  ```
- [ ] 7.3 If "needs changes": ask what to adjust, incorporate, re-present. Max 2 rounds.

---

## Phase 8: Write Spec Files

- [ ] 8.1 Derive slug for each spec: lowercase, spaces → hyphens, strip special chars.
- [ ] 8.2 Resolve output path for parent — run:
  ```
  python3 ${CLAUDE_PLUGIN_ROOT}/skills/build-spec/scripts/build-spec-query.py resolve-path feature <SPEC-NNN> <slug> [--parent <parent-SPEC-NNN>]
  ```
  If non-zero exit: stop and report error.
- [ ] 8.3 **Write parent spec first.** Create `Spec.md` + empty `resources/` directory at the resolved path. The parent folder must exist before subtask paths can be resolved.
- [ ] 8.4 Move provided resources into the parent's /resources folder.
- [ ] 8.5 For each subtask, resolve output path — run:
  ```
  python3 ${CLAUDE_PLUGIN_ROOT}/skills/build-spec/scripts/build-spec-query.py resolve-path subtask <SPEC-NNN> <slug> --parent <parent-SPEC-NNN>
  ```
- [ ] 8.6 Write each subtask spec file. Create empty `resources/` directory alongside each.
- [ ] 8.7 Confirm to user with list of all files written.

---

## Constraints
- This workflow always produces epic
- Do NOT modify the existing code — only read and analyze.
- Do NOT create module files — only spec files.
- Do NOT create criteria or requirements coupled with the code to be rewritten, exception how to connect with the legacy system
- Reuse `build-spec-query.py` for path resolution — do NOT inline path logic.
- Fully written specs: `status: ready`.
- `blocked-by` entries are permanent — never remove them.
- If any `build-spec-query.py` call exits non-zero, report and stop.
