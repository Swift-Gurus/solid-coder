---
name: find-spec
description: Navigate the spec hierarchy interactively, query ancestors, scan specs, or get next available spec number.
argument-hint: <mode> [mode-specific args]
allowed-tools: Read, Bash, AskUserQuestion
user-invocable: false
---

# find-spec — Spec Hierarchy Navigator

Query the spec tree or drill down interactively. Returns JSON.

## Input

- MODE: $ARGUMENTS[0] — one of `next-number`, `ancestors`, `scan`, or `navigate`
- Arguments per mode:
  - `next-number`: (no additional arguments)
  - `ancestors`: SPEC_NUMBER = $ARGUMENTS[1], BLOCKED = `--blocked` flag if present in $ARGUMENTS[2]
  - `scan`: SCAN_ARGS = $ARGUMENTS[1..] (passed through to script — supports `--type`, `--status`, `--no-parent`, `--parent`)
  - `navigate`: STATUS = $ARGUMENTS[1] (comma-separated statuses), ACTION = $ARGUMENTS[2] (label for select option, defaults to `Select this`)

## Output

| Mode | Output |
|------|--------|
| `next-number` | `{"next": "SPEC-NNN"}` |
| `ancestors` | JSON array of `{number, feature, type, status, path}`, ordered root → leaf |
| `scan` | JSON array of `{number, feature, type, status, path}` matching filters |
| `navigate` | Single `{number, feature, type, status, path}` |

## Modes

### Mode: next-number

- Run:
  ```
  python3 ${CLAUDE_PLUGIN_ROOT}/skills/find-spec/scripts/find-spec-query.py next-number
  ```
- Return the JSON result to the caller.

### Mode: ancestors

- Run:
  ```
  python3 ${CLAUDE_PLUGIN_ROOT}/skills/find-spec/scripts/find-spec-query.py ancestors {SPEC_NUMBER} [--blocked]
  ```
- Return the JSON array result to the caller. When `--blocked` is present, blocked-by specs are appended after the ancestor chain.

### Mode: scan

- Run:
  ```
  python3 ${CLAUDE_PLUGIN_ROOT}/skills/find-spec/scripts/find-spec-query.py scan {SCAN_ARGS}
  ```
- Return the JSON array result to the caller. Supports all script scan flags: `--type <type>`, `--status <statuses>`, `--no-parent`, `--parent <SPEC-NNN>`.

### Mode: navigate

Enter the interactive drill-down phases below.

## Phases (navigate mode only)

- [ ] 1. **Root level** — run:
  ```
  python3 ${CLAUDE_PLUGIN_ROOT}/skills/find-spec/scripts/find-spec-query.py scan --type epic --no-parent
  ```
  Filter results to STATUS. If empty: report "No specs found matching status filter." and exit with error.
  Present results + "Create new root epic" (if caller supports creation) using AskUserQuestion (`"SPEC-NNN — <feature> [<status>]"` per option).

- [ ] 2. **Drill down** — repeat until user selects the action or "Create new":
  - Run:
    ```
    python3 ${CLAUDE_PLUGIN_ROOT}/skills/find-spec/scripts/find-spec-query.py scan --parent <current-SPEC-NNN>
    ```
    Filter results to STATUS.
  - Present results + `{ACTION}` for current item using AskUserQuestion.
  - If user selects `{ACTION}`: return current item as JSON output.
  - If results are empty: automatically return current item (it is the leaf).
  - Otherwise: update current to selected item and repeat.