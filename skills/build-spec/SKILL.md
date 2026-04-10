---
name: build-spec
description: >-
  Detailed workflow for creating and updating specs — covers spec structure, required sections, status lifecycle,
  dependency wiring (blocked-by/blocking), subtask breakdown, and rules for what belongs in a spec vs what doesn't.
  TRIGGER when: creating a new spec, modifying or editing an existing spec, updating a spec's status,
  adding or removing blocked-by/blocking dependencies, breaking a spec into subtasks, or resuming a draft spec.
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

- [ ] 0.2 If the user provided a descriptive prompt (not a spec number, not empty):
  - Proceed to Phase 1 (Prompt-Aware Create).

- [ ] 0.3 Otherwise (no argument), ask using AskUserQuestion:
  ```
  What would you like to do?
  1. Create a new spec
  2. Resume a draft spec
  3. Edit an existing spec
  ```
  - If option 1: proceed to Phase 1 (with empty prompt — full interview).
  - If option 2: proceed to Phase 2.
  - If option 3: proceed to Phase 3.

---

## Phase 1: Create New Spec

- [ ] 1.1 **Analyze prompt** — if the user provided a descriptive prompt, infer as much as possible:
  - **Type** — from language cues (e.g., "bug" → bug, "screen/view/feature" → feature, "break down/epic/initiative" → epic)
  - **Title** — the core noun/action from the prompt
  - **Description** — the full prompt, cleaned up
  - **Parent** — use skill **solid-coder:find-spec** with `scan --status draft,ready,in-progress`. Match the prompt topic against existing epics/features. If one clearly matches, suggest it. If ambiguous or none match, suggest root.
  - **User stories (draft)** — extract any behaviors, goals, or actions mentioned in the prompt. Format as stories. These are drafts — Phase 4 will refine them.
  - If no prompt was provided, set all inferences to empty.

- [ ] 1.2 **Present inference** — if any fields were inferred, present them via AskUserQuestion:
  ```
  Here's what I got from your prompt:

  Type: <inferred type>
  Title: <inferred title>
  Parent: <inferred parent or "root">

  Description: <inferred description>

  User Stories (draft):
  - <story 1>
  - <story 2>
  ...

  1. Looks good, continue to detail questions [default]
  2. Needs adjustments
  3. Start fresh (full interview)
  ```
  - If "looks good": store all inferred values, proceed to Phase 1.4.
  - If "needs adjustments": ask what to change, incorporate, re-present.
  - If "start fresh": clear all inferences, proceed to Phase 1.3.

