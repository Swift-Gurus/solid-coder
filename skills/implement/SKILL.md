---
name: implement
description: Spec-to-code orchestrator — architects, validates, synthesizes, implements, and reviews a feature from a spec file.
argument-hint: <spec-file-path> [--verbose] [--iterations N]
allowed-tools: Read, Glob, Bash, Write, Edit
user-invocable: true
---

# /implement — Spec-to-Code Orchestrator

Accepts a feature spec file and coordinates sub-skills to architect, validate, synthesize, implement, and review the feature — all in one command.

## Constants

- RULES_PATH: ${CLAUDE_PLUGIN_ROOT}/references
- OUTPUT_ROOT: CURRENT_PROJECT/.solid_coder/implement-{spec-number}-<YYYYMMDDhhmmss>

## Input

- SPEC_FILE: $ARGUMENTS[0] — path to a markdown spec file with YAML frontmatter (must contain at least a `number` field)
- --verbose: (optional) Enable per-phase timing and `implement-log.json` output. Default: off.
- --iterations N: (optional) Number of post-implementation refactor iterations. Default: 1. Use 0 to skip safety review.

## Phase 0: Validate Input & Setup

- [ ] 0.1 Parse $ARGUMENTS — extract the spec file path and flags. If no spec file provided, fail with: "Input must be a spec file with frontmatter. Use `/build-spec` to create one."
  - Set VERBOSE = true if `--verbose` is present, false otherwise
  - Set ITERATIONS = N if `--iterations N` is present, 1 otherwise
- [ ] 0.2 Verify the file exists and ends in `.md`. If not, fail with the same message as 0.1.
- [ ] 0.3 Use skill **solid-coder:parse-frontmatter** to extract YAML frontmatter from the spec file. Verify it contains a `number` field. If not, fail with the same message as 0.1.
- [ ] 0.4 Generate timestamp: run `date -u +%Y%m%d-%H%M%S`
- [ ] 0.5 Set OUTPUT_ROOT to `.solid_coder/implement-{number}-{timestamp}/` (where `{number}` is the frontmatter `number` value)
- [ ] 0.6 Copy the spec file to `{OUTPUT_ROOT}/spec.md`
- [ ] 0.7 If VERBOSE: initialize `implement-log.json` at `{OUTPUT_ROOT}/implement-log.json` with empty phases array

## Phase 1: Architecture Decomposition

- [ ] 1.1 Prepare a Task call:
  - subagent_type: `solid-coder:plan-agent`
  - prompt:
    ```
    spec: {OUTPUT_ROOT}/spec.md
    output: {OUTPUT_ROOT}/arch.json
    ```
- [ ] 1.2 Launch Task
- [ ] 1.3 If VERBOSE: capture timestamps and update `implement-log.json` with `{ "phase": "plan", "status": "success" }`
- [ ] 1.4 If the Task failed → report: "Phase 1 (plan) failed: {error}. Run `/plan` manually to debug." STOP.

## Phase 2: Codebase Validation

- [ ] 2.1 Prepare a Task call:
  - subagent_type: `solid-coder:validate-plan-agent`
  - prompt:
    ```
    arch-json: {OUTPUT_ROOT}/arch.json
    output: {OUTPUT_ROOT}/validation.json
    ```
- [ ] 2.2 Launch Task
- [ ] 2.3 If VERBOSE: capture timestamps and update `implement-log.json` with `{ "phase": "validate-plan", "status": "success" }`
- [ ] 2.4 If the Task failed → report: "Phase 2 (validate-plan) failed: {error}. Run `/validate-plan` manually to debug." STOP.

## Phase 3: Synthesize Implementation Plan

- [ ] 3.1 Prepare a Task call:
  - subagent_type: `solid-coder:synthesize-implementation-agent`
  - prompt:
    ```
    arch-json: {OUTPUT_ROOT}/arch.json
    validation-json: {OUTPUT_ROOT}/validation.json
    output: {OUTPUT_ROOT}/implementation-plan.json
    refs-root: {RULES_PATH}
    ```
- [ ] 3.2 Launch Task
- [ ] 3.3 If VERBOSE: capture timestamps and update `implement-log.json` with `{ "phase": "synthesize-implementation", "status": "success" }`
- [ ] 3.4 If the Task failed → report: "Phase 3 (synthesize-implementation) failed: {error}. Run `/synthesize-implementation` manually to debug." STOP.

## Phase 4: Code Implementation

- [ ] 4.1 Prepare a Task call:
  - subagent_type: `solid-coder:code-agent`
  - prompt:
    ```
    mode: implement
    plan: {OUTPUT_ROOT}/implementation-plan.json
    ```
  The code-agent reads the plan, iterates over `plan_items[]` in order (respecting `depends_on`), and executes each directive. Do NOT iterate plan items yourself — the code-agent handles this.
- [ ] 4.2 Launch Task
- [ ] 4.3 If VERBOSE: capture timestamps and update `implement-log.json` with `{ "phase": "code", "status": "success" }`
- [ ] 4.4 If the Task failed → report which plan items completed, which failed, and which remain. Suggestion: "You can re-run `/code` with the remaining items or fix the issue and retry." Do NOT rollback already-completed items. STOP.

## Phase 5: Safety Review (conditional)

- [ ] 5.0 If ITERATIONS == 0: **skip this phase entirely** — go to Phase 6.
- [ ] 5.1 Stage all files created/modified by Phase 4: run `git add -A` to capture all changes
- [ ] 5.2 Invoke skill **solid-coder:refactor** with: `changes --iterations {ITERATIONS}` (if VERBOSE: append `--verbose`)
- [ ] 5.3 If VERBOSE: capture timestamps and update `implement-log.json` with `{ "phase": "refactor", "status": "success" }`
- [ ] 5.4 If refactor found violations that persist → report remaining violations to the user. This is informational — the implementation is complete.
- [ ] 5.5 If refactor found all code compliant → continue.

## Phase 6: Final Summary

- [ ] 6.1 If VERBOSE: write final `implement-log.json` with all phase entries
- [ ] 6.2 Print summary:
  ```
  /implement complete
  Spec:    {spec file}
  Run:     {OUTPUT_ROOT}
  Phases:  plan ✓ | validate ✓ | synthesize ✓ | code ✓ | review ✓
  ```
  (Mark failed/skipped phases accordingly)

## Constraints

- The orchestrator NEVER reads phase JSON outputs — it only passes paths forward between phases.
- The orchestrator does NOT loop back to previous phases. The synthesizer reconciles conflicts.
- The orchestrator runs phases 1-4 in sequence. Phase 5 (safety review) runs only when `--iterations N` is set with N > 0.
- Do NOT build the project.
- Do NOT deviate from the instructions. Follow them thoroughly.
