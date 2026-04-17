---
name: review
description: Run a code review via the refactor pipeline in review-only mode, then produce MD + HTML reports from the review findings and synthesized fix plans.
argument-hint: [changes|folder|file|files|buffer] [target] [--verbose]
allowed-tools: Read, Glob, Bash, Write, Skill
tools: Read, Glob, Bash, Write, Skill
user-invocable: true
---

# Review Orchestrator (thin wrapper)

`/review` runs `/refactor --review-only` then renders MD + HTML reports. All review/synthesis logic lives in `/refactor`; this skill owns only the wiring and reporting.

## Input

- OUTPUT_ROOT: `CURRENT_PROJECT/.solid_coder/review-<YYYYMMDDhhmmss>`

## Phase 1: Stage output root

- [ ] 1.1 Compute TIMESTAMP: `! date +%Y%m%d%H%M%S`
- [ ] 1.2 Set OUTPUT_ROOT to `CURRENT_PROJECT/.solid_coder/review-{TIMESTAMP}`

## Phase 2: Run refactor in review-only mode

- [ ] 2.1 Use skill **solid-coder:refactor** with arguments: `$ARGUMENTS --review-only --output-root {OUTPUT_ROOT}`
  - Refactor runs: discover → prepare → review → validate → synthesize, then stops.
- [ ] 2.2 Wait for refactor to complete. If it failed, stop and report the error.
- [ ] 2.3 Verify `{OUTPUT_ROOT}/1/refactor-log.json` exists. If missing, stop and report.
- [ ] 2.4 Verify `{OUTPUT_ROOT}/1/by-file/` is non-empty (review produced findings). If empty, stop and report.

## Phase 3: Generate reports

- [ ] 3.1 Run: `! python3 ${CLAUDE_PLUGIN_ROOT}/mcp-server/gateway.py generate_report --data-dir {OUTPUT_ROOT} --report-dir {OUTPUT_ROOT}`
  - The script aggregates across ALL iteration subdirs (`1/`, `2/`, ...) and produces one deduplicated report organized by file.
- [ ] 3.2 Parse JSON output. If `success` is false → stop and report the error.
- [ ] 3.3 Report both paths: `{OUTPUT_ROOT}/report.md` and `{OUTPUT_ROOT}/report.html`.

## Constraints

- Do NOT modify any source code files.
- Do NOT invoke any review/synthesis logic directly — delegate to `/refactor`.
- If `/refactor` reports all-compliant and no synthesized plans exist, still generate reports from review findings (MD + HTML will reflect a clean state).
