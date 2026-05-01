---
name: scope-synthesize
description: Merge heuristic.json, skeleton.json, and cohesion.json into a single scope-assessment.json with verdict and split candidates. Internal skill — invoked by validate-spec Phase C after the three measurement subagents complete.
argument-hint: <output-dir>
allowed-tools: Bash
user-invocable: false
---

# Scope Synthesize

## Input

- OUTPUT_DIR: `$ARGUMENTS[0]` — directory containing `heuristic.json`, `skeleton.json`, and `cohesion.json` produced by the three measurement subagents. The synthesis writes `scope-assessment.json` to the same directory.
- SKILL_ROOT: `${CLAUDE_PLUGIN_ROOT}/skills/scope-synthesize`

## Workflow

- [ ] 1.1 Run the synthesis script:
    ```bash
    python3 {SKILL_ROOT}/scripts/synthesize-scope.py {OUTPUT_DIR}
    ```
- [ ] 1.2 Report the verdict (`compliant` / `advisory` / `needs_split`), consensus LOC, cohesion group count, and split-recommendation summary from `{OUTPUT_DIR}/scope-assessment.json`.
- [ ] 1.3 If the script exits non-zero, fail with the script's error message.

## Output

`{OUTPUT_DIR}/scope-assessment.json` matching `output.schema.json`. This is the **public contract** for downstream consumers — validate-spec Phase 4 turns this into Phase C findings, and any future tool reading scope results should read this file (not the three intermediate JSONs).

## Constraints

- Do NOT modify the three input JSONs.
- Do NOT add LLM judgment — this is deterministic merge logic. Promote to a subagent only if a future requirement actually needs reasoning.
