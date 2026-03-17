---
number: SPEC-001
feature: implement
status: draft
blocked-by: [SPEC-002, SPEC-003, SPEC-004]
blocking: []
---

# /implement — Spec-to-Code Orchestrator

## Description

As a user, I want to provide a feature spec and have the system architect a solution, validate it against my existing codebase, synthesize a concrete implementation plan, and execute it — all in one command.

The `/implement` skill is the top-level orchestrator. It does not write code itself — it coordinates sub-skills in sequence, passing JSON artifact **paths** between phases. The orchestrator never reads phase outputs — it only passes paths forward.

## Constants

- `RULES_PATH`: `${CLAUDE_PLUGIN_ROOT}/references` — principle references directory, passed to phases that need it
- `RUN_ROOT`: `.solid_coder/implement-{spec-number}-{timestamp}/` — run artifact directory

## Flow

```
User provides: spec (markdown or prompt)
                │
                ▼
┌──────────────────────────────────┐
│  Phase 1: /plan                  │  ← SPEC-002
│  Input:  spec, --output          │
│  Output: arch.json               │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  Phase 2: /validate-plan         │  ← SPEC-003
│  Input:  arch.json, --output     │
│  Output: validation.json         │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  Phase 3: /synthesize-           │  ← SPEC-004
│  implementation                  │
│  Input:  arch.json,              │
│          validation.json,        │
│          --output, --refs-root   │
│  Output: implementation-plan.json│
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  Phase 4: code-agent             │  (existing agent)
│  Input:  implementation-plan.json│
│  Output: source files            │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  Phase 5: /refactor              │  (safety check)
│  Input:  staged files from Ph.4  │
│  Output: review + fixes          │
└──────────────────────────────────┘
```

## Requirements

### REQ-1: Orchestrator Flow

- REQ-1.1: `/implement` is user-invocable. It accepts a path to a spec file (markdown) or inline prompt.
- REQ-1.2: Each phase runs as a sub-skill or agent invocation. The orchestrator passes artifact **paths** between phases — it does not read or interpret the JSON artifacts itself.
- REQ-1.3: Each phase produces a JSON artifact saved to `RUN_ROOT`.
- REQ-1.4: The orchestrator does NOT loop back to previous phases. The synthesizer reconciles any conflicts between architecture and validation findings.

### REQ-2: Phase Invocations

- REQ-2.1: **Phase 1** — invoke skill **solid-coder:plan** with: `<spec> --output {RUN_ROOT}/arch.json`
- REQ-2.2: **Phase 2** — invoke skill **solid-coder:validate-plan** with: `{RUN_ROOT}/arch.json --output {RUN_ROOT}/validation.json`
- REQ-2.3: **Phase 3** — invoke skill **solid-coder:synthesize-implementation** with: `{RUN_ROOT}/arch.json {RUN_ROOT}/validation.json --output {RUN_ROOT}/implementation-plan.json --refs-root {RULES_PATH}`
- REQ-2.4: **Phase 4** — spawn `code-agent` with prompt: the path to `{RUN_ROOT}/implementation-plan.json`. The code-agent reads the plan, iterates over `plan_items[]` in order (respecting `depends_on`), and executes each directive. The orchestrator does not iterate plan items itself.
- REQ-2.5: **Phase 5** — safety review of implemented code. Stage all files created/modified by Phase 4 (`git add <files>`), then invoke skill **solid-coder:refactor** with: `changes --iterations 1`. This runs a single-pass review/fix cycle on the staged changes — the same principle-driven review loop that `/refactor` uses, limited to one iteration. If violations are found, `/refactor` fixes them inline. If violations remain after the single pass, they are reported to the user (same behavior as `/refactor` hitting its iteration limit).

### REQ-3: Artifact Management

- REQ-3.1: Run folder structure:
  ```
  .solid_coder/implement-{spec-number}-{timestamp}/
    spec.md                    (copy of input spec)
    arch.json                  (Phase 1 output)
    validation.json            (Phase 2 output)
    implementation-plan.json   (Phase 3 output)
    refactor-<timestamp>/      (Phase 5 output — /refactor's own run folder)
    implement-log.json         (orchestrator log)
  ```
- REQ-3.2: `implement-log.json` records per-phase: start time, end time, status (`success`|`failed`|`skipped`), and error message if failed.

### REQ-4: Input Handling

- REQ-4.1: If input is a markdown file → copy to `{RUN_ROOT}/spec.md`, pass path to Phase 1.
- REQ-4.2: If input is an inline prompt → write to `{RUN_ROOT}/spec.md` as minimal markdown, pass path to Phase 1.

### REQ-5: Error Handling

- REQ-5.1: If Phase 1, 2, or 3 fails → stop execution. Record failure in `implement-log.json`. Report which phase failed, the error, and what the user can do (e.g., "Phase 2 failed: validation found no codebase files with solid-frontmatter. Run `/validate-plan` manually to debug.").
- REQ-5.2: If Phase 4 (code-agent) fails on a plan item → do NOT rollback already-completed items. Stop and report:
  - Which plan items completed successfully
  - Which plan item failed and why
  - Remaining plan items not yet attempted
  - Suggestion: "You can re-run `/code` with the remaining items or fix the issue and retry."
- REQ-5.3: Record partial completion state in `implement-log.json` so the user can see progress.
- REQ-5.4: If Phase 5 (`/refactor`) finds violations that persist after its single pass, report them to the user with the refactor output path. This is informational — the implementation is complete, but the user should review the remaining violations.

### Edge Cases

- EC-1: Spec references types that don't exist yet AND types that do exist — the validator handles mixed create/reuse scenarios.
- EC-2: Architect proposes a component that is redundant with an existing one — the synthesizer reconciles (prefer existing, document decision).
- EC-3: Spec is vague or underspecified — the architect produces the decomposition based on what's given, doesn't block. The synthesizer can flag gaps.
- EC-4: All components already exist (`reuse`) — `implementation-plan.json` has zero plan items. Phase 4 and 5 are skipped. Report "All components already exist — nothing to implement."
- EC-5: Phase 5 finds all code COMPLIANT — `/refactor` reports clean and stops early. Log as success.

## Definition of Done

- [ ] `/implement` skill exists with `user-invocable: true`
- [ ] Accepts a spec file path or inline prompt as argument
- [ ] Invokes Phase 1–5 in sequence, passing artifact paths between phases
- [ ] Orchestrator never reads phase JSON outputs — only passes paths
- [ ] Saves all artifacts to `RUN_ROOT`
- [ ] Produces `implement-log.json` with per-phase timing and status
- [ ] On phase failure: stops, reports actionable guidance
- [ ] On code-agent partial failure: preserves completed work, reports remaining items
- [ ] Handles zero plan items (all reuse) by skipping Phase 4 and 5
- [ ] Phase 5 stages changes and runs `/refactor changes --iterations 1` as safety check
- [ ] End-to-end: given a feature spec, produces working source files with solid-frontmatter
