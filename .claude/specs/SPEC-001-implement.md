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

The `/implement` skill is the top-level orchestrator. It does not write code itself — it coordinates three sub-skills in sequence and feeds each phase's JSON output into the next.

## Flow

```
User provides: spec (markdown)
                │
                ▼
┌──────────────────────────┐
│  Phase 1: /plan          │  ← SPEC-002
│  (Architect)             │
│  Input:  spec            │
│  Output: arch.json       │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  Phase 2: /validate-plan │  ← SPEC-003
│  (Validator)             │
│  Input:  spec, arch.json │
│  Output: validation.json │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  Phase 3: /synthesize-   │  ← SPEC-004
│  implementation          │
│  (Synthesizer)           │
│  Input:  spec,           │
│          arch.json,      │
│          validation.json │
│  Output: plan.json       │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  Phase 4: /code          │  (existing skill)
│  Input:  plan.json       │
│  Output: source files    │
└──────────────────────────┘
```

## Requirements

### REQ-1: Orchestrator Flow

- REQ-1.1: `/implement` is user-invocable. It accepts a path to a spec file (markdown or JSON) or inline prompt.
- REQ-1.2: Each phase runs as a sub-skill invocation. The orchestrator passes outputs between phases — no phase reads from a previous phase's artifacts directly.
- REQ-1.3: Each phase produces a JSON artifact saved to a run folder: `.solid_coder/implement-{spec-number}{timestamp}/`.
- REQ-1.4: If any phase fails or returns an error state, the orchestrator stops and reports which phase failed and why.
- REQ-1.5: The orchestrator does NOT loop back to previous phases. The synthesizer reconciles any conflicts between architecture and validation findings.

### REQ-2: Artifact Management

- REQ-2.1: Run folder structure:
  ```
  .solid_coder/implement-{spec-number}-{timestamp}/
    spec.md              (copy of input spec)
    arch.json            (Phase 1 output)
    validation.json      (Phase 2 output)
    plan.json            (Phase 3 output)
    implement-log.json   (orchestrator log with phase timings, status)
  ```
- REQ-2.2: `implement-log.json` follows the same structure as `refactor-log.json` — phase timings, status, summary.

### REQ-3: Input Handling

- REQ-3.1: If input is a markdown file → pass as-is to Phase 1.
- REQ-3.2: If input is an inline prompt → wrap into a minimal spec structure before passing to Phase 1.

### Edge Cases

- EC-1: Spec references types that don't exist yet AND types that do exist — the validator must handle mixed create/reuse scenarios.
- EC-2: Architect proposes a component that is redundant with an existing one — the synthesizer must reconcile (prefer existing, document decision).
- EC-3: Spec is vague or underspecified — the architect should produce the decomposition based on what's given, not block. The synthesizer can flag gaps.
- EC-4: `/code` fails on a plan item — the orchestrator reports which item failed. No automatic retry in v1.

## Definition of Done

- [ ] `/implement` skill exists with `user-invocable: true`
- [ ] Accepts a spec file path or inline prompt as argument
- [ ] Invokes Phase 1–4 in sequence, passing JSON paths between phases, no loading into memory
- [ ] Saves all artifacts to `.solid_coder/implement-{spec-number}{timestamp}/`
- [ ] Produces `implement-log.json` with phase timings and status
- [ ] Stops and reports on phase failure
- [ ] End-to-end test: given a feature spec, produces working source files with solid-frontmatter
