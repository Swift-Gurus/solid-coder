---
name: fix-suggest
description: Generate fix suggestions from review findings. Reads findings JSON, source code, and principle-specific fix instructions to produce refactoring suggestions.
argument-hint: <principle-folder> <findings-json> <code-files>
allowed-tools: Read, Grep, Glob, Bash, Write
user-invocable: false
---

# Fix Suggestion Generator

## Input
- GATEWAY: ${CLAUDE_PLUGIN_ROOT}/mcp-server/gateway.py
- Principle name: $ARGUMENTS[0]
- Findings JSON: $ARGUMENTS[1] (e.g., .solid-coder/review-20260215-002137/SRP/output.json)
- Code files: remaining arguments

## Workflow

## Phase 1: Preparation
Create Preparation task list and execute it
- [ ] 1.1 **Load principle rules** — Run:
  `! python3 {GATEWAY} load_rules --profile code --principle {$ARGUMENTS[0]}`
  Parse JSON output — `rules[NAME]` contains `rule`, `instructions` (fix), `examples`, `patterns`.
- [ ] 1.2 **Load findings** — Read the findings JSON from $ARGUMENTS[1]
- [ ] 1.7 **Load source code** — Read each code file from remaining arguments

## Phase 2: Analysis
Creating/appending tasks from the fix instructions.
Once you read fix instructions, rules, and findings, they contain more tasks.
Create a second tasklist and execute it

## Phase 3: Output
- [ ] 3.1 **Load output schema** — Read the schema file path from step 1.1
- [ ] 3.2 **Generate output** — Produce JSON matching the output schema, write to `fix.json` into the same folder where findings are $ARGUMENTS[1]

## Constraints
- Do NOT invent fixes — base suggestions on findings data and fix instruction patterns
- Do NOT re-analyze the code for violations — trust the review findings
- Reference finding IDs (e.g., srp-001) in the `addresses` field of each fix
- Each fix should produce compilable code (before/after)
- Prefer minimal changes that address the most findings
