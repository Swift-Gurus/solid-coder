---
name: implement
description: >-
  Orchestrate implementation of a spec, reads the spec, finds dependencies, plans architecture,
  validates plan with the current codebase, synthesize implementation plan, write code,
  does validation of the implementation with checkpoint asking user validation,
  does on round of refactoring for self-validation
  TRIGGER when: user says "implement spec", "implement" and passes spec file  
argument-hint: <spec-file-path> [--verbose] [--iterations N]
allowed-tools: Read, Glob, Bash, Write, Edit, AskUserQuestion, Skill, TaskCreate, TaskUpdate
user-invocable: true
---

# /implement — Spec-to-Code Orchestrator

Accepts a feature spec file and coordinates sub-skills to architect, validate, synthesize, implement, and review the feature — all in one command.

## Constants

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
- [ ] 0.3 Call `mcp__plugin_solid-coder_specs__parse_spec` with the spec file path. On error, stop and report the message.
- [ ] 0.4 Generate timestamp: run `date -u +%Y%m%d-%H%M%S`
- [ ] 0.5 Set OUTPUT_ROOT to `.solid_coder/implement-{number}-{timestamp}/` (where `{number}` is the frontmatter `number` value)
- [ ] 0.6 Copy the spec file to `{OUTPUT_ROOT}/spec.md`
- [ ] 0.7 Check if a `resources/` directory exists as a sibling of the spec file. If yes, copy it to `{OUTPUT_ROOT}/resources/` (preserving all files — screenshots, schemas, etc.)
- [ ] 0.8 If VERBOSE: initialize `implement-log.json` at `{OUTPUT_ROOT}/implement-log.json` with empty phases array

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
    ```
- [ ] 3.2 Launch Task
- [ ] 3.3 If VERBOSE: capture timestamps and update `implement-log.json` with `{ "phase": "synthesize-implementation", "status": "success" }`
- [ ] 3.4 If the Task failed → report: "Phase 3 (synthesize-implementation) failed: {error}. Run `/synthesize-implementation` manually to debug." STOP.
- [ ] 3.5 Read `{OUTPUT_ROOT}/implementation-plan.json` → extract `matched_tags[]` as comma-separated string. Store as MATCHED_TAGS. If empty or missing, set MATCHED_TAGS to empty string.

## Phase 4: Code Implementation

- [ ] 4.1 Prepare a Task call:
  - subagent_type: `solid-coder:code-agent`
  - prompt:
    ```
    mode: implement
    plan: {OUTPUT_ROOT}/implementation-plan/
    matched-tags: {MATCHED_TAGS}
    ```
- [ ] 4.2 Launch Task
- [ ] 4.3 If VERBOSE: capture timestamps and update `implement-log.json` with `{ "phase": "code", "status": "success" }`
- [ ] 4.4 If the Task failed → report which plan items completed, which failed, and which remain. Do NOT rollback completed items. STOP.

## Phase 5: Validate Implementation
SKIP THIS STEP MOVE TO PHASE 6
- [ ] 5.1 Use skill **solid-coder:validate-implementation** with: `{OUTPUT_ROOT}`
- [ ] 5.2 If result `status` == `"skipped"` or `"approved"` → proceed to Phase 6
- [ ] 5.3 If result `status` == `"has_fixes"`:
  - [ ] 5.3.1 Prepare a Task call:
    - subagent_type: `solid-coder:code-agent`
    - prompt:
      ```
      mode: implement
      plan: {fixes_path}
      ```
  - [ ] 5.3.2 Launch Task
  - [ ] 5.3.3 After fixes applied, ask user: "Fixes applied. Would you like to re-validate, continue to refactor, or stop?"
    - **Re-validate** → return to 5.1 (max 2 re-validates — after that, offer only continue or stop)
    - **Continue** → proceed to Phase 6 with remaining issues noted
    - **Stop** → STOP. Report what was implemented and what design issues remain.
- [ ] 5.4 If VERBOSE: capture timestamps and update `implement-log.json` with `{ "phase": "validate-implementation", "status": "success" }`

## Phase 6: Safety Review (conditional)

- [ ] 6.0 If ITERATIONS == 0: **skip this phase entirely** — go to Phase 7.
- [ ] 6.1 Stage all files created/modified by Phase 4 and 5: run `git add -A` to capture all changes
- [ ] 6.2 Invoke skill **solid-coder:refactor** with: `changes --iterations {ITERATIONS}` (if VERBOSE: append `--verbose`)
- [ ] 6.3 If VERBOSE: capture timestamps and update `implement-log.json` with `{ "phase": "refactor", "status": "success" }`
- [ ] 6.4 If refactor found violations that persist → report remaining violations to the user. This is informational — the implementation is complete.
- [ ] 6.5 If refactor found all code compliant → continue.

## Phase 7: Final Summary

- [ ] 7.1 If VERBOSE: write final `implement-log.json` with all phase entries
- [ ] 7.2 Print summary:
  ```
  /implement complete
  Spec:    {spec file}
  Run:     {OUTPUT_ROOT}
  Phases:  plan ✓ | codebase ✓ | synthesize ✓ | code ✓ | validate ✓ | review ✓
  ```
  (Mark failed/skipped phases accordingly)
- [ ] 7.3 **Cleanup** — only if all phases succeeded: delete the `.solid_coder/` directory in the project root. If any phase failed or stopped early, keep artifacts for debugging.

## Constraints

- The orchestrator NEVER reads phase JSON outputs — it only passes paths forward between phases.
- The orchestrator does NOT loop back to previous phases. The synthesizer reconciles conflicts.
- The orchestrator runs phases 1-4 in sequence. Phase 6 (safety review) runs only when `--iterations N` is set with N > 0.
- Do NOT build the project.
- Do NOT deviate from the instructions. Follow them thoroughly.
- ALL Task calls must run in foreground (never `run_in_background: true`) — background agents hit permission prompts silently and stall.