- [ ] 1.3 **Manual create** (when no prompt, or user chose "start fresh"):
  - Run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/build-spec/scripts/build-spec-query.py types` and ask using AskUserQuestion: "What type is this?"
  - **Where does it belong?** — use skill **solid-coder:find-spec** with `navigate draft,ready Select as parent`. Store as `parent_epic`.
  - "Give it a short title." — ask using AskUserQuestion free-text only.
  - "What are we building?" — ask using AskUserQuestion free-text description only.

- [ ] 1.4 Get next spec number — use skill **solid-coder:find-spec** with `next-number`. Store result as `next_number`.

Continue to Phase 4. If stories were inferred in 1.1, Phase 4.4 presents them as `[default]` for confirmation instead of asking from scratch. Same for any other Phase 4 question where the answer is already inferred from the prompt.

---

## Phase 2: Resume Draft Spec

- [ ] 2.1 **Find target** — use skill **solid-coder:find-spec** with `navigate draft Resume this`. Returns selected spec as `target_spec`.

- [ ] 2.2 **Load context** — use skill **solid-coder:find-spec** with `ancestors <target-SPEC-NNN>`. Read each file in the returned `path` fields (root → leaf). Hold all content as context.

Continue to Phase 4.

---

## Phase 3: Edit Existing Spec

- [ ] 3.1 **Find target** — use skill **solid-coder:find-spec** with `navigate draft,ready,in-progress Edit this`. Returns selected spec as `target_spec`.

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

  ### Phase 3.6: Break Down Into Subtasks (lightweight)

  Do NOT rerun the full Phase 4 interview per child. Derive child specs from the parent's stories.

  - [ ] 3.6.1 Analyze the target spec's user stories, acceptance criteria, and scope. Suggest a subtask breakdown — each story or story group becomes a subtask:
    ```
    Based on this spec, here's a suggested breakdown:
    1. <subtask title> — <one-line scope> (from story: <story reference>)
    2. <subtask title> — <one-line scope> (from story: <story reference>)
    ...
    ```
    Ask using AskUserQuestion: "Adjust, add, remove, or confirm these subtasks?"

  - [ ] 3.6.2 Finalize the subtask list. For each subtask, get the next spec number — use skill **solid-coder:find-spec** with `next-number` before each.

  - [ ] 3.6.3 **For each subtask**, generate a pre-filled draft directly from parent context:
    - Set `type = subtask`, `parent = <target_spec number>`, title from the breakdown list.
    - Derive stories, connections, I/O, technical requirements, and edge cases from the parent spec's content. The parent already has all the context — the child spec narrows scope, it doesn't re-discover it.
    - Run Phase 5 (Generate Draft) — no Phase 4 interview.
    - Run Phase 6 (Buildability Gate).
    - Present each child draft to the user with a single AskUserQuestion: "Write this subtask spec, or adjust?"
    - If "adjust": user provides changes in one free-text response, apply, then write.
    - Run Phase 8 (Write) — each subtask gets its own folder with `Spec.md` + `resources/`.

  - [ ] 3.6.4 After all subtasks are written, confirm to user with list of all files created.

  Done — do not continue to Phase 4.

---

## Phase 4: Interview (3 steps)

Infer suggestions from loaded ancestor context. Present inferences as `[default]` options. Always include a free-text fallback. The goal is **3 user interactions** for Phase 4 — not 9.

### Step 1: Stories — "What is this?"

Stories are the anchor. Everything else flows from them.

- [ ] 4.1 **User Stories** — type-differentiated. Ask using AskUserQuestion.
  - **Epic**: "List the main things a user can do with this. I'll turn each into a story." Push for breadth — one story per major capability. Acceptance criteria can be high-level outcomes (each will be detailed in child specs).
  - **Feature**: "What are the distinct user goals this covers?" — 1–3 stories. For each: "What exactly makes this done?" Push for concrete, independently verifiable acceptance criteria.
  - **Subtask**: One story. Push for specificity — placement, connection, and integration details in acceptance criteria.
  - **Bug**: Skip — bugs use reproduction steps, not stories.

  If Phase 1 inferred stories from the prompt, present them as `[default]` for confirmation.

  Story format:
  - User-facing: `As a [user], I want [goal] so that [reason]`
  - Business logic / system: `As the system, when [trigger], [outcome]`

  Acceptance criteria rules: each criterion must be independently verifiable. No "works correctly", no "handles edge cases" — name the specific value, behavior, or condition.

  - **Epic breakdown** (only if type is `epic`): after confirming stories, suggest a feature breakdown:
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

### Step 2: Context — "What surrounds it?"

Batch related context questions into a single AskUserQuestion with multiple questions (the tool supports up to 4 questions per call). Pre-fill from ancestor context and stories.

- [ ] 4.2 Ask using AskUserQuestion with up to 4 questions in one call:

  **Q1 — Connections**: "What does this connect to, depend on, or interact with?"
  - Suggest related features/modules inferred from ancestor specs. Free-text fallback.

  **Q2 — Inputs & Outputs**: "What goes in and what comes out? Who consumes the output?"
  - Suggest I/O patterns inferred from stories and sibling specs. Free-text fallback.

  **Q3 — Technical constraints** (conditional — skip for epics/bugs):
  - "What technical constraints apply? (APIs, libraries, patterns, error modes)"
  - Free-text fallback.

  **Q4 — Dependencies**: "Any specs this is blocked by or blocking?"
  - Use skill **solid-coder:find-spec** with `scan --parent <parent_spec> --status draft,ready` to get siblings.
  - Present as multi-select from results. Free-text fallback.

### Step 3: Edge cases — "What could go wrong?"

Now asked AFTER stories exist — answers become acceptance criteria on specific stories.

- [ ] 4.3 **Edge cases & design choices** — infer edge cases from the stories and context already collected. Present inferred edge cases as `[default]` options. Ask using AskUserQuestion:
  - "Based on the stories, here are the edge cases and design choices I see. Confirm, add, or adjust."
  - Suggest: error conditions, boundary values, failure modes, race conditions inferred from the stories and technical context.
  - Free-text fallback.
  - Hold answers — these will be written as acceptance criteria on the relevant user stories, not as a separate section.

### Silent generation (no user interaction)

These are generated automatically and shown in the draft for review in Phase 7. No separate confirmation step.

- [ ] 4.4 **UI / Mockup** — ask using AskUserQuestion:
  - If UI elements detected in description/stories: "Do you have design screenshots to include in resources/?"
    - If yes: write `## UI / Mockup\nReference screenshots are in the \`resources/\` directory adjacent to this spec file.`
    - If no: skip `## UI / Mockup` section entirely.
  - If no UI elements detected: skip.

