---
name: refactor
description: Run refactor using SOLID principles. First conducts review of the code, suggest fixes, then implement them.
argument-hint: [branch|changes|folder|file]
allowed-tools: Read, Glob, Bash, Write, Edit
---

# Refactor Review Orchestrator

## Input
- RULES_PATH: ${CLAUDE_PLUGIN_ROOT}/references
- OUTPUT_ROOT: CURRENT_PROJECT/.solid_coder/refactor-<YYYYMMDDhhmmss>
- MAX_ITERATIONS: 2                                                                                                                                                                                                                                                                            
- ITERATION: 1 (counter)

## Phase 1: Prepare Input 
- [ ] 1.1 Parse $ARGUMENTS: extract `--iterations N` if present set MAX_ITERATIONS, else default MAX_ITERATIONS to 2
- [ ] 1.2 Prepare a Task call:
  - subagent_type: `prepare-review-input-agent`
  - prompt:
   ```
    input: $ARGUMENTS
    output_root: {OUTPUT_ROOT}/{ITERATION}
    ```
- [ ] 1.3 Launch Task
- [ ] 1.4 From the Task result, extract the output path (review-input.json location in {OUTPUT_ROOT}/{ITERATION}/prepare)
  - If the Task failed, stop and report the error

## Phase 2: Discover Principles (wait for phase 1)
- [ ] 2.1 Glob for `RULES_PATH/**/review/instructions.md`
- [ ] 2.2 Extract principle abbreviation from each path (directory name: SRP, OCP, etc.)
- [ ] 2.3 Build list of principles to review

## Phase 3: Launch Parallel Reviews (Review loop)

- [ ] 3.1 For EACH discovered principle, prepare a Task call:
    - subagent_type: `solid-coder:principle-review-fx-agent`
    - prompt:
      ```
      principle: {NAME}
      review-input: {{OUTPUT_ROOT}/{ITERATION}/prepare/review-input.json }
      rules-path: {RULES_PATH}
      principle-folder: {RULES_PATH}/{NAME}
      output-path: {OUTPUT_ROOT}/{ITERATION}/rules/{NAME}
      ```
- [ ] 3.2 Launch ALL Tasks in a SINGLE message (multiple Task tool calls for parallel execution)
- [ ] 3.3 Wait for all to complete

## Phase 4: Collect Results
- [ ] 4.1 Glob for review output files in .OUTPUT_ROOT/{ITERATION}/rules/**
- [ ] 4.2 Read each output JSON, extract severity and finding count
- [ ] 4.3 Print summary table:

  | Principle | Severity | Findings | Output Path |
  |-----------|----------|----------|-------------|

- [ ] 4.4 List all output file paths

## Phase 5: Validate Findings (wait for phase 4)
- [ ] 5.1 Prepare a Task call:
  - subagent_type: `solid-coder:validate-findings-agent`
  - prompt:
    ```
    output-root: {OUTPUT_ROOT}/{ITERATION}
    ```
- [ ] 5.2 Launch Task
- [ ] 5.3 Report validated output paths from `{OUTPUT_ROOT}/{ITERATION}/by-file/`


## Phase 6: Implement suggestions (wait for phase 5)

- [ ] 6.1 Glob for `{OUTPUT_ROOT}/{ITERATION}/by-file/*.output.json`
- [ ] 6.2 For EACH by-file output JSON, prepare a Task call:
    - subagent_type: `solid-coder:refactor-implement-agent`
    - prompt:
      ```
      by-file-json: {OUTPUT_ROOT}/{ITERATION}/by-file/{filename}.output.json
      output-root: {OUTPUT_ROOT}/{ITERATION}
      ```
- [ ] 6.3 Launch ALL Tasks in a SINGLE message (multiple Task tool calls for parallel execution)
- [ ] 6.4 Wait for all to complete
- [ ] 6.5 Collect results from `{OUTPUT_ROOT}/{ITERATION}/implement/*.refactor-log.json`
- [ ] 6.6 If all files were skipped (all compliant), write summary to `{OUTPUT_ROOT}/{ITERATION}/refactor-log.json` and stop
- [ ] 6.7 Write combined Refactor Log — `{OUTPUT_ROOT}/{ITERATION}/refactor-log.json` with summary of all per-file logs
- [ ] 6.8 Go to Phase 7

## Phase 7: Iteration loop 
- [ ] 7.1 Increment ITERATION counter. If ITERATION > MAX_ITERATIONS provide summary and stop
- [ ] 7.2 Prepare a Task call with `changes` to re-review only staged/unstaged/untracked files:
    - subagent_type: `prepare-review-input-agent`
    - prompt:
   ```
    input: "changes"
    output_root: {OUTPUT_ROOT}/{ITERATION}
    ```
- [ ] 7.3 Launch Task
- [ ] 7.4 From the Task result, extract the output path (review-input.json location in {OUTPUT_ROOT}/{ITERATION}/prepare)
    - If the Task failed, stop and report the error
- [ ] 7.5 go to 3.1

  
## Constraints

- Do NOT invent principles — only run reviews for folders that have review/instructions.md
- Launch ALL reviews in parallel for maximum throughput
- Each review agent is independent — no shared state between principles
- Do NOT auto-resolve issues: if anything fails, report the error
- Do NOT build the project.
- DO NOT Deviate from the instructions, Follow them thoroughly.
