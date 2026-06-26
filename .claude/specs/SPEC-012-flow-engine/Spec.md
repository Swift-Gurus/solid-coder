---
number: SPEC-012
feature: Core Flow Engine (Abstraction)
type: subtask
status: draft
parent: SPEC-010
blocked-by: []
blocking: [SPEC-013, SPEC-014, SPEC-015]
---

# Core Flow Engine (Abstraction)

## Overview

A pure Python library — no MCP, no hooks, no I/O side effects — that implements the flow state machine. All higher layers (MCP tools, stop hooks) depend on this. The engine is the only place that knows how DAGs work, how events are replayed, and how templates are interpolated.

## Scope

`mcp-server/harness/` (new module):

| File | Responsibility |
|---|---|
| `flow_loader.py` | Load + validate a flow YAML (DAG validator, `uses:` resolution) |
| `event_log.py` | Append events to `events.jsonl`; replay log → current state |
| `dag_runner.py` | Given current state, compute which steps are ready next |
| `interpolator.py` | `{{expr}}` template interpolation against step context |
| `schema_validator.py` | Validate step outputs against inline schema or `schema_file` |

## User Stories

### US-1: Load and validate a flow definition

As a caller, I want to load a flow YAML and get back a validated DAG so invalid definitions fail fast at load time, not mid-run.

**Acceptance Criteria:**
- `flow_loader.load(path, search_paths)` resolves `uses:` references (user path first, plugin path fallback by filename)
- Returns a `FlowDef` dataclass: `name`, `max_turns`, `steps[]` each with `id`, `prompt`, `depends_on`, `outputs`, `execution`, `for_each`
- Raises `FlowValidationError` with a clear message for: missing required fields, duplicate step IDs, unresolvable `uses:` references, dependency cycles (topological sort), `for_each` referencing a non-existent dependency output

### US-2: Append and replay events

As a caller, I want to append events to an append-only log and replay the log to reconstruct current state.

**Acceptance Criteria:**
- `event_log.append(path, event_type, payload)` appends one JSON line to `events.jsonl`; atomic on POSIX (`os.write` to fd opened with `O_APPEND`)
- `event_log.replay(path)` reads all lines, returns `RunState`: `{ completed: {step_id: outputs}, running: [step_id], turn_count, status }`
- Partial/corrupt lines at end of file (interrupted write) are skipped with a warning, not a hard error
- Replay is pure — no I/O side effects, deterministic given the same file

### US-3: Compute ready steps

As a caller, given a `FlowDef` and a `RunState`, I want the list of steps that are ready to execute.

**Acceptance Criteria:**
- `dag_runner.ready_steps(flow_def, run_state)` returns steps whose `depends_on` are all in `run_state.completed`
- Excludes steps already in `running` or `completed`
- Expands `for_each` steps into N `StepInstance` objects, one per item, with `item` bound in each instance's context
- Returns `[]` when all steps are complete (`status = done`)
- Returns `[]` when `run_state.turn_count >= flow_def.max_turns` (`status = timed_out`)

### US-4: Interpolate templates

As a caller, I want `{{expr}}` placeholders in a prompt resolved against run context.

**Acceptance Criteria:**
- `interpolator.render(template, context)` resolves `{{steps.<id>.outputs.<name>}}`, `{{item}}`, `{{output_dir}}`
- Supports `| length` filter on lists
- Raises `InterpolationError` for unresolvable references (missing step or output key)
- Pure function — no I/O

### US-5: Validate step outputs

As a caller, I want submitted step outputs validated against the declared schema before they are accepted.

**Acceptance Criteria:**
- `schema_validator.validate(output_spec, value)` validates `type: data` against inline JSON Schema (using `jsonschema` library) or `schema_file` (relative to step file, loaded once and cached)
- `type: file` validates the path exists on disk
- Returns `ValidationResult(ok=True)` or `ValidationResult(ok=False, errors=[...])` — never raises
- Pure function for `type: data`; only `type: file` does I/O (path existence check)

## Test Plan

- Unit: `flow_loader` — valid flow loads correctly; each validation error case raises with message
- Unit: `event_log.append` — file grows by one line per call; concurrent appends from threads don't corrupt lines
- Unit: `event_log.replay` — correct `RunState` from a sequence of events; corrupt final line skipped
- Unit: `dag_runner.ready_steps` — respects depends_on; for_each expansion; timed_out at max_turns
- Unit: `interpolator.render` — resolves all context types; raises on unresolvable
- Unit: `schema_validator.validate` — inline schema pass/fail; schema_file pass/fail; type:file exists/missing
