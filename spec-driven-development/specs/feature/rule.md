# Feature Template

A new capability or improvement to existing behavior.

## Frontmatter

```yaml
---
number: SPEC-NNN
feature: <slug>
type: feature
status: draft          # draft | ready | in-progress | done
parent: SPEC-NNN       # parent epic (or root)
blocked-by: []
blocking: []
mode: rewrite          # optional — only for rewrite features from build-spec-from-code
---
```

## Required Sections (in order)

1. `# <Title>`
2. `## Description` — 2–4 sentences: purpose, what the feature enables, where it fits
3. `## Input / Output` — table of formats and locations for what goes in and comes out
4. `## User Stories` — 1–3 stories with independently verifiable acceptance criteria
5. `## Connects To` — upstream and downstream relationships table
6. `## Diagrams` — connection + flow diagrams (sequence if async/multi-actor)
7. `## Definition of Done` — verifiable checklist

## Conditional Sections

| Section                     | When required                                                                                  |
| --------------------------- | ---------------------------------------------------------------------------------------------- |
| `## Technical Requirements` | When touching business logic, integration, APIs, or external systems                           |
| `## UI / Mockup`            | When description or stories mention screens, views, components, or user interaction            |
| `## Test Plan`              | When behavior is testable (almost always — only skip for pure internal/infrastructure stories) |
| `## Current State`          | `mode: rewrite` specs only                                                                     |

## Story Depth

Feature stories are **concrete and independently verifiable**. Push for specific acceptance criteria:

- Each criterion must name a specific value, behavior, or condition
- No "works correctly", "handles edge cases", "behaves as expected"
- Edge cases and design choices are captured as acceptance criteria on the relevant story (not a separate section)

**Generation hint for `build-spec`:** push for **concrete ACs** on features. Don't accept "system handles errors" — ask which errors, and what happens for each.

## Scope Metrics

A feature is treated as **leaf** (Phase C scope checks apply) unless it has a `## Subtasks` section AND no `## Technical Requirements` AND no own acceptance criteria — in which case it's an **index** for its subtasks and is exempt.

Formula and bands live in [README § Scope Metrics](../README.md#scope-metrics). Validation runs in [feature/review/instructions.md § Phase C](review/instructions.md#phase-c--scope--cohesion).

## Input / Output

```markdown
## Input / Output

|   | Detail |
|---|--------|
| Input | <what comes in, format, source> |
| Output | <what goes out, format, destination, who consumes it, lifetime> |
```

The consumer contract matters — who holds the output, how they receive it (init injection, environment, closure, return), and how long it lives.

## Test Plan Format

Group by component or screen:

```markdown
## Test Plan

### Unit Tests — <ComponentName>
- When <condition>, <action>, <outcome>
- When <condition>, <action>, <outcome>

### UI Tests — <ScreenName>
- When <user action>, <system state>, <observable outcome>
```

## What a Feature Does NOT Have

- No `## Features` list — features don't break into child features (use subtasks for that)
- No `## Current State` (unless `mode: rewrite`)
