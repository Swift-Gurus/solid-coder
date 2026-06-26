---
number: SPEC-014
feature: Agent Flow Stop Hook
type: subtask
status: draft
parent: SPEC-010
blocked-by: [SPEC-013]
blocking: [SPEC-015]
---

# Agent Flow Stop Hook

## Overview

`mcp-server/hooks/on_flow_stop.py` — a `Stop` event handler that prevents the **main agent** from exiting before the active flow run reaches `done` or `timed_out`. Registered in `hooks/hooks.json` alongside the existing `on_stop.py` and `on_agent_stop.py` handlers.

## Behavior

- Fires on every `Stop` event
- If no active run → no-op, exit 0
- If run is `done` or `timed_out` → clean up `active.json`, exit 0
- If run is in progress → write next step prompt to stderr, exit 2 (blocks the stop)

## User Stories

### US-1: Block main agent stop when flow is incomplete

As a flow, when the main agent tries to stop before the run is done, I want the harness to re-inject the next step so the agent continues without any explicit check in its prompt.

**Acceptance Criteria:**
- Hook reads `active.json` from `solid_coder_project_dir() / "runs" / "active.json"`
- Replays `events.jsonl` via `event_log.replay` (imported from SPEC-012's engine)
- If `run_state.status == "done"` or `"timed_out"`: removes `active.json`, exits 0
- If `run_state.status == "in_progress"`: calls `dag_runner.ready_steps(flow_def, run_state)` to get next steps, writes their prompts to stderr, exits 2
- `stop_hook_active: true` in the event → exit 0 immediately (prevents infinite re-entry)

### US-2: Respect the turn limit

As a flow, when the agent has exceeded `max_turns` without completing, I want the harness to release the agent (not re-inject forever).

**Acceptance Criteria:**
- If `run_state.turn_count >= flow_def.max_turns`: marks run as `timed_out` (appends event), removes `active.json`, exits 0
- `flow_def` is loaded from the snapshotted `workflow.yaml` in the run directory

### US-3: Managed session bypass

As a pipeline-internal session (health check, review subagent), I want the hook to be a no-op so internal sessions are not interrupted.

**Acceptance Criteria:**
- If `SOLID_CODER_SESSION_TYPE` env var is set → exit 0 immediately (matches existing `ManagedSessionGuard` pattern)

## Implementation Notes

- Reads `event` from stdin (JSON, same shape as `on_agent_stop.py`)
- Uses `solid_coder_project_dir()` from `hook_utils.py` for run path resolution
- Imports `event_log`, `dag_runner`, `flow_loader` from `mcp-server/harness/` (SPEC-012)
- Writes multi-step prompt as: one line per step, prefixed with step index if multiple
- `hooks/hooks.json` addition:
  ```json
  { "hooks": [{ "type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/mcp-server/hooks/on_flow_stop.py\"" }] }
  ```
  added to the `Stop` array

## Test Plan

- Unit: no `active.json` → exits 0
- Unit: run is `done` → deletes `active.json`, exits 0
- Unit: run in progress → writes prompt to stderr, exits 2
- Unit: `turn_count >= max_turns` → appends `timed_out` event, deletes `active.json`, exits 0
- Unit: `stop_hook_active: true` → exits 0
- Unit: `SOLID_CODER_SESSION_TYPE` set → exits 0
- Integration: agent that stops mid-flow gets re-injected with correct next step
