---
name: refactor
description: Run refactor using SOLID principles. First conducts review of the code, then generates a holistic cross-principle fix plan, then implements it.
argument-hint: [branch|changes|folder|file] [--iterations N] [--verbose]
allowed-tools: Read, Glob, Bash, Write, Edit
user-invocable: true
---

# Refactor Review Orchestrator

## Input
- RULES_PATH: ${CLAUDE_PLUGIN_ROOT}/references
- OUTPUT_ROOT: CURRENT_PROJECT/.solid_coder/refactor-<YYYYMMDDhhmmss>
- MAX_ITERATIONS: 2
- ITERATION: 1 (counter)
- VERBOSE: false

## Timing (verbose only)

When VERBOSE is enabled, capture timestamps at phase boundaries using `date -u +%Y-%m-%dT%H:%M:%SZ` and include them in `refactor-log.json` as the `phase_timings` object. When VERBOSE is off, skip all timestamp captures and omit `phase_timings` from logs.

## Phase 1: Discover Principles
- [ ] 1.1 Parse $ARGUMENTS: extract `--iterations N` if present set MAX_ITERATIONS, else default MAX_ITERATIONS to 2. Extract `--verbose` flag → set VERBOSE.
- [ ] 1.2 Use skill **solid-coder:discover-principles** with: `--refs-root RULES_PATH`
- [ ] 1.3 Parse JSON output — extract `all_candidate_tags` and the full principle list

## Phase 2: Prepare Input (wait for phase 1)
- [ ] 2.1 Prepare a Task call:
  - subagent_type: `solid-coder:prepare-review-input-agent`
  - prompt:
   ```
    input: $ARGUMENTS
    output_root: {OUTPUT_ROOT}/{ITERATION}
    candidate_tags: {all_candidate_tags from Phase 1}
    ```
- [ ] 2.2 Launch Task
- [ ] 2.3 From the Task result, extract the output path (review-input.json location in {OUTPUT_ROOT}/{ITERATION}/prepare)
  - If the Task failed, stop and report the error

## Phase 3: Filter Principles & Launch Reviews (wait for phase 2)

- [ ] 3.0 If VERBOSE: capture timestamp → store as `time_prepare_end` AND `time_review_start`
- [ ] 3.1 Use skill **solid-coder:discover-principles** with: `--refs-root RULES_PATH --review-input {OUTPUT_ROOT}/{ITERATION}/prepare/review-input.json`
- [ ] 3.2 Use `active_principles` from the output — these are the principles to review
- [ ] 3.3 For EACH active principle, prepare a Task call:
    - subagent_type: `solid-coder:apply-principle-review-agent`
    - prompt:
      ```
      principle: {NAME}
      review-input: {OUTPUT_ROOT}/{ITERATION}/prepare/review-input.json
      rules-path: {RULES_PATH}
      principle-folder: {FOLDER from discovery output}
      output-path: {OUTPUT_ROOT}/{ITERATION}/rules/{NAME}
      ```
- [ ] 3.4 Launch ALL Tasks in a SINGLE message (multiple Task tool calls for parallel execution)
- [ ] 3.5 Wait for all to complete

