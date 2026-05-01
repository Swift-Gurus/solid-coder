# Subtask Template

A scoped unit of work under a parent epic or feature.

## Frontmatter

```yaml
---
number: SPEC-NNN
feature: <slug>
type: subtask
status: draft          # draft | ready | in-progress | done
parent: SPEC-NNN       # parent epic or feature — required
blocked-by: []
blocking: []
mode: rewrite          # optional — only for rewrite subtasks
---
```

## Required Sections (in order)

1. `# <Title>`
2. `## Description` — 2–4 sentences: purpose, where it fits in the parent, what it delivers
3. `## Input / Output` — table of formats and locations
4. `## User Stories` — one story, focused on this subtask's specific deliverable
5. `## Technical Requirements` — APIs, libraries, error codes, patterns, integration points (always required for subtasks)
6. `## Connects To` — upstream and downstream relationships table
7. `## Diagrams` — connection + flow diagrams (sequence if async/multi-actor)
8. `## Test Plan` — grouped by component/screen, covering happy paths and edge cases
9. `## Definition of Done` — verifiable checklist

## Conditional Sections

| Section | When required |
|---------|---------------|
| `## UI / Mockup` | When the subtask touches a screen, view, or user interaction |
| `## Current State` | `mode: rewrite` specs only |

## Story Depth

Subtask stories are **highly specific**. A subtask has one story that focuses on its exact deliverable:

- Placement: where this lives in the codebase
- Connection: how it plugs into parent/sibling specs
- Integration: what APIs, protocols, and types it produces/consumes

Acceptance criteria are the most concrete of any spec type — they should read like a pre-implementation checklist.

**Generation hint for `build-spec`:** push for **specificity** on subtasks — placement, connection, integration details. Ask "which type/protocol/module does this plug into?" — don't accept vague boundaries.

## Scope Metrics

Subtasks are always **leaf** specs — Phase C scope checks always apply. Subtasks cannot be index-only (they have no children).

Formula and bands live in [README § Scope Metrics](../README.md#scope-metrics). Validation runs in [subtask/review/instructions.md § Phase C](review/instructions.md#phase-c--scope--cohesion).

## Technical Requirements

**Always required for subtasks.** Covers:

- APIs and libraries used
- Error codes and error modes
- Patterns (e.g., strategy, decorator, factory)
- Integration points (upstream inputs, downstream consumers)
- Threading/concurrency model
- Performance constraints if any
- Testing strategies, frameworks

Keep this **boundary-focused**: what the subtask must satisfy, not how internal implementation will achieve it. Internal implementation emerges in the arch/implementation plan.

## Input / Output

```markdown
## Input / Output

|   | Detail |
|---|--------|
| Input | <what comes in, format, source> |
| Output | <what goes out, format, destination, who consumes it, lifetime> |
```

## Test Plan Format

```markdown
## Test Plan

### Unit Tests — <ComponentName>
- When <condition>, <action>, <outcome>

### UI Tests — <ScreenName>     (only if UI)
- When <user action>, <system state>, <observable outcome>
```

## What a Subtask Does NOT Have

- No `## Features` list — subtasks are leaves, they don't break further
- No child subtasks — break the work differently if it's too large
- No `## Current State` (unless `mode: rewrite`)
