---
name: find-spec
description: Navigate the spec hierarchy interactively and return the selected spec. Internal skill used by build-spec.
argument-hint: "--status <draft|ready|draft,ready> [--action <label>]"
allowed-tools: Read, Bash, AskUserQuestion
user-invocable: false
---

# find-spec — Spec Hierarchy Navigator

Drills down through the spec tree level by level using AskUserQuestion. Returns the selected spec as JSON.

## Input

- `next-number` — non-interactive mode: returns the next available SPEC number as `{"next": "SPEC-NNN"}`
- `--status` — comma-separated statuses to show at each level (e.g. `draft`, `draft,ready`)
- `--action` — label for the "select this item" option at each level (e.g. `Resume this`, `Select as parent`). Defaults to `Select this`.

## Output

JSON written to stdout:
```json
{
  "number": "SPEC-NNN",
  "feature": "...",
  "type": "...",
  "status": "...",
  "path": "..."
}
```

## Modes

### Mode: next-number

If called with `next-number` as the argument:
- Run:
  ```
  python3 @scripts/find-spec-query.py next-number
  ```
- Return the JSON result `{"next": "SPEC-NNN"}` to the caller. Do not enter the interactive drill-down.

### Mode: interactive navigation

If called with `--status` (and optional `--action`), enter the drill-down phases below.

## Phases

- [ ] 1. **Root level** — run:
  ```
  python3 @scripts/find-spec-query.py scan --type epic --no-parent
  ```
  Filter results to allowed statuses. If empty: report "No specs found matching status filter." and exit with error.
  Present results + "Create new root epic" (if caller supports creation) using AskUserQuestion (`"SPEC-NNN — <feature> [<status>]"` per option).

- [ ] 2. **Drill down** — repeat until user selects the action or "Create new":
  - Run:
    ```
    python3 @scripts/find-spec-query.py scan --parent <current-SPEC-NNN>
    ```
    Filter results to allowed statuses.
  - Present results + `{--action}` for current item using AskUserQuestion.
  - If user selects `{--action}`: return current item as JSON output.
  - If results are empty: automatically return current item (it is the leaf).
  - Otherwise: update current to selected item and repeat.