- [ ] 4.5 **Test Plan** — generate test cases from user stories and edge cases collected in steps 4.1–4.3:
  - Derive test cases from every acceptance criterion and edge case — both happy paths and failure/boundary paths
  - Language: `"When [precondition or state], [action], [observable outcome]"` — present tense, no "should", no "verify that"
  - Group by component or screen: Unit Tests per service/model, UI Tests per screen or flow (if UI spec)
  - Each case is one sentence — concrete and independently runnable
  - After generating, present to user via AskUserQuestion:
    ```
    Here are the test cases I derived. Add, remove, or adjust:
    ### Unit Tests — <ComponentName>
    - When ...
    ### UI Tests — <ScreenName>
    - When ...
    ```
  - Incorporate user's changes. Store final list for Phase 5.

- [ ] 4.6 **Diagrams** — generate Mermaid diagrams from the collected answers:
  - **Connection diagram** (all types): upstream inputs, downstream consumers, sibling specs, external dependencies.
  - **Flow diagram** (all types): epic = high-level user journey, feature/subtask = data/control path end-to-end.
  - **Sequence diagram** (conditional): generate if the spec mentions async operations, callbacks, delegates, notifications, network calls, or multiple distinct actors.
  - Embed all in draft under `## Diagrams`. User reviews them in Phase 7.

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
- **Test Plan** (feature/subtask/bug with testable behavior): grouped by component/screen, test cases in `"When [condition], [action], [outcome]"` format covering happy paths and edge cases. For bugs: must include at least one regression test case that would have caught the bug.
- **Diagrams**: Mermaid connection diagram, flow diagram, sequence diagram (if applicable)
- **Connects To table**: upstream and downstream from interview answers
- **Definition of Done**: verifiable checklist

If `epic_mode = split`: Epic = `next_number`, children = `next_number+1…N`, children get `status: draft`.

---

## Phase 6: Buildability Gate (max 2 rounds)

Use skill **solid-coder:validate-spec** with `--batch` on the draft spec. Batch mode returns all findings at once instead of asking one-by-one.

For `epic` specs, validate-spec applies epic-specific rules (scope clarity, subtask breakdown completeness) instead of the standard buildability scan. See validate-spec for details.

- [ ] 6.1 Run validate-spec with `--batch` on the current draft. Collect all findings.
- [ ] 6.2 If findings exist, present ALL of them in a single AskUserQuestion (multiSelect: true):
  ```
  Buildability findings — select which to resolve now (rest will be marked TBD):
  1. [category] location — question
  2. [category] location — question
  ...
  ```
  User selects which findings to address and provides answers.
- [ ] 6.3 Incorporate selected answers into the draft. Mark unselected findings as `TBD`.
- [ ] 6.4 Re-run validate-spec with `--batch`. If new findings → repeat 6.2 (max 1 more round).
- [ ] 6.5 If gaps remain after 2 rounds, annotate remaining as `TBD`. Proceed to Phase 7.

---

## Phase 7: User Review (max 2 rounds)

- [ ] 7.1 Present the full draft spec (includes diagrams and mockups generated in Phase 4).
- [ ] 7.2 Ask using AskUserQuestion:
  ```
  1. Yes, write it
  2. Specific changes needed — describe ALL changes at once
  ```
- [ ] 7.3 If "specific changes": user provides all changes in one free-text response. Apply all changes, re-present once. Max 1 re-present — after 2 total rounds, write what exists.
- [ ] 7.4 Proceed to Phase 8.

---

## Phase 8: Write Spec File(s)

- [ ] 8.1 Derive slug: lowercase, spaces → hyphens, strip special chars.
- [ ] 8.2 Resolve output path — run:
  ```
  python3 ${CLAUDE_PLUGIN_ROOT}/skills/build-spec/scripts/build-spec-query.py resolve-path <type> <SPEC-NNN> <slug> [--parent <parent-SPEC-NNN>]
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
