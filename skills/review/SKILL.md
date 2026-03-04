---
name: review
description: Orchestrate parallel reviews across all principles. Prepares input once, then fans out.
argument-hint: [branch|changes|folder|file]
allowed-tools: Read, Glob, Bash, Write
---

# Parallel Review Orchestrator

## Input
- RULES_PATH: ${CLAUDE_PLUGIN_ROOT}/references
- OUTPUT_ROOT: CURRENT_PROJECT/.solid_coder/review-<YYYYMMDDhhmmss>

## Phase 1: Prepare Input 
- [ ] 1.1 Prepare a Task call:
  - subagent_type: `prepare-review-input-agent`
  - prompt:
   ```
    input: $ARGUMENTS
    ouput_root: {OUTPUT_ROOT}
    ```
- [ ] 1.2 Launch Task
- [ ] 1.3 From the Task result, extract the output path (review-input.json location in {OUTPUT_ROOT}/prepare)
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
      output-path: {OUTPUT_ROOT}/rules/{NAME}
      ```
- [ ] 3.2 Launch ALL Tasks in a SINGLE message (multiple Task tool calls for parallel execution)
- [ ] 3.3 Wait for all to complete

## Phase 4: Collect Results
- [ ] 4.1 Glob for review output files in .OUTPUT_ROOT/rules/**
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
    review-input-root: {OUTPUT_ROOT}
    output-root: {OUTPUT_ROOT}
    ```
- [ ] 5.2 Launch Task
- [ ] 5.3 Report validated output paths from `{OUTPUT_ROOT}/by-file/`

## Phase 6: Generate Report (wait for phase 5)
- [ ] 6.1 Prepare a Task call:
  - subagent_type: `solid-coder:generate-report-agent`
  - prompt:
    ```
    output-root: {OUTPUT_ROOT}
    ```
- [ ] 6.2 Launch Task
- [ ] 6.3 Report the path to the generated HTML: `{OUTPUT_ROOT}/report.html`

## Constraints
- Do NOT invent principles — only run reviews for folders that have review/instructions.md
- Do NOT modify any source code files
- Launch ALL reviews in parallel for maximum throughput
- Each review agent is independent — no shared state between principles
- Do NOT auto-resolve issues: if anything fails, report the error
