---
number: SPEC-006
feature: build-spec
type: feature
status: done
blocked-by: []
blocking: []
---

# build-spec — Interview-Driven Spec Builder

## Description

User-invocable skill that takes a free-text feature prompt and guides the user through a structured interview to produce a well-formed spec file at `{CURRENT_PROJECT}/.claude/specs/SPEC-NNN-<slug>.md`.

Generic — not limited to skills or agents. Can produce a spec for any feature, module, bug fix, or epic.

The flow is **hybrid**: the skill classifies the prompt, resolves ambiguity, checks scope, asks focused questions, generates a full draft spec, presents it for review, then writes the file.

## Input

- `$ARGUMENTS[0]` — a free-text prompt describing the feature, bug, or idea (e.g., `"a skill that lints Swift file headers"`).

## Output

A spec markdown file written to `{CURRENT_PROJECT}/.claude/specs/SPEC-NNN-<slug>.md` with:
- YAML frontmatter: `number`, `feature`, `type`, `status: draft`, `blocked-by`, `blocking`, `parent` (if subtask)
- Structured body: Description, Inputs/Outputs, Workflow phases, Connects To, Design Decisions, Definition of Done

## Spec Types

| Type | When to use |
|------|-------------|
| `bug` | Something is broken and needs fixing |
| `feature` | New capability or improvement to existing behaviour |
| `epic` | Large initiative that must be broken down into subtasks |
| `subtask` | A scoped unit of work that belongs to a parent epic |

## Connects To

None — spec discovery uses direct grep/glob on frontmatter fields rather than delegating to `parse-frontmatter`.

## Design Decisions

- **Status lifecycle (draft → ready → in-progress → done)** — all specs track status. Propagation rules enforce that a parent can't advance past `draft` while any child is `draft`. Violations warn before allowing override.
- **Resume mode** — when invoked with no args, offers "Resume existing spec". Navigates the hierarchy: epic → child (feature/bug/child-epic) → subtask. Supports updating status or editing content. Propagation rules are applied at status-update time.
- **Edit mode (Phase 3)** — "Edit an existing spec" covers two sub-flows: (1) Extend/modify — user describes changes, spec is updated and re-validated. (2) Break down into subtasks — AI analyzes the spec, suggests a subtask breakdown, user confirms, then each subtask goes through the full interview+write flow with parent context. The breakdown flow runs Phases 4–8 per subtask in sequence.
- **Technical Requirements (Phase 4.5)** — interview step between User Stories and UI/Mockup. Always asked for subtasks, asked for features only when touching business logic or integration, skipped for epics and bugs. Captures APIs, libraries, error codes, patterns, and integration points. validate-spec flags missing Technical Requirements on subtasks as a structural gap.
- **No-argument guided mode (Phase 0-New)** — if invoked with no argument, the skill runs a short upfront interview (what are we building → type → title → standalone or subfeature) before entering the normal classify/scope/interview flow. This makes `/build-spec` usable without knowing what to type as the argument.
- **Prescriptive interview question format** — all choice questions use a numbered list with "N. other: <describe here>" as the last option and `[default]` marking the inferred answer. Multi-select questions (blocked-by, blocking, parent) list existing specs by number. Free-text questions ask one thing at a time. This prevents unpredictable or inconsistent UX.
- **Folder-per-spec** — every spec (not just epics) is a folder containing `Spec.md` and `resources/`. Features, bugs, and subtasks are placed inside their parent epic's folder under `features/`, `features/bugs/`, or `features/subtasks/` — each as their own subfolder. Epics can nest: a child epic gets its own subfolder inside the parent epic's folder. The `resources/` directory holds designs, images, and other materials for that spec. This mirrors the logical ownership structure in the filesystem and supports attaching reference materials alongside specs.
- **Epic split writes all specs in one session** — when the user picks "one spec per subtask", the skill pre-assigns spec numbers (epic = next_number, subtasks = next_number+1…N) and writes all specs immediately, wiring `blocked-by` sequentially between subtasks and `blocking` on the epic. Does not defer to separate `/build-spec` invocations.
- **Type system (bug / feature / epic / subtask)** — spec type shapes the interview questions, the spec body structure, and the Definition of Done. A bug spec needs reproduction steps; an epic needs a subtask list; a subtask needs a parent reference.
- **Adaptive interview** — ambiguity questions are only asked when Phase 2 identifies gaps. Clear prompts get fewer questions.
- **Scope gate** — if a prompt implies an epic, the skill surfaces this before drafting, giving the user a chance to split or confirm. Prevents creating one bloated spec that should be multiple.
- **Free-text connections** — user describes relationships in their own words rather than selecting from a fixed catalogue. Generic and expressive.
- **Buildability gate (Phase 4)** — after generating the draft, runs `validate-spec --interactive`. For features/bugs/subtasks this checks concrete buildability: vague terms, undefined types, implicit consumer contracts, intent-described API calls. For epics it applies epic-specific rules: vague scope, undefined subtasks, missing success criteria, ambiguous ownership. Loops up to 3 rounds, asking the user to resolve gaps. Unresolved gaps after 3 rounds are annotated as `TBD`. Runs before user review so the user sees a tighter draft.
- **User stories replace workflow (2.4)** — features, epics, and subtasks use user stories instead of a phased workflow checklist. The planner/synthesizer derives implementation steps from stories; the spec doesn't pre-solve sequencing. Interview depth is type-differentiated: epics push breadth (one story per capability), features push concrete acceptance criteria, subtasks push placement/connection specificity. Bugs keep reproduction steps — stories don't fit.
- **System story format for business logic** — when a feature has no UI actor, stories use `As the system, when [trigger], [outcome]`. Same format, fits alongside user-facing stories.
- **UI / Mockup phase (2.5, conditional)** — triggered when description or any user story mentions screens, views, components, or user interaction. AI generates an ASCII mockup and asks the user to keep it or provide a design/screenshot. If user will provide: inserts a placeholder that validate-spec flags as a structural gap.
- **Diagram generation (2.8)** — after interview answers are collected, AI generates Mermaid diagrams: connection (all types), flow (all types, epic=user journey, feature=data/control path), sequence (conditional on async/multi-actor). User reviews and confirms before draft is written.
- **Consumer contract in I/O (2.2)** — the inputs/outputs question also asks who consumes the output, how they get it, and what its lifetime is. Prevents implicit ownership models.
- **User review loop capped at 2 rounds** — prevents infinite back-and-forth. After 2 rounds, write what exists.
- **parse-frontmatter for all discovery** — no hand-rolled YAML parsing. Consistent with project conventions.
- **Status always `draft`** — `build-spec` never marks a spec as `done`. That happens when the module is implemented (per spec lifecycle rules).
- **`**/.claude/CLAUDE.md` glob** — two-level wildcard required because module specs live at `skills/<name>/.claude/CLAUDE.md`, not `*/.claude/CLAUDE.md`.

## Gotchas

- The skill must re-scan spec numbers at runtime (not hardcode), because specs may have been added since the last run.
- `blocked-by` lists are permanent records — spec lifecycle rules say never remove entries when a dependency is completed.
- Do NOT create module files (SKILL.md, agents/*.md) — only the spec file.
- For epics, the subtask breakdown is a suggestion. The user decides whether to write one spec or many.