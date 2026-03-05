---
name: refactor-implement
description: Implement refactor actions from a synthesized fix plan. Reads the plan JSON, follows todo items and suggested fixes, and applies code changes.
argument-hint: <plan-json-path> <output-root>
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
user-invocable: false
---

# Refactor Implement

Implements all refactor actions for a single source file from its synthesized fix plan.

## Input
- PLAN_JSON: $ARGUMENTS[0] — path to the synthesized plan JSON (e.g., `.solid_coder/refactor-20260302/1/synthesized/MyFile.swift.plan.json`)
- OUTPUT_ROOT: $ARGUMENTS[1] — iteration output root (e.g., `.solid_coder/refactor-20260302/1`)

## Phase 1: Load Context

- [ ] 1.1 Read the plan JSON from $ARGUMENTS[0]
- [ ] 1.2 Extract the `file` path — this is the source file to modify
- [ ] 1.3 Read the source file
- [ ] 1.4 Extract the `actions[]` array — these are the changes to implement
- [ ] 1.5 If actions array is empty, write a skip entry to the refactor log and stop

## Phase 2: Plan

- [ ] 2.1 For each action, read the `todo_items` array and `suggested_fix`
- [ ] 2.2 Order actions by `depends_on` graph: actions with no dependencies first, then actions whose dependencies are satisfied
- [ ] 2.3 Within the same dependency level, order by: SEVERE > MODERATE > MINOR
- [ ] 2.4 Create a task list from the ordered actions

## Phase 3: Implement

FOR each action (in order from Phase 2):
- [ ] 3.1 Read the `suggested_fix` description — this contains full code snippets (protocols, types, modified class, before/after)
- [ ] 3.2 Follow the `todo_items` step by step
- [ ] 3.3 Apply code changes using Edit tool
- [ ] 3.4 After each action, verify the file is syntactically valid (no broken brackets, missing imports)
END

## Phase 4: Write Log

- [ ] 4.1 Write a per-file refactor log to `{OUTPUT_ROOT}/implement/{filename}.refactor-log.json` with:
  ```json
  {
    "file": "<source file path>",
    "timestamp": "<ISO 8601>",
    "suggestions_applied": ["<action suggestion_id>", ...],
    "suggestions_skipped": ["<action suggestion_id>", ...],
    "errors": ["<description if any>"]
  }
  ```
- [ ] 4.2 Report summary: file path, number of actions applied, any errors

## Constraints

- Do NOT modify files other than the target source file
- Do NOT invent changes beyond what the actions describe
- Do NOT re-analyze the code for new violations — trust the plan
- If an action cannot be applied (e.g., code has changed), skip it and log the reason
- Preserve existing formatting and style conventions of the file
