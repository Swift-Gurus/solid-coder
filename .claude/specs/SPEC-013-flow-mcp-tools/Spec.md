---
number: SPEC-013
feature: Flow Harness MCP Tools
type: subtask
status: draft
parent: SPEC-010
blocked-by: [SPEC-012]
blocking: [SPEC-014, SPEC-015]
---

# Flow Harness MCP Tools

## Overview

Three new tools added to `mcp-server/pipeline/server.py` that expose the flow engine (SPEC-012) over MCP. Agents interact with the harness exclusively through these tools. The tools own the active run pointer and record session→step mappings needed by the stop hooks.

## Tools

**`flow_start(flow, params?)`** — Start a new flow run.

**`flow_next(outputs?)`** — Submit current step outputs and get next ready steps. The core loop tool.

**`flow_status()`** — Read current run state. Used by stop hooks and for debugging.

## User Stories

### US-1: Start a flow

As an agent, I want to start a named flow so the harness resolves the definition, creates run state, and tells me what to do first.

**Acceptance Criteria:**
- `flow_start(flow, params?)` resolves the flow YAML via search paths: `{project}/.solid-coder/harness/flows/` first, `{plugin}/harness/flows/` fallback
- Creates `~/.solid-coder/{slug}/runs/{run_id}/` directory
- Writes `workflow.yaml` snapshot (the resolved, fully-merged flow definition)
- Appends `run_started` event to `events.jsonl`
- Writes `~/.solid-coder/{slug}/runs/active.json` → `{ run_id }`
- Returns `{ run_id, steps: [{ step_id, instance_id, prompt, execution_intent }] }` — first ready steps with interpolated prompts
- Fails with a clear error if `active.json` already exists (another run in progress)

### US-2: Submit a step and get the next one

As an agent, I want to submit my step's outputs and receive the next instruction so I stay in a tight loop without tracking state myself.

**Acceptance Criteria:**
- `flow_next(outputs?)` reads `active.json` to locate the run
- If `outputs` provided: validates each output against its declared schema via `schema_validator`; returns `{ error, validation_errors }` on failure — no state transition
- On valid outputs: appends `step_completed` event with `{ instance_id, outputs, session_id }`
- Records `session_id → instance_id` mapping in `events.jsonl` (`session_step_recorded` event) for SubagentStop lookup
- Increments turn counter (appends `turn_counted` event)
- Calls `dag_runner.ready_steps` to compute newly unblocked steps
- Returns `{ status: "ready", steps: [...] }` with interpolated prompts and resolved `execution_intent`
- Returns `{ status: "done" }` when all steps complete; deletes `active.json`
- Returns `{ status: "timed_out" }` when `turn_count >= max_turns`; deletes `active.json`
- Called with no `outputs` (first call after `flow_start`) — returns next steps without validating or transitioning

### US-3: Read current state

As a stop hook or developer, I want to inspect the current run without modifying it.

**Acceptance Criteria:**
- `flow_status()` reads `active.json`; returns `{ status: "no_active_run" }` if absent
- Replays `events.jsonl` via `event_log.replay`
- Returns `{ flow, run_id, status, turn_count, max_turns, completed: [...], running: [...], pending: [...] }`
- Read-only — no events appended, no state changed

### US-4: Execution intent resolution

As an agent, I want `flow_next` to tell me HOW to run each step (inline, subagent, session) so I don't have to interpret it.

**Acceptance Criteria:**
- `flow_next` detects runtime environment at `flow_start` time (env var `CLAUDE_AGENT_TYPE` or similar) and stores in run state
- Maps `execution.intent` → concrete mechanism per environment:
  - `inline` → `{ mode: "inline" }` always
  - `parallel_isolated` → `{ mode: "subagent" }` in Claude Code, `{ mode: "session" }` elsewhere
  - `sequential_isolated` → `{ mode: "subagent" }` or `{ mode: "session" }` same as above
- Each step in the returned list includes `execution: { mode: "inline" | "subagent" | "session" }`

## Technical Notes

- `session_id` is read from the MCP request context (Claude Code passes it per-call)
- Run directory slug derived via `solid_coder_slug()` from `hook_utils.py`
- Tools added to the existing `pipeline/server.py` tool registry — no new server

## Test Plan

- Unit: `flow_start` creates correct directory structure and `active.json`
- Unit: `flow_start` fails when `active.json` exists
- Unit: `flow_next` with valid outputs appends correct events and returns next steps
- Unit: `flow_next` with invalid outputs returns error, no events appended
- Unit: `flow_next` returns `done` when all steps complete; deletes `active.json`
- Unit: `flow_next` returns `timed_out` at `max_turns`; deletes `active.json`
- Unit: `flow_status` returns correct state snapshot; no side effects
- Unit: session_id → instance_id recorded in `session_step_recorded` event
- Integration: `flow_start` → `flow_next` loop runs a simple 3-step flow to `done`
