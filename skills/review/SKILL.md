---
name: review
description: Orchestrate parallel reviews across all principles. Prepares input once, then fans out.
argument-hint: [branch|changes|folder|file]
allowed-tools: Read, Glob, Bash, Write
user-invocable: true
---

# Parallel Review Orchestrator

## Input
- RULES_PATH: ${CLAUDE_PLUGIN_ROOT}/references
- OUTPUT_ROOT: CURRENT_PROJECT/.solid_coder/review-<YYYYMMDDhhmmss>

## Phase 1: Discover Principles
- [ ] 1.1 Use skill **solid-coder:discover-principles** with: `--refs-root RULES_PATH`
- [ ] 1.2 Parse JSON output — extract `all_candidate_tags` and the full principle list

## Phase 2: Prepare Input (wait for phase 1)
- [ ] 2.1 Prepare a Task call:
  - subagent_type: `solid-coder:prepare-review-input-agent`
  - prompt:
   ```
    input: $ARGUMENTS
    output_root: {OUTPUT_ROOT}
    candidate_tags: {all_candidate_tags from Phase 1}
    ```
- [ ] 2.2 Launch Task
- [ ] 2.3 From the Task result, extract the output path (review-input.json location in {OUTPUT_ROOT}/prepare)
  - If the Task failed, stop and report the error

## Phase 3: Filter Principles (wait for phase 2)
- [ ] 3.1 Use skill **solid-coder:discover-principles** with: `--refs-root RULES_PATH --review-input {OUTPUT_ROOT}/prepare/review-input.json`
- [ ] 3.2 Use `active_principles` from the output — these are the principles to review

## Phase 4: Launch Parallel Reviews
- [ ] 4.1 For EACH active principle, prepare a Task call:
    - subagent_type: `solid-coder:principle-review-fx-agent`
    - prompt:
      ```
      principle: {NAME}
      review-input: {OUTPUT_ROOT}/prepare/review-input.json
      rules-path: {RULES_PATH}
      principle-folder: {FOLDER from discovery output}
      output-path: {OUTPUT_ROOT}/rules/{NAME}
      ```
- [ ] 4.2 Launch ALL Tasks in a SINGLE message (multiple Task tool calls for parallel execution). Do NOT run in background — all agents must run in foreground to avoid permission issues.
- [ ] 4.3 Wait for all to complete

## Phase 5: Collect Results
- [ ] 5.1 Glob for review output files in .OUTPUT_ROOT/rules/**
- [ ] 5.2 Read each output JSON, extract severity and finding count
- [ ] 5.3 Print summary table:

  | Principle | Severity | Findings | Output Path |
  |-----------|----------|----------|-------------|

- [ ] 5.4 List all output file paths

## Phase 6: Validate Findings (wait for phase 5)
- [ ] 6.1 Prepare a Task call:
  - subagent_type: `solid-coder:validate-findings-agent`
  - prompt:
    ```
    review-input-root: {OUTPUT_ROOT}
    output-root: {OUTPUT_ROOT}
    ```
- [ ] 6.2 Launch Task
- [ ] 6.3 Report validated output paths from `{OUTPUT_ROOT}/by-file/`

## Phase 7: Generate Report (wait for phase 6)
- [ ] 7.1 Prepare a Task call:
  - subagent_type: `solid-coder:generate-report-agent`
  - prompt:
    ```
    output-root: {OUTPUT_ROOT}
    ```
- [ ] 7.2 Launch Task
- [ ] 7.3 Report the path to the generated HTML: `{OUTPUT_ROOT}/report.html`

## Constraints
- Do NOT invent principles — only run reviews for folders that have review/instructions.md
- Do NOT modify any source code files
- Launch ALL reviews in parallel for maximum throughput
- Each review agent is independent — no shared state between principles
- Do NOT auto-resolve issues: if anything fails, report the error
- ALL Task calls must run in foreground (never `run_in_background: true`) — background agents hit permission prompts silently and stall.
