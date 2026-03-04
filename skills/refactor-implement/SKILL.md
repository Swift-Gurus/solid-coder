---
name: refactor-implement
description: Implement refactor suggestions for a single file from validated findings. Reads the by-file output JSON, follows todo items, and applies code changes.
argument-hint: <by-file-json-path> <output-root>
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
user-invocable: false
---

# Refactor Implement

Implements all refactor suggestions for a single source file.

## Input
- BY_FILE_JSON: $ARGUMENTS[0] — path to the validated by-file output JSON (e.g., `.solid_coder/refactor-20260302/1/by-file/MyFile.swift.output.json`)
- OUTPUT_ROOT: $ARGUMENTS[1] — iteration output root (e.g., `.solid_coder/refactor-20260302/1`)

## Phase 1: Load Context

- [ ] 1.1 Read the by-file JSON from $ARGUMENTS[0]
- [ ] 1.2 Extract the `file` path — this is the source file to modify
- [ ] 1.3 Read the source file
- [ ] 1.4 Extract all `principles[].suggestions[]` — these are the changes to implement
- [ ] 1.5 If all principles have severity `COMPLIANT` or suggestions are empty, write a skip entry to the refactor log and stop

## Phase 2: Plan

- [ ] 2.1 For each principle's suggestions, read the `todo_items` array
- [ ] 2.2 Order suggestions by severity: SEVERE > MODERATE > MINOR
- [ ] 2.3 If suggestions from different principles touch overlapping lines, implement higher-severity first
- [ ] 2.4 Create a task list from the ordered todo items

## Phase 3: Implement

FOR each suggestion (in order from Phase 2):
- [ ] 3.1 Read the `suggested_fix` description
- [ ] 3.2 Follow the `todo_items` step by step
- [ ] 3.3 Apply code changes using Edit tool
- [ ] 3.4 After each suggestion, verify the file is syntactically valid (no broken brackets, missing imports)
END

## Phase 4: Write Log

- [ ] 4.1 Write a per-file refactor log to `{OUTPUT_ROOT}/implement/{filename}.refactor-log.json` with:
  ```json
  {
    "file": "<source file path>",
    "timestamp": "<ISO 8601>",
    "suggestions_applied": ["<suggestion-id>", ...],
    "suggestions_skipped": ["<suggestion-id>", ...],
    "errors": ["<description if any>"]
  }
  ```
- [ ] 4.2 Report summary: file path, number of suggestions applied, any errors

## Constraints

- Do NOT modify files other than the target source file
- Do NOT invent changes beyond what the suggestions describe
- Do NOT re-analyze the code for new violations — trust the suggestions
- If a suggestion cannot be applied (e.g., code has changed), skip it and log the reason
- Preserve existing formatting and style conventions of the file
