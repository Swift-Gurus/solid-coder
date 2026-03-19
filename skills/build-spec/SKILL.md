---
name: build-spec
description: Interview-driven spec builder — creates new specs or resumes draft specs within the hierarchy.
argument-hint: ""
allowed-tools: Read, Write, Bash, AskUserQuestion
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

Ask using AskUserQuestion:
```
What would you like to do?
1. Create a new spec
2. Resume a draft spec
```
- If option 1: proceed to Phase 1.
- If option 2: proceed to Phase 2.

---

## Phase 1: Create New Spec

- [ ] 1.1 Run `python3 @scripts/build-spec-query.py types` and ask using AskUserQuestion: "What type is this?" — required choice, no other option, no default.

- [ ] 1.2 **Where does it belong?** — use skill **solid-coder:find-spec** with `--status draft,ready --action Select as parent`. Returns selected spec. Store as `parent_epic` (or none if user chose root epic).

- [ ] 1.3 "Give it a short title." — ask using AskUserQuestion free-text only. This becomes the `feature` slug.

- [ ] 1.4 "What are we building?" — ask using AskUserQuestion free-text description only.

- [ ] 1.5 Get next spec number — use skill **solid-coder:find-spec** with `next-number`. Store result as `next_number`.

Continue to Phase 3.

---

## Phase 2: Resume Draft Spec

- [ ] 2.1 **Find target** — use skill **solid-coder:find-spec** with `--status draft --action Resume this`. Returns selected spec as `target_spec`.

- [ ] 2.2 **Load context** — use skill **solid-coder:find-spec** with `ancestors <target-SPEC-NNN>`. Read each file in the returned `path` fields (root → leaf). Hold all content as context.

Continue to Phase 3.

---

## Phase 3: Interview

For each question, infer suggestions from the loaded ancestor context (epic/feature specs read in Phase 2 or 1.2). Present suggestions as numbered options. Always include a free-text fallback as the last option so the user can describe or discuss freely.

- [ ] 3.1 **Connections & context** — "What does this connect to, depend on, or interact with?". Ask using AskUserQuestion. Suggest related features/modules inferred from ancestor specs. Free-text fallback.

- [ ] 3.2 **Inputs & Outputs** — "What goes in and what comes out? Who consumes the output, how do they get it, and what's its lifetime?". Ask using AskUserQuestion. Suggest input/output patterns inferred from sibling specs in the same epic. Free-text fallback.

- [ ] 3.3 **Edge Cases** — "What could go wrong or behave unexpectedly?". Ask using AskUserQuestion. Suggest edge cases inferred from context (e.g. missing data, failures, boundary conditions mentioned in the epic). Free-text fallback.

- [ ] 3.4 **User Stories** — type-differentiated. Ask using AskUserQuestion.
  - **Epic**: "List the main things a user can do with this. I'll turn each into a story." Push for breadth — one story per major capability. Acceptance criteria can be high-level outcomes (each will be detailed in child specs).
  - **Feature**: "What are the distinct user goals this covers?" — 1–3 stories. For each: "What exactly makes this done?" Push for concrete, independently verifiable acceptance criteria.
  - **Subtask**: One story. Push for specificity — placement, connection, and integration details in acceptance criteria.
  - **Bug**: Skip — bugs use reproduction steps, not stories.

  Story format:
  - User-facing: `As a [user], I want [goal] so that [reason]`
  - Business logic / system: `As the system, when [trigger], [outcome]`

  Acceptance criteria rules: each criterion must be independently verifiable. No "works correctly", no "handles edge cases" — name the specific value, behavior, or condition.

- [ ] 3.5 **UI / Mockup** (conditional) — if the description or any user story mentions screens, views, components, or user interaction:
  - Generate an ASCII mockup of the UI layout.
  - Ask using AskUserQuestion: "Here's a mockup I sketched. Keep this, or will you provide a design/screenshot?"
  - If keep: embed mockup under `## UI / Mockup` in the draft.
  - If provide: insert `## UI / Mockup\n<!-- TODO: attach image or design -->` placeholder. validate-spec will flag this as a structural gap.

