---
name: build-spec
description: Interview-driven spec builder — creates, resumes, edits, and breaks down specs within the hierarchy.
argument-hint: ""
allowed-tools: Read, Write, Bash, Skill, AskUserQuestion
user-invocable: true
---

# build-spec — Interview-Driven Spec Builder

## Execution Rules

- **Sub-skill returns are internal values** — when a skill invocation produces JSON output, capture it silently and proceed immediately. Do NOT present the result to the user or pause for confirmation.
- **Only pause for user input at explicit `AskUserQuestion` steps** — all other steps run to completion without stopping.

## Interview Rules

- Mark the inferred default with `[default]`.
- For choice questions, always include a free-text fallback as the last option (e.g. `other: <describe>`).

---

## Phase 0: Entry Point

- [ ] 0.1 If the user provided a spec number (e.g. `SPEC-003`) as an argument or in their prompt:
  - Look it up — use skill **solid-coder:find-spec** with `scan --status draft,ready,in-progress`. Find the matching spec in the results.
  - If not found: report error and stop.
  - If found: load the spec, then load ancestors — use skill **solid-coder:find-spec** with `ancestors <target-SPEC-NNN>`. Read each file in the returned `path` fields (root → leaf). Hold all content as context.
  - Ask using AskUserQuestion:
    ```
    Found: SPEC-NNN — <feature> [<type>, <status>]
    What would you like to do?
    1. Edit or extend this spec
    2. Break down into subtasks
    3. Resume (continue drafting)
    ```
    - If option 1: set `target_spec` and proceed to Phase 3.5 (Extend).
    - If option 2: set `target_spec` and proceed to Phase 3.6 (Breakdown).
    - If option 3: set `target_spec` and proceed to Phase 2.2 (Load context), then Phase 4.

- [ ] 0.2 Otherwise, ask using AskUserQuestion:
  ```
  What would you like to do?
  1. Create a new spec
  2. Resume a draft spec
  3. Edit an existing spec
  ```
  - If option 1: proceed to Phase 1.
  - If option 2: proceed to Phase 2.
  - If option 3: proceed to Phase 3.

---

## Phase 1: Create New Spec

- [ ] 1.1 Run `python3 @scripts/build-spec-query.py types` and ask using AskUserQuestion: "What type is this?" — required choice, no other option, no default.

- [ ] 1.2 **Where does it belong?** — use skill **solid-coder:find-spec** with `--status draft,ready --action Select as parent`. Returns selected spec. Store as `parent_epic` (or none if user chose root epic).

- [ ] 1.3 "Give it a short title." — ask using AskUserQuestion free-text only. This becomes the `feature` slug.

- [ ] 1.4 "What are we building?" — ask using AskUserQuestion free-text description only.

- [ ] 1.5 Get next spec number — use skill **solid-coder:find-spec** with `next-number`. Store result as `next_number`.

Continue to Phase 4.

---

## Phase 2: Resume Draft Spec

- [ ] 2.1 **Find target** — use skill **solid-coder:find-spec** with `--status draft --action Resume this`. Returns selected spec as `target_spec`.

- [ ] 2.2 **Load context** — use skill **solid-coder:find-spec** with `ancestors <target-SPEC-NNN>`. Read each file in the returned `path` fields (root → leaf). Hold all content as context.

Continue to Phase 4.

---

## Phase 3: Edit Existing Spec

- [ ] 3.1 **Find target** — use skill **solid-coder:find-spec** with `--status draft,ready,in-progress --action Edit this`. Returns selected spec as `target_spec`.

- [ ] 3.2 **Load spec** — read the target spec file. Hold its full content as context.

- [ ] 3.3 **Load ancestors** — use skill **solid-coder:find-spec** with `ancestors <target-SPEC-NNN>`. Read each file in the returned `path` fields (root → leaf). Hold all content as context.

- [ ] 3.4 Ask using AskUserQuestion:
  ```
  What would you like to do with this spec?
  1. Extend or modify the spec
  2. Break down into subtasks
  ```
  - If option 1: proceed to Phase 3.5.
  - If option 2: proceed to Phase 3.6.

