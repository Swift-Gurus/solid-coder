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

Internal skill that navigates the spec hierarchy interactively and returns the selected spec. Takes a `--status` filter so callers control which specs are visible (e.g. `draft` for resume, `draft,ready` for parent selection when creating).

## Input

- `--status` — comma-separated list of statuses to show (e.g. `draft`, `draft,ready`)
- `--action` — label for "select this" option at each level (defaults to `Select this`)

## Output

JSON to stdout: `{number, feature, type, status, path}`

## Connects To

| Skill | Relationship |
|-------|-------------|
| `build-spec` | Called in Phase 0 (navigate to parent) and Phase 1-Resume (find target) |

## Design Decisions

- **Status filter at call site** — callers pass `--status` so the same skill serves both resume (draft only) and new spec parent selection (draft+ready). No logic duplication.
- **Script owns discovery** — `find-spec/scripts/find-spec-query.py` handles all file system queries. The skill handles only the interactive drill-down.
- **Returns leaf automatically** — if a level has no matching children, the current item is returned without asking.