- [ ] 3.6 **Dependency chain** — use skill **solid-coder:find-spec** with `scan --parent <parent_spec> --status draft,ready` to get siblings, then ask:
  - "Which specs must be done before this can start? (`blocked-by`)" — multi-select from results.
  - "Which specs are waiting on this to be done first? (`blocking`)" — multi-select from results.

- [ ] 3.7 **Epic breakdown** (only if type is `epic`):
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

- [ ] 3.8 **Diagrams** — generate Mermaid diagrams from the collected answers:
  - **Connection diagram** (all types): upstream inputs, downstream consumers, sibling specs, external dependencies.
  - **Flow diagram** (all types):
    - Epic: high-level user journey across subtasks.
    - Feature/subtask: data/control path end-to-end.
  - **Sequence diagram** (conditional): generate if the spec mentions async operations, callbacks, delegates, notifications, network calls, or multiple distinct actors.
  - Present all generated diagrams using AskUserQuestion: "Here are the diagrams I generated. Keep, revise, or describe what to change?"
  - Incorporate any revisions before proceeding.

---

## Phase 4: Generate Draft Spec

- **Frontmatter**: `number`, `feature`, `type`, `status: ready`, `blocked-by`, `blocking`, `parent` (SPEC-NNN if non-root)
- **Description**: 2–4 sentences — purpose, type, where it fits, what it enables
- **Input / Output table** (features/subtasks): formats and locations
- **Bug report section** (bugs): steps to reproduce, expected vs actual, affected component
- **Features section** (epics): ordered list with assigned spec numbers
- **User Stories** (features/epics/subtasks): stories with acceptance criteria, type-differentiated depth
- **UI / Mockup** (conditional): ASCII mockup or `<!-- TODO: attach image or design -->` placeholder
- **Diagrams**: Mermaid connection diagram, flow diagram, sequence diagram (if applicable)
- **Connects To table**: upstream and downstream from interview answers
- **Edge Cases**: from interview
- **Design Decisions**: key choices and rationale
- **Definition of Done**: verifiable checklist

If `epic_mode = split`: Epic = `next_number`, children = `next_number+1…N`, children get `status: draft`.

---

## Phase 5: Buildability Gate (max 3 rounds)

Use skill **solid-coder:validate-spec** with `--interactive` on the draft spec.

For `epic` specs, validate-spec applies epic-specific rules (scope clarity, subtask breakdown completeness) instead of the standard buildability scan. See validate-spec for details.

- [ ] 5.1 Run validate-spec on the current draft. It will flag gaps and ask the user to resolve them.
- [ ] 5.2 Incorporate the user's answers into the draft.
- [ ] 5.3 Re-run validate-spec on the updated draft. Repeat until clean or 3 rounds reached.
- [ ] 5.4 If gaps remain after 3 rounds, annotate them as `TBD` in the spec with a note explaining what's unresolved. Proceed to Phase 6.

---

## Phase 6: User Review (max 2 rounds)

- [ ] 6.1 Present the full draft spec.
- [ ] 6.2 Ask:
  ```
  1. Yes, write it
  2. Needs changes
  ```
- [ ] 6.3 If "needs changes": ask what to adjust, incorporate, re-present. Max 2 rounds.
- [ ] 6.4 Proceed to Phase 7.

---

## Phase 7: Write Spec File(s)

- [ ] 7.1 Derive slug: lowercase, spaces → hyphens, strip special chars.
- [ ] 7.2 Resolve output path — run:
  ```
  python3 @scripts/build-spec-query.py resolve-path <type> <SPEC-NNN> <slug> [--parent <parent-SPEC-NNN>]
  ```
  If non-zero exit: stop and report error.
- [ ] 7.3 If `epic_mode = split`: write epic first (`status: ready`), then scaffold each child with frontmatter only — `number`, `feature`, `type`, `status: draft`, `parent: SPEC-{epic-N}`. No `blocked-by` wiring — dependencies are set later.
- [ ] 7.4 Confirm to user with list of all files written.

---

## Constraints

- Do NOT create module files — only spec files.
- Fully written specs: `status: ready`. Scaffolded children: `status: draft`.
- `blocked-by` entries are permanent — never remove them.
- Re-scan spec numbers at runtime.
- For `split` mode, write ALL specs in this session.
- If any `build-spec-query.py` call exits non-zero, report and stop.
