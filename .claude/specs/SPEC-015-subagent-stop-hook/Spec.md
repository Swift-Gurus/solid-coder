---
number: SPEC-015
feature: Subagent Flow Stop Hook
type: subtask
status: draft
parent: SPEC-010
blocked-by: [SPEC-013, SPEC-014]
blocking: []
---

# Subagent Flow Stop Hook

## Overview

`mcp-server/hooks/on_flow_subagent_stop.py` — a `SubagentStop` event handler that prevents a **subagent** from exiting before it has submitted the step output it was spawned to produce. Reuses the same engine (SPEC-012) and session→step mapping written by `flow_next` (SPEC-013).

The key difference from SPEC-014: a subagent is responsible for ONE step, not the whole flow. The check is "did this session call `flow_next(outputs)` for its assigned step?" not "is the full flow done?".

## How Session→Step Mapping Works

When a subagent calls `flow_next(outputs)`, MCP (SPEC-013) appends a `session_step_recorded` event to `events.jsonl`:

```jsonl
{"event": "session_step_recorded", "session_id": "abc-123", "instance_id": "run_reviews-2"}
```

`SubagentStop` reads `session_id` from the hook event, scans `events.jsonl` for a `session_step_recorded` line matching that session, and uses that to determine whether the subagent has submitted.

## User Stories

### US-1: Block subagent stop when its step is not submitted

As a flow, when a subagent spawned for a specific step tries to stop before calling `flow_next(outputs)`, I want the harness to re-inject the step prompt so the subagent completes its assignment.

**Acceptance Criteria:**
- Hook reads `session_id` from the Stop event
- Reads `active.json` to locate the active run
- Replays `events.jsonl` and scans for `session_step_recorded` with matching `session_id`
- If found → this session submitted its step; exit 0 (allow stop)
- If not found → this session hasn't submitted; write step prompt to stderr, exit 2

### US-2: Re-inject the correct step prompt

As a subagent, when I'm blocked from stopping, I want to be re-injected with the exact prompt I was spawned with so I know what to complete.

**Acceptance Criteria:**
- Hook reads the subagent's prompt from the Stop event's `transcript_path` or from the `step_started` event for the instance assigned to this session
- Falls back to a generic "You have an incomplete step. Call flow_next with your outputs." if the original prompt can't be recovered
- Writes the prompt to stderr before exiting 2

### US-3: No active run → no-op

As a subagent running outside a flow context, I want the hook to be transparent.

**Acceptance Criteria:**
- If `active.json` does not exist → exit 0
- If `SOLID_CODER_SESSION_TYPE` is set → exit 0

### US-4: Subagent that legitimately finishes without flow_next

As a subagent running an `inline` step or non-flow work, I want the hook to not interfere.

**Acceptance Criteria:**
- If no `session_step_recorded` event exists for this session AND no `step_started` event references this session → exit 0 (this session was not part of the flow)

## Implementation Notes

- `session_id` is read from the `SubagentStop` event JSON (`event["session_id"]`)
- Same `solid_coder_project_dir()` path convention as SPEC-014
- Imports `event_log` from `mcp-server/harness/` (SPEC-012)
- `hooks/hooks.json` addition:
  ```json
  "SubagentStop": [
    {
      "matcher": "",
      "hooks": [{ "type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/mcp-server/hooks/on_flow_subagent_stop.py\"" }]
    }
  ]
  ```

## Test Plan

- Unit: session has `session_step_recorded` event → exits 0
- Unit: session has no `session_step_recorded` event but is in `step_started` → writes prompt, exits 2
- Unit: session not referenced in events at all → exits 0
- Unit: no `active.json` → exits 0
- Unit: `SOLID_CODER_SESSION_TYPE` set → exits 0
- Integration: subagent that stops without submitting gets re-injected; after submitting, stop is allowed
