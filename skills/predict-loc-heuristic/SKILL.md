---
name: predict-loc-heuristic
description: Compute a fast, deterministic heuristic estimate of production LOC for a spec, based on AC count and screen count. Internal skill — invoked by validate-spec Phase C.
argument-hint: <spec-path> <output-dir>
allowed-tools: Bash
user-invocable: false
---

# Predict LOC — Heuristic

## Input

- SPEC_PATH: `$ARGUMENTS[0]` — absolute path to the spec's `Spec.md`
- OUTPUT_DIR: `$ARGUMENTS[1]` — absolute path to the directory where `heuristic.json` will be written
- SKILL_ROOT: `${CLAUDE_PLUGIN_ROOT}/skills/predict-loc-heuristic`

## Workflow

- [ ] 1.1 Run the counting script:
    ```bash
    python3 {SKILL_ROOT}/scripts/count-spec.py {SPEC_PATH} {OUTPUT_DIR}/heuristic.json
    ```
- [ ] 1.2 Report the predicted LOC, severity, and per-story AC counts from the resulting JSON.
- [ ] 1.3 If the script exits non-zero, fail with the script's error message.

## Output

`{OUTPUT_DIR}/heuristic.json` matching `output.schema.json`. Contains: `ac_count`, `screens`, `predicted_loc`, `severity`, `formula`, `by_story`, `spec_path`.

## Constraints

- Do NOT modify the spec file.
- Do NOT invent ACs — count only `- ` bullets that follow a `### US-N:` story header until the next `##`/`###` boundary.
- Do NOT count tests, DoD items, or TR bullets as ACs.
