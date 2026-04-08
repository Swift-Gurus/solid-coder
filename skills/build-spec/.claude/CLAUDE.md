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
- Structured body: Description, Inputs/Outputs, User Stories, Connects To, Technical Requirements, Definition of Done

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
- **Edit mode (Phase 3)** — "Edit an existing spec" covers two sub-flows: (1) Extend/modify — user describes changes, spec is updated and re-validated. (2) Break down into subtasks — AI analyzes the spec, suggests a subtask breakdown, user confirms. **Lightweight children**: each subtask is derived from the parent's stories, not re-interviewed. One confirmation per child instead of full Phase 4.
- **Technical Requirements (Phase 4, Step 2)** — batched with connections, I/O, and dependencies into a single AskUserQuestion. Always asked for subtasks, asked for features only when touching business logic or integration, skipped for epics and bugs.
- **Edge cases and design decisions are acceptance criteria** — no separate `## Edge Cases` or `## Design Decisions` sections. Edge cases (error conditions, boundary values, failure modes) and design choices (patterns, approaches, trade-offs) are captured as concrete, verifiable acceptance criteria on the relevant user stories. This ensures they propagate through the structured AC pipeline (arch.json → implementation-plan → code self-check) instead of being lost as narrative text.
- **Prompt-aware fast path (Phase 1)** — if the user provides a descriptive prompt, the skill infers type, title, parent, description, and draft stories from it. Presents everything in a single confirmation step. User confirms, adjusts, or opts for the full interview. Rich prompts skip most of Phase 1 and pre-fill Phase 4 answers as `[default]`. No prompt = full interview as before.
- **Prescriptive interview question format** — all choice questions use a numbered list with "N. other: <describe here>" as the last option and `[default]` marking the inferred answer. Multi-select questions (blocked-by, blocking, parent) list existing specs by number. Free-text questions ask one thing at a time. This prevents unpredictable or inconsistent UX.
- **Folder-per-spec** — every spec (not just epics) is a folder containing `Spec.md` and `resources/`. Features, bugs, and subtasks are placed inside their parent epic's folder under `features/`, `features/bugs/`, or `features/subtasks/` — each as their own subfolder. Epics can nest: a child epic gets its own subfolder inside the parent epic's folder. The `resources/` directory holds designs, images, and other materials for that spec. This mirrors the logical ownership structure in the filesystem and supports attaching reference materials alongside specs.
- **Epic split writes all specs in one session** — when the user picks "one spec per subtask", the skill pre-assigns spec numbers (epic = next_number, subtasks = next_number+1…N) and writes all specs immediately, wiring `blocked-by` sequentially between subtasks and `blocking` on the epic. Does not defer to separate `/build-spec` invocations.
- **Type system (bug / feature / epic / subtask)** — spec type shapes the interview questions, the spec body structure, and the Definition of Done. A bug spec needs reproduction steps; an epic needs a subtask list; a subtask needs a parent reference.
- **3-step interview (Phase 4)** — redesigned from 9 sequential questions to 3 focused steps: (1) Stories first — the anchor, everything flows from them. (2) Context batch — connections, I/O, tech constraints, and dependencies in a single multi-question AskUserQuestion. (3) Edge cases — asked AFTER stories exist so answers become concrete acceptance criteria. Diagrams and mockups generated silently, shown in draft. Reduces feature spec from 12-18 interactions to 5-7.
- **Adaptive interview** — ambiguity questions are only asked when gaps are identified. Clear prompts get fewer questions.
- **Scope gate** — if a prompt implies an epic, the skill surfaces this before drafting, giving the user a chance to split or confirm. Prevents creating one bloated spec that should be multiple.
- **Free-text connections** — user describes relationships in their own words rather than selecting from a fixed catalogue. Generic and expressive.
- **Buildability gate (Phase 6)** — after generating the draft, runs `validate-spec --batch`. Batch mode returns all findings at once. build-spec presents ALL findings in a single AskUserQuestion (multiSelect) — user picks which to resolve now, rest marked TBD. Max 2 rounds (down from 3). For epics: epic-specific rules (vague scope, undefined subtasks, missing success criteria, ambiguous ownership).
- **User stories replace workflow (2.4)** — features, epics, and subtasks use user stories instead of a phased workflow checklist. The planner/synthesizer derives implementation steps from stories; the spec doesn't pre-solve sequencing. Interview depth is type-differentiated: epics push breadth (one story per capability), features push concrete acceptance criteria, subtasks push placement/connection specificity. Bugs keep reproduction steps — stories don't fit.
- **System story format for business logic** — when a feature has no UI actor, stories use `As the system, when [trigger], [outcome]`. Same format, fits alongside user-facing stories.
- **UI / Mockup (Phase 4.4)** — asks user whether to keep generated ASCII mockup or provide design screenshots. When no UI detected, asks if designs exist. Placeholder inserted for user-provided designs. No separate confirmation round-trip.
- **Diagrams generated silently (Phase 4.5)** — connection, flow, and sequence diagrams are generated from collected answers and embedded directly in the draft. No separate "keep or revise?" step — user reviews diagrams as part of the full draft in Phase 7.
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