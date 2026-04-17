# Bug Template

Something broken that needs fixing. Bug specs evolve through two phases — **report** (minimal reproduction artifact) and **ready** (investigation complete, fix planned). Both phases live in the same spec; the spec grows as investigation progresses.

## Two-Phase Lifecycle

| Phase | Status | Purpose |
|-------|--------|---------|
| **Report** | `draft` | Captures what's broken and how to reproduce it. Small, focused. No fix plan yet. |
| **Ready** | `ready` / `in-progress` / `done` | Investigation complete. Root cause identified, fix planned, regression test defined. Now flow-able through `/implement`. |

The spec transitions from **report → ready** by appending sections — never rewriting existing content. The reproduction steps and original symptoms stay intact as historical context.

## Frontmatter

```yaml
---
number: SPEC-NNN
feature: <slug>
type: bug
status: draft          # draft (report) | ready (fix planned) | in-progress | done
parent: SPEC-NNN       # parent spec where the bug lives
blocked-by: []
blocking: []
---
```

---

## Phase 1 — Report (status: `draft`)

Minimal artifact capturing the bug. Kept small on purpose — no diagrams, no fix plan.

### Required Sections (in order)

1. `# <Title>` — describe the bug symptom, not the fix
2. `## Description` — 2–4 sentences: what's broken, where, user impact
3. `## Steps to Reproduce` — numbered list of exact, deterministic steps
4. `## Expected vs Actual` — what should happen vs what does happen
5. `## Affected Component` — which module/file/feature owns the broken behavior

### Conditional Sections

| Section | When |
|---------|------|
| `## UI / Mockup` | If the bug is visual — attach screenshots of the incorrect state to `resources/` |

### Steps to Reproduce

```markdown
## Steps to Reproduce

1. <setup or precondition>
2. <action taken>
3. <action taken>
4. Observe: <the bug symptom>
```

Steps must be **deterministic**. If the bug is intermittent, document the trigger conditions and frequency.

### Expected vs Actual

```markdown
## Expected vs Actual

|          | Behavior |
|----------|----------|
| Expected | <correct behavior> |
| Actual   | <what happens now — the bug> |
```

**Generation hint for `build-spec`:** keep Phase 1 **minimal**. Don't ask for a fix plan — the bug hasn't been investigated yet. Just capture what the reporter knows: symptom, repro, impact.

---

## Phase 2 — Ready (status: `ready` or later)

After investigation, append these sections to the same spec. The spec now contains the full story: report + root cause + fix plan.

### Additional Required Sections (in order, appended after Phase 1 sections)

6. `## Root Cause` — what actually causes the bug. Identifies the responsible code path, missing check, incorrect assumption, race condition, etc.
7. `## Fix Plan` — what will change. Describes the fix behaviorally (not line-by-line): which modules/protocols change, what the corrected flow looks like, any new abstractions.
8. `## Diagrams` — connection + flow diagrams showing the failing path AND the fixed path. Sequence diagram if the bug involves async/multi-actor interactions.
9. `## Test Plan` — must include at least one **regression test** matching the reproduction steps, plus any edge-case tests near the bug.
10. `## Definition of Done` — verifiable checklist including regression test passing.

### Root Cause

```markdown
## Root Cause

<Narrative of what actually causes the bug. Identify the responsible
code path, the missing precondition, or the incorrect assumption.
Not a line-by-line analysis — capture the conceptual fault.>
```

### Fix Plan

```markdown
## Fix Plan

<Describe the fix behaviorally. What changes, what gets added,
what invariant is now enforced. Do NOT write code; do NOT name
specific methods or types unless they already exist.>
```

### Test Plan (regression required)

```markdown
## Test Plan

### Regression Tests
- When <the exact repro condition>, <action>, <the expected correct outcome>

### Related Tests
- When <edge case near the bug>, <action>, <outcome>
```

At least one test case must exactly match the reproduction steps and assert the expected (corrected) behavior.

---

## Why No User Stories

Bugs use reproduction steps instead of user stories. The pipeline treats "Steps to Reproduce + Expected vs Actual" as the requirement — the fix must make those steps produce the expected outcome.

---

## What a Bug Does NOT Have (any phase)

- No `## User Stories` — use Steps to Reproduce instead
- No `## Technical Requirements` — the fix is bounded by the bug, not by new requirements
- No `## Features` list
- No `## Current State` (that's for rewrite epics)
- No `## Input / Output` section — already covered by Affected Component + repro
