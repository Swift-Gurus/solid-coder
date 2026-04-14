---
name: review
description: Orchestrate parallel reviews across all principles. Prepares input once, then fans out.
argument-hint: [branch|changes|folder|file]
allowed-tools: Read, Glob, Bash, Write
user-invocable: true
---

# Parallel Review Orchestrator

## Input
- OUTPUT_ROOT: CURRENT_PROJECT/.solid_coder/review-<YYYYMMDDhhmmss>

## Phase 1: Get Candidate Tags
- [ ] 1.1 Run: `! python3 ${CLAUDE_PLUGIN_ROOT}/mcp-server/gateway.py get_candidate_tags`
- [ ] 1.2 Parse JSON output — store `candidate_tags`

## Phase 2: Prepare Input (wait for phase 1)
- [ ] 2.1 Prepare a Task call:
  - subagent_type: `solid-coder:prepare-review-input-agent`
  - prompt:
   ```
    input: $ARGUMENTS
    output_root: {OUTPUT_ROOT}
    candidate_tags: {candidate_tags from Phase 1}
    ```
- [ ] 2.2 Launch Task
- [ ] 2.3 From the Task result, extract the output path (review-input.json location in {OUTPUT_ROOT}/prepare)
  - If the Task failed, stop and report the error
- [ ] 2.4 Read `{OUTPUT_ROOT}/prepare/review-input.json` and extract `matched_tags`

## Phase 3: Discover Active Principles (wait for phase 2)
- [ ] 3.1 Run: `! python3 ${CLAUDE_PLUGIN_ROOT}/mcp-server/gateway.py discover_principles --matched-tags {matched_tags as comma-separated}`
- [ ] 3.2 Parse JSON output. If `active_principles` is empty → STOP: "No principles active for matched tags"
- [ ] 3.3 Store the `active_principles` list (names only — do NOT load rule content here)

## Phase 4: Launch Parallel Reviews
Each review agent loads its own rules via MCP — the orchestrator does NOT load rule content.

- [ ] 4.1 For EACH active principle, prepare a Task call:
    - subagent_type: `solid-coder:principle-review-fx-agent`
    - prompt:
      ```
      principle: {NAME}
      review-input: {OUTPUT_ROOT}/prepare/review-input.json
      output-path: {OUTPUT_ROOT}/rules/{NAME}
      ```
    The agent will call `mcp__solid-coder__load_rules` with `profile: "review"` and `principle: {NAME}` to load its own rules.
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
- [ ] 6.1 Run: `! python3 ${CLAUDE_PLUGIN_ROOT}/mcp-server/gateway.py validate_findings --output-root {OUTPUT_ROOT}`
- [ ] 6.2 Parse JSON output. If `success` is false → STOP and report the error
- [ ] 6.3 Report validated output paths from `{OUTPUT_ROOT}/by-file/`

## Phase 7: Generate Report (wait for phase 6)
- [ ] 7.1 Run: `! python3 ${CLAUDE_PLUGIN_ROOT}/mcp-server/gateway.py generate_report --output-root {OUTPUT_ROOT}`
- [ ] 7.2 Parse JSON output. If `success` is false → STOP and report the error
- [ ] 7.3 Report the path to the generated HTML: `{OUTPUT_ROOT}/report.html`

## Constraints
- Do NOT invent principles — only run reviews for folders that have review/instructions.md
- Do NOT modify any source code files
- Launch ALL reviews in parallel for maximum throughput
- Each review agent is independent — no shared state between principles
- Do NOT auto-resolve issues: if anything fails, report the error
- ALL Task calls must run in foreground (never `run_in_background: true`) — background agents hit permission prompts silently and stall.
