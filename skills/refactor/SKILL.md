---
name: refactor
description: Run refactor using SOLID principles. First conducts review of the code, suggest fixes, then implement them.
argument-hint: [branch|folder|file]
allowed-tools: Read, Glob, Bash, Write, Edit
---

# Refactor Review Orchestrator

## Input
- RULES_PATH: ${CLAUDE_PLUGIN_ROOT}/references
- OUTPUT_ROOT: CURRENT_PROJECT/.solid_coder/refactor-<YYYYMMDDhhmmss>
- MAX_ITERATIONS: 2                                                                                                                                                                                                                                                                            
- ITERATION: 0 (counter)
## Phase 1: Prepare Input (Review loop)
- [ ] 1.1 Parse $ARGUMENTS: extract `--iterations N` if present set MAX_ITERATIONS, else default MAX_ITERATIONS to 2
- [ ] 1.2 Increment ITERATION counter. If ITERATION > MAX_ITERATIONS go to Phase 6
- [ ] 1.3 Prepare a Task call:
  - subagent_type: `prepare-review-input-agent`
  - prompt:
   ```
    input: $ARGUMENTS
    ouput_root: {OUTPUT_ROOT}
    ```
- [ ] 1.3 Launch Task
- [ ] 1.4 From the Task result, extract the output path (review-input.json location in {OUTPUT_ROOT}/prepare)
  - If the Task failed, stop and report the error

## Phase 2: Discover Principles (wait for phase 1)
- [ ] 2.1 Glob for `RULES_PATH/**/review/instructions.md`
- [ ] 2.2 Extract principle abbreviation from each path (directory name: SRP, OCP, etc.)
- [ ] 2.3 Build list of principles to review

## Phase 3: Launch Parallel Reviews 

- [ ] 3.1 For EACH discovered principle, prepare a Task call:
    - subagent_type: `solid-coder:principle-review-fx-agent`
    - prompt:
      ```
      principle: {NAME}
      review-input: {$ARGUMENTS[1]}
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
FOR every plan file in `{OUTPUT_ROOT}/{ITERATION}/by-file/` DO
- [ ] 6.1 Read the principles[].suggestions[] for this file
  - if suggestions are empty, or all principles compliant  Write Refactor Log — `{OUTPUT_ROOT}/{ITERATION}/refactor-log.json` with summary and stop.
- [ ] 6.2 Read todo items
- [ ] 6.3 Create task lists
- [ ] 6.4 Follow the task list to implement suggestions
- [ ] 6.5 Write Refactor Log — `{OUTPUT_ROOT}/{ITERATION}/refactor-log.json` with summary
- [ ] 6.6 Go to 3.1
END

  
## Constraints

- Do NOT invent principles — only run reviews for folders that have review/instructions.md
- Launch ALL reviews in parallel for maximum throughput
- Each review agent is independent — no shared state between principles
- Do NOT auto-resolve issues: if anything fails, report the error
- Do NOT build the project.
