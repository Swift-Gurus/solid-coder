---
number: SPEC-008
feature: find-spec
type: feature
status: ready
parent: SPEC-007
blocked-by: []
blocking: []
---

# find-spec — Spec Hierarchy Navigator

## Description

Internal skill that navigates the spec hierarchy interactively and returns the selected spec, or performs non-interactive queries (ancestors, next-number) against the spec tree.

## Modes

| Mode | Input | Output | Interactive |
|------|-------|--------|-------------|
| `navigate` | `navigate <statuses> [<action label>]` | Single spec JSON `{number, feature, type, status, path}` | Yes |
| `ancestors` | `ancestors <SPEC-NNN> [--blocked]` | JSON array of specs, root → leaf (+ blocked-by if `--blocked`) | No |
| `scan` | `scan [--type X] [--status X] [--no-parent] [--parent X]` | JSON array of matching specs | No |
| `next-number` | `next-number` | `{"next": "SPEC-NNN"}` | No |

## Connects To

| Skill | Relationship |
|-------|-------------|
| `build-spec` | Called in Phase 0 (navigate to parent) and Phase 1-Resume (find target) |
| `plan` | Called in Phase 1.2 (load ancestor context via `ancestors --blocked`) |

## Design Decisions

- **Mode-first arguments** — `$ARGUMENTS[0]` is always the mode (`next-number`, `ancestors`, `scan`, `navigate`). Remaining args are mode-specific. Callers never mix flag styles.
- **Status filter at call site** — `navigate` mode takes statuses as $ARGUMENTS[1] so callers control which specs are visible (e.g. `draft` for resume, `draft,ready` for parent selection). No logic duplication.
- **Script owns discovery** — `find-spec/scripts/find-spec-query.py` handles all file system queries. The skill handles only the interactive drill-down.
- **Returns leaf automatically** — if a level has no matching children, the current item is returned without asking.