---

  ### Phase 3.5: Extend / Modify Spec

  - [ ] 3.5.1 Ask using AskUserQuestion: "What needs changing?" — free-text. User describes what to add, remove, or modify.

  - [ ] 3.5.2 Apply the requested changes to the spec draft. Preserve all existing sections and frontmatter — only modify what the user asked to change.

  Continue to Phase 6 (Buildability Gate) with the updated draft.

  ---

  ### Phase 3.6: Break Down Into Subtasks

  - [ ] 3.6.1 Analyze the target spec's user stories, acceptance criteria, and scope. Suggest a subtask breakdown:
    ```
    Based on this spec, here's a suggested breakdown:
    1. <subtask title> — <one-line scope>
    2. <subtask title> — <one-line scope>
    ...
    ```
    Ask using AskUserQuestion: "Adjust, add, remove, or confirm these subtasks?"

  - [ ] 3.6.2 Finalize the subtask list. For each subtask, get the next spec number — use skill **solid-coder:find-spec** with `next-number` before each.

  - [ ] 3.6.3 **For each subtask**, run the full interview and write flow:
    - Set `type = subtask`, `parent = <target_spec number>`, title from the breakdown list.
    - Run Phase 4 (Interview) with the parent spec loaded as ancestor context.
    - Run Phase 5 (Generate Draft).
    - Run Phase 6 (Buildability Gate).
    - Run Phase 7 (User Review).
    - Run Phase 8 (Write) — each subtask gets its own folder with `Spec.md` + `resources/`.

  - [ ] 3.6.4 After all subtasks are written, confirm to user with list of all files created.

  Done — do not continue to Phase 4.

---

## Phase 4: Interview

For each question, infer suggestions from the loaded ancestor context (epic/feature specs read in Phase 2, 3, or 1.2). Present suggestions as numbered options. Always include a free-text fallback as the last option so the user can describe or discuss freely.

- [ ] 4.1 **Connections & context** — "What does this connect to, depend on, or interact with?". Ask using AskUserQuestion. Suggest related features/modules inferred from ancestor specs. Free-text fallback.

- [ ] 4.2 **Inputs & Outputs** — "What goes in and what comes out? Who consumes the output, how do they get it, and what's its lifetime?". Ask using AskUserQuestion. Suggest input/output patterns inferred from sibling specs in the same epic. Free-text fallback.

- [ ] 4.3 **Edge Cases** — "What could go wrong or behave unexpectedly?". Ask using AskUserQuestion. Suggest edge cases inferred from context (e.g. missing data, failures, boundary conditions mentioned in the epic). Free-text fallback.

- [ ] 4.4 **User Stories** — type-differentiated. Ask using AskUserQuestion.
  - **Epic**: "List the main things a user can do with this. I'll turn each into a story." Push for breadth — one story per major capability. Acceptance criteria can be high-level outcomes (each will be detailed in child specs).
  - **Feature**: "What are the distinct user goals this covers?" — 1–3 stories. For each: "What exactly makes this done?" Push for concrete, independently verifiable acceptance criteria.
  - **Subtask**: One story. Push for specificity — placement, connection, and integration details in acceptance criteria.
  - **Bug**: Skip — bugs use reproduction steps, not stories.

  Story format:
  - User-facing: `As a [user], I want [goal] so that [reason]`
  - Business logic / system: `As the system, when [trigger], [outcome]`

  Acceptance criteria rules: each criterion must be independently verifiable. No "works correctly", no "handles edge cases" — name the specific value, behavior, or condition.

- [ ] 4.5 **Technical Requirements** (conditional) —
  - **Subtask**: always ask.
  - **Feature**: ask only if touching business logic or integration.
  - **Epic / Bug**: skip.
  - Ask using AskUserQuestion: "What technical constraints or requirements apply? Think about: specific APIs or frameworks, libraries/dependencies, error codes or failure modes, patterns to follow (or avoid), integration points with existing code."
  - Free-text. Store answers for the `## Technical Requirements` section in the draft.

- [ ] 4.6 **UI / Mockup** (conditional) — if the description or any user story mentions screens, views, components, or user interaction:
  - Generate an ASCII mockup of the UI layout.
  - Ask using AskUserQuestion: "Here's a mockup I sketched. Keep this, or will you provide a design/screenshot?"
  - If keep: embed mockup under `## UI / Mockup` in the draft.
  - If provide: insert `## UI / Mockup\n<!-- TODO: attach image or design -->` placeholder. validate-spec will flag this as a structural gap.

- [ ] 4.7 **Dependency chain** — use skill **solid-coder:find-spec** with `scan --parent <parent_spec> --status draft,ready` to get siblings, then ask:
  - "Which specs must be done before this can start? (`blocked-by`)" — multi-select from results.
  - "Which specs are waiting on this to be done first? (`blocking`)" — multi-select from results.

