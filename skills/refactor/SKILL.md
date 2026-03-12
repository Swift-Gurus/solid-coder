---
name: refactor
description: Run refactor using SOLID principles. First conducts review of the code, then generates a holistic cross-principle fix plan, then implements it.
argument-hint: [branch|changes|folder|file]
allowed-tools: Read, Glob, Bash, Write, Edit
user-invocable: true
---

# Refactor Review Orchestrator

## Input
- RULES_PATH: ${CLAUDE_PLUGIN_ROOT}/references
- OUTPUT_ROOT: CURRENT_PROJECT/.solid_coder/refactor-<YYYYMMDDhhmmss>
- MAX_ITERATIONS: 2
- ITERATION: 1 (counter)

## Timing

At the **start** of each major phase, capture a timestamp by running:
```bash
date -u +%Y-%m-%dT%H:%M:%SZ
```
Store timestamps in memory using these names:
- `time_prepare_start`, `time_prepare_end`
- `time_review_start`, `time_review_end`
- `time_validate_start`, `time_validate_end`
- `time_synthesize_start`, `time_synthesize_end`
- `time_implement_start`, `time_implement_end`

The "end" of one phase equals the "start" of the next (reuse the same timestamp to avoid redundant calls). Include all timestamps in `refactor-log.json` as the `phase_timings` object.

## Phase 1: Discover Principles
- [ ] 1.0 Capture timestamp → store as `time_prepare_start`
- [ ] 1.1 Parse $ARGUMENTS: extract `--iterations N` if present set MAX_ITERATIONS, else default MAX_ITERATIONS to 2
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

- [ ] 3.0 Capture timestamp → store as `time_prepare_end` AND `time_review_start`
- [ ] 3.1 Use skill **solid-coder:discover-principles** with: `--refs-root RULES_PATH --review-input {OUTPUT_ROOT}/{ITERATION}/prepare/review-input.json`
- [ ] 3.2 Use `active_principles` from the output — these are the principles to review
- [ ] 3.3 For EACH active principle, prepare a Task call:
    - subagent_type: `solid-coder:principle-review-agent`
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
- [ ] 4.5 If ALL principles are COMPLIANT (no findings), capture timestamp as `time_review_end`. Write summary to `{OUTPUT_ROOT}/{ITERATION}/refactor-log.json` including `phase_timings` for `prepare` and `review` (set validate/synthesize/implement to `null`). Stop.
- [ ] 4.6 Run: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/validate-findings/scripts/check-severity.py {OUTPUT_ROOT}/{ITERATION}`
  - If output contains `MINOR_ONLY`:
    - Capture timestamp → store as `time_review_end`
    - Write `{OUTPUT_ROOT}/{ITERATION}/refactor-log.json` with:
      - `status: "all_compliant"`
      - `stop_reason`: the summary line from script output
      - `phase_timings` with validate/synthesize/implement set to `null`
      - `minor_findings` array: read each `rules/*/review-output.json`, collect findings with severity MINOR
    - Print summary and STOP (do not proceed to Phase 5)
  - If output contains `HAS_SEVERE`: continue to Phase 5

## Phase 5: Validate Findings (wait for phase 4)
- [ ] 5.0 Capture timestamp → store as `time_review_end` AND `time_validate_start`
- [ ] 5.1 Prepare a Task call:
  - subagent_type: `solid-coder:validate-findings-agent`
  - prompt:
    ```
    output-root: {OUTPUT_ROOT}/{ITERATION}
    ```
- [ ] 5.2 Launch Task
- [ ] 5.3 Report validated output paths from `{OUTPUT_ROOT}/{ITERATION}/by-file/`

## Phase 6: Holistic Fix Planning (wait for phase 5)

- [ ] 6.0 Capture timestamp → store as `time_validate_end` AND `time_synthesize_start`
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

- [ ] 7.0 Capture timestamp → store as `time_synthesize_end` AND `time_implement_start`
- [ ] 7.1 Glob for `{OUTPUT_ROOT}/{ITERATION}/synthesized/*.plan.json`
- [ ] 7.2 For EACH plan JSON, prepare a Task call:
    - subagent_type: `solid-coder:refactor-implement-agent`
    - prompt:
      ```
      plan-json: {OUTPUT_ROOT}/{ITERATION}/synthesized/{filename}.plan.json
      output-root: {OUTPUT_ROOT}/{ITERATION}
      ```
- [ ] 7.3 Launch ALL Tasks in a SINGLE message (multiple Task tool calls for parallel execution)
- [ ] 7.4 Wait for all to complete
- [ ] 7.5 Collect results from `{OUTPUT_ROOT}/{ITERATION}/implement/*.refactor-log.json`
- [ ] 7.6 If all files were skipped (all compliant), write summary to `{OUTPUT_ROOT}/{ITERATION}/refactor-log.json` and stop
- [ ] 7.7 Capture timestamp as `time_implement_end`. Write combined Refactor Log — `{OUTPUT_ROOT}/{ITERATION}/refactor-log.json` with summary of all per-file logs AND phase timings:
  ```json
  {
    "iteration": "<ITERATION>",
    "phase_timings": {
      "prepare":    { "start": "<time_prepare_start>",    "end": "<time_prepare_end>" },
      "review":     { "start": "<time_review_start>",     "end": "<time_review_end>" },
      "validate":   { "start": "<time_validate_start>",   "end": "<time_validate_end>" },
      "synthesize": { "start": "<time_synthesize_start>", "end": "<time_synthesize_end>" },
      "implement":  { "start": "<time_implement_start>",  "end": "<time_implement_end>" }
    },
    "status": "changes_applied | all_compliant",
    "...": "rest of existing fields"
  }
  ```
- [ ] 7.8 Collect changed file list for next iteration:
  - From the refactor logs collected in 7.5, collect:
    - Each log's `file` (the modified source file)
    - Each log's `files_created[]` entries
  - Store this list as CHANGED_FILES (used in Phase 8)
  - Run: `git add <file1> <file2> ...` with all collected paths (for git hygiene)
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
- [ ] 8.5 Capture timestamp → store as `time_prepare_start` AND `time_prepare_end` (Phase 8 replaces Phase 1 for subsequent iterations). Go to 3.1


## Constraints

- Do NOT invent principles — only run reviews for folders that have review/instructions.md
- Launch ALL reviews in parallel for maximum throughput
- Each review agent is independent — no shared state between principles
- Do NOT auto-resolve issues: if anything fails, report the error
- Do NOT build the project.
- DO NOT Deviate from the instructions, Follow them thoroughly.