## Phase 4: Collect Results
- [ ] 4.1 Glob for review output files in .OUTPUT_ROOT/{ITERATION}/rules/**
- [ ] 4.2 Read each output JSON, extract severity and finding count
- [ ] 4.3 Print summary table:

  | Principle | Severity | Findings | Output Path |
  |-----------|----------|----------|-------------|

- [ ] 4.4 List all output file paths
- [ ] 4.5 If ALL principles are COMPLIANT (no findings), write summary to `{OUTPUT_ROOT}/{ITERATION}/refactor-log.json` (if VERBOSE: include `phase_timings`). Stop.
- [ ] 4.6 Run: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/validate-findings/scripts/check-severity.py {OUTPUT_ROOT}/{ITERATION}`
  - If output contains `MINOR_ONLY`:
    - Write `{OUTPUT_ROOT}/{ITERATION}/refactor-log.json` with:
      - `status: "all_compliant"`
      - `stop_reason`: the summary line from script output
      - If VERBOSE: include `phase_timings`
      - `minor_findings` array: read each `rules/*/review-output.json`, collect findings with severity MINOR
    - Print summary and STOP (do not proceed to Phase 5)
  - If output contains `HAS_SEVERE`: continue to Phase 5

## Phase 5: Validate Findings (wait for phase 4)
- [ ] 5.0 If VERBOSE: capture timestamp → store as `time_review_end` AND `time_validate_start`
- [ ] 5.1 Prepare a Task call:
  - subagent_type: `solid-coder:validate-findings-agent`
  - prompt:
    ```
    output-root: {OUTPUT_ROOT}/{ITERATION}
    ```
- [ ] 5.2 Launch Task
- [ ] 5.3 Report validated output paths from `{OUTPUT_ROOT}/{ITERATION}/by-file/`

## Phase 6: Holistic Fix Planning (wait for phase 5)

- [ ] 6.0 If VERBOSE: capture timestamp → store as `time_validate_end` AND `time_synthesize_start`
- [ ] 6.1 Prepare a Task call:
  - subagent_type: `solid-coder:synthesize-fixes-agent`
  - prompt:
    ```
    output-root: {OUTPUT_ROOT}/{ITERATION}
    rules-path: {RULES_PATH}
    ```
- [ ] 6.2 Launch Task
- [ ] 6.3 Report synthesized plan paths from `{OUTPUT_ROOT}/{ITERATION}/synthesized/`

## Phase 7: Implement from Plans (wait for phase 6)

- [ ] 7.0 If VERBOSE: capture timestamp → store as `time_synthesize_end` AND `time_implement_start`
- [ ] 7.1 Prepare a Task call:
    - subagent_type: `solid-coder:code-agent`
    - prompt:
      ```
      mode: refactor
      plans-dir: {OUTPUT_ROOT}/{ITERATION}/synthesized
      output-root: {OUTPUT_ROOT}/{ITERATION}
      ```
- [ ] 7.2 Launch Task and wait for completion
- [ ] 7.3 From the Task result, extract the list of files created and modified per plan
- [ ] 7.4 For EACH plan that was implemented, write `{OUTPUT_ROOT}/{ITERATION}/implement/{base-filename}.refactor-log.json`:
  - `base-filename`: derived from the plan JSON filename (e.g., `MyClass` from `MyClass.plan.json`)
  - `file_path`: the target file from the plan JSON's `file_path` field
  - Classify files touched by the implement agent:
    - `files_created`: files that did not exist before implementation (new types, protocols, extracted classes)
    - `files_modified`: pre-existing files changed as side effects (e.g., call site updates) — excludes the target `file_path`
  - Schema:
    ```json
    {
      "file_path": "<target file from plan JSON>",
      "status": "changes_applied | all_compliant",
      "files_created": [],
      "files_modified": [],
      "summary": "<brief description>"
    }
    ```
  - If no changes were needed, set `status: "all_compliant"` and both arrays to `[]`
- [ ] 7.5 Collect all refactor logs from `{OUTPUT_ROOT}/{ITERATION}/implement/*.refactor-log.json`
- [ ] 7.6 If all files were skipped (all compliant), write summary to `{OUTPUT_ROOT}/{ITERATION}/refactor-log.json` and stop
- [ ] 7.7 Write combined Refactor Log — `{OUTPUT_ROOT}/{ITERATION}/refactor-log.json` with summary of all per-file logs:
  ```json
  {
    "iteration": "<ITERATION>",
    "status": "changes_applied | all_compliant",
    "...": "rest of existing fields"
  }
  ```
  If VERBOSE: capture timestamp as `time_implement_end` and include `phase_timings` in the log.
- [ ] 7.8 Collect changed file list for next iteration:
  - From the refactor logs collected in 7.5, collect:
    - Each log's `file_path` (the plan target)
    - Each log's `files_created[]` entries (new types, protocols, extracted classes)
  - Store as CHANGED_FILES (used in Phase 8) — excludes `files_modified[]` (call site side effects don't need re-review)
  - Run: `git add <CHANGED_FILES + all files_modified entries>` (for git hygiene)
- [ ] 7.9 Go to Phase 8

## Phase 8: Iteration loop
- [ ] 8.1 Increment ITERATION counter. If ITERATION > MAX_ITERATIONS provide summary and stop
- [ ] 8.2 Prepare a Task call with `files` to re-review only files modified in the previous iteration:
    - subagent_type: `solid-coder:prepare-review-input-agent`
    - prompt:
   ```
    input: "files" {CHANGED_FILES as space-separated paths}
    output_root: {OUTPUT_ROOT}/{ITERATION}
    candidate_tags: {all_candidate_tags from Phase 1}
    ```
- [ ] 8.3 Launch Task
- [ ] 8.4 From the Task result, extract the output path (review-input.json location in {OUTPUT_ROOT}/{ITERATION}/prepare)
    - If the Task failed, stop and report the error
- [ ] 8.5 If VERBOSE: capture timestamp → store as `time_prepare_start` AND `time_prepare_end`. Go to 3.1


## Constraints

- Do NOT invent principles — only run reviews for folders that have review/instructions.md
- Launch ALL reviews in parallel for maximum throughput
- Each review agent is independent — no shared state between principles
- Do NOT auto-resolve issues: if anything fails, report the error
- Do NOT build the project.
- DO NOT Deviate from the instructions, Follow them thoroughly.