- [ ] 4.8 **Epic breakdown** (only if type is `epic`):
  ```
  Here is a suggested feature breakdown:
  1. <feature 1>
  2. <feature 2>
  ...

  How should I proceed?
  1. Write as a single epic spec (features listed in Definition of Done)
  2. Write the epic + scaffold each feature now (frontmatter only, dependencies set later)
  ```
  Store choice as `epic_mode` (`single` or `split`).

- [ ] 4.9 **Diagrams** — generate Mermaid diagrams from the collected answers:
  - **Connection diagram** (all types): upstream inputs, downstream consumers, sibling specs, external dependencies.
  - **Flow diagram** (all types):
    - Epic: high-level user journey across subtasks.
    - Feature/subtask: data/control path end-to-end.
  - **Sequence diagram** (conditional): generate if the spec mentions async operations, callbacks, delegates, notifications, network calls, or multiple distinct actors.
  - Present all generated diagrams using AskUserQuestion: "Here are the diagrams I generated. Keep, revise, or describe what to change?"
  - Incorporate any revisions before proceeding.

---

## Phase 5: Generate Draft Spec

- **Frontmatter**: `number`, `feature`, `type`, `status: ready`, `blocked-by`, `blocking`, `parent` (SPEC-NNN if non-root)
- **Description**: 2–4 sentences — purpose, type, where it fits, what it enables
- **Input / Output table** (features/subtasks): formats and locations
- **Bug report section** (bugs): steps to reproduce, expected vs actual, affected component
- **Features section** (epics): ordered list with assigned spec numbers
- **User Stories** (features/epics/subtasks): stories with acceptance criteria, type-differentiated depth
- **Technical Requirements** (subtasks always, features if business logic/integration): APIs, libraries, error codes, patterns, integration points
- **UI / Mockup** (conditional): ASCII mockup or `<!-- TODO: attach image or design -->` placeholder
- **Diagrams**: Mermaid connection diagram, flow diagram, sequence diagram (if applicable)
- **Connects To table**: upstream and downstream from interview answers
- **Edge Cases**: from interview
- **Design Decisions**: key choices and rationale
- **Definition of Done**: verifiable checklist

If `epic_mode = split`: Epic = `next_number`, children = `next_number+1…N`, children get `status: draft`.

---

## Phase 6: Buildability Gate (max 3 rounds)

Use skill **solid-coder:validate-spec** with `--interactive` on the draft spec.

For `epic` specs, validate-spec applies epic-specific rules (scope clarity, subtask breakdown completeness) instead of the standard buildability scan. See validate-spec for details.

- [ ] 6.1 Run validate-spec on the current draft. It will flag gaps and ask the user to resolve them.
- [ ] 6.2 Incorporate the user's answers into the draft.
- [ ] 6.3 Re-run validate-spec on the updated draft. Repeat until clean or 3 rounds reached.
- [ ] 6.4 If gaps remain after 3 rounds, annotate them as `TBD` in the spec with a note explaining what's unresolved. Proceed to Phase 7.

---

## Phase 7: User Review (max 2 rounds)

- [ ] 7.1 Present the full draft spec.
- [ ] 7.2 Ask:
  ```
  1. Yes, write it
  2. Needs changes
  ```
- [ ] 7.3 If "needs changes": ask what to adjust, incorporate, re-present. Max 2 rounds.
- [ ] 7.4 Proceed to Phase 8.

---

## Phase 8: Write Spec File(s)

- [ ] 8.1 Derive slug: lowercase, spaces → hyphens, strip special chars.
- [ ] 8.2 Resolve output path — run:
  ```
  python3 @scripts/build-spec-query.py resolve-path <type> <SPEC-NNN> <slug> [--parent <parent-SPEC-NNN>]
  ```
  If non-zero exit: stop and report error.
- [ ] 8.3 Create empty `resources/` directory alongside each `Spec.md` written.
- [ ] 8.4 If `epic_mode = split`: write epic first (`status: ready`), then scaffold each child with frontmatter only — `number`, `feature`, `type`, `status: draft`, `parent: SPEC-{epic-N}`. No `blocked-by` wiring — dependencies are set later. Each child gets its own folder with `Spec.md` + `resources/`.
- [ ] 8.5 Confirm to user with list of all files written.

---

## Constraints

- Do NOT create module files — only spec files.
- Fully written specs: `status: ready`. Scaffolded children: `status: draft`.
- `blocked-by` entries are permanent — never remove them.
- Re-scan spec numbers at runtime.
- For `split` mode, write ALL specs in this session.
- If any `build-spec-query.py` call exits non-zero, report and stop.
