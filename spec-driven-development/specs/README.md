# Spec Rules — Shared Reference

Single source of truth for spec structure and validation across the SDD pipeline. Used by:

| Skill | Usage |
|-------|-------|
| `build-spec` | Generates drafts following the per-type rule |
| `build-spec-from-code` | Generates rewrite specs following the per-type rule (with `mode: rewrite` frontmatter flag) |
| `validate-spec` | Structural + buildability checks verify each spec per type |

## Per-Type Rules

Each type follows the same split pattern as `references/principles/`: `rule.md` defines the structure; `review/instructions.md` defines the validation rules.

| Type | Structure | Validation | When to use |
|------|-----------|------------|-------------|
| `epic` | [epic/rule.md](epic/rule.md) | [epic/review/instructions.md](epic/review/instructions.md) | Large initiative broken into subtasks/features |
| `feature` | [feature/rule.md](feature/rule.md) | [feature/review/instructions.md](feature/review/instructions.md) | New capability or improvement |
| `subtask` | [subtask/rule.md](subtask/rule.md) | [subtask/review/instructions.md](subtask/review/instructions.md) | Scoped unit of work under a parent epic/feature |
| `bug` | [bug/rule.md](bug/rule.md) | [bug/review/instructions.md](bug/review/instructions.md) | Something broken that needs fixing (status-aware, two-phase) |

- `build-spec` / `build-spec-from-code` read **`<type>/rule.md`** (structure + story depth + format)
- `validate-spec` reads **`<type>/review/instructions.md`** (structural + buildability rules)

## Common Frontmatter

Every spec file starts with YAML frontmatter. These fields are **common to all types**:

| Field | Required | Values | Notes |
|-------|----------|--------|-------|
| `number` | always | `SPEC-NNN` | Assigned by `find-spec next-number` |
| `feature` | always | slug string | Lowercase, hyphen-separated |
| `type` | always | `epic` / `feature` / `subtask` / `bug` | Drives rule selection |
| `status` | always | `draft` / `ready` / `in-progress` / `done` | Lifecycle state |
| `parent` | if non-root | `SPEC-NNN` | Parent spec number |
| `blocked-by` | always (can be `[]`) | array of `SPEC-NNN` | Permanent record — never remove entries |
| `blocking` | always (can be `[]`) | array of `SPEC-NNN` | Permanent record — never remove entries |
| `mode` | optional | `rewrite` | Signals greenfield rebuild — validate-plan skips codebase search |

## Common Sections (all types)

Every spec — regardless of type — includes these sections:

1. **`# <Title>`** — H1 with the feature name
2. **`## Description`** — 2–4 sentences covering purpose, where it fits, what it enables
3. **`## Diagrams`** — at minimum: connection diagram + flow diagram. Sequence diagram if async/multi-actor.
4. **`## Definition of Done`** — verifiable checklist

Type-specific sections (Input/Output, User Stories, Test Plan, etc.) are documented in the per-type `rule.md` files.

## Section Rules (applied everywhere)

- **Acceptance criteria must be independently verifiable.** No "works correctly", "handles edge cases", "behaves as expected". Name the specific value, behavior, or condition.
- **No implementation leaking.** Specs are behavioral. No language-specific syntax, type names, method signatures, attributes, or framework-specific types in requirement text. Pseudo-code, algorithms, diagrams, design pattern names, and schema contracts are allowed.
- **Edge cases and design decisions belong in acceptance criteria** — not separate sections. They propagate through the pipeline as verifiable ACs.
- **Story format:**
  - User-facing: `As a [user], I want [goal] so that [reason]`
  - Business logic / system: `As the system, when [trigger], [outcome]`
- **Test cases format:** `"When [condition], [action], [outcome]"` — present tense, no "should", no "verify that".
- **Connections** — describe what this connects to, depends on, interacts with. Always a table with upstream + downstream rows.

## Conditional Sections

These appear when the spec's content warrants them:

| Section | When required |
|---------|---------------|
| `## Input / Output` | `feature` / `subtask` always. Formats + locations. |
| `## User Stories` | `feature` / `subtask` / `epic` (epic = one story per capability) |
| `## Technical Requirements` | `subtask` always. `feature` if touching business logic/integration/APIs. Not for `epic`/`bug`. |
| `## UI / Mockup` | When the spec mentions screens, views, components, or user interaction. Content: reference to `resources/`, ASCII mockup, or image. Placeholder-only counts as missing. |
| `## Test Plan` | `feature` / `subtask` / `bug` where behavior is testable. Not for `epic` or internal/infrastructure-only stories. |
| `## Current State` | `rewrite` mode specs only. Snapshot of existing code — types, responsibilities, integration map. |
| `## Features` | `epic` only. Ordered list of child features with assigned spec numbers. |

## Folder Structure

Every spec is a folder. Layout:

```
SPEC-NNN-<slug>/
├── Spec.md
└── resources/          (designs, images, screenshots)
```

Children are nested:

```
epic-folder/
├── Spec.md
├── resources/
└── features/
    ├── feature-folder/
    │   ├── Spec.md
    │   ├── resources/
    │   └── subtasks/
    │       └── subtask-folder/
    │           ├── Spec.md
    │           └── resources/
    └── bugs/
        └── bug-folder/
            ├── Spec.md
            └── resources/
```
