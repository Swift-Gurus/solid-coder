# Epic Template

Large initiative that must be broken down into features or subtasks.

## Frontmatter

```yaml
---
number: SPEC-NNN
feature: <slug>
type: epic
status: draft          # draft | ready | in-progress | done
parent: SPEC-NNN       # omit for root epic
blocked-by: []
blocking: []
mode: rewrite          # optional — only for rewrite epics from build-spec-from-code
---
```

## Required Sections (in order)

1. `# <Title>`
2. `## Description` — 2–4 sentences: purpose, where it fits, what the epic enables
3. `## User Stories` — one story per major capability (breadth-first, not depth)
4. `## Features` — ordered list of child features/subtasks with assigned spec numbers
5. `## Diagrams` — connection diagram + flow diagram (high-level user journey)
6. `## Connects To` — upstream and downstream relationships table
7. `## Definition of Done` — verifiable checklist describing the epic's observable outcome

## Conditional Sections

| Section | When present |
|---------|--------------|
| `## Current State` | `mode: rewrite` specs only. Snapshot of existing code — types, responsibilities, integration map. Not a target; carried only for reference. |

## Story Depth

Epic stories are **high-level outcomes** — each will be detailed in child specs. Acceptance criteria can be epic-level (e.g., "users can open a project from a welcome screen"). Detailed AC lives in the child specs that implement each story.

**Generation hint for `build-spec`:** push for **breadth** on epics — one story per major capability. Don't drill into detail; that's the child spec's job.

## Features Section

An ordered list with assigned spec numbers:

```markdown
## Features

| # | Feature | Spec | Scope |
|---|---------|------|-------|
| 1 | <name>  | SPEC-NNN | <1-line scope> |
| 2 | <name>  | SPEC-NNN | <1-line scope> |
```

## What an Epic Does NOT Have

- No `## Technical Requirements` — that's for features/subtasks
- No `## Test Plan` — tests live in child specs
- No `## UI / Mockup` — designs attach to the feature or subtask that implements the screen
- No `## Input / Output` — I/O is defined at the feature/subtask level
