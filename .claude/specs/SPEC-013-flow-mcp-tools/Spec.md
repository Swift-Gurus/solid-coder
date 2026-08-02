---
number: SPEC-013
feature: Flow Harness MCP Tools
type: subtask
status: done
parent: SPEC-010
blocked-by: [SPEC-012]
blocking: [SPEC-014, SPEC-015, SPEC-028]
---

# Flow Harness MCP Tools

## Overview

Four tools added to `mcp-server/pipeline/server.py` that expose the flow engine (SPEC-012) over MCP. Agents interact with the harness exclusively through these tools. The tools own the active run pointer and record session→step mappings needed by the stop hooks.

## Tools

**`flow_start(flow, params?, isolated?)`** — Start a new flow run. `isolated` (SPEC-028) starts the run in its own isolated slot instead of the shared main-run slot.

**`flow_next(outputs?, run_id?)`** — Submit current step outputs and get next ready steps. The core loop tool. `run_id` (SPEC-028) targets a specific isolated run instead of the main run.

**`flow_status(run_id?)`** — Read current run state. Used by stop hooks and for debugging. `run_id` (SPEC-028) targets a specific isolated run instead of the main run.

**`flow_clear_lock(run_id)`** — Clear the main run's lock after validating `run_id` matches the currently active run. See US-4.

## User Stories

### US-1: Start a flow

As an agent, I want to start a named flow so the harness resolves the definition, creates run state, and tells me what to do first.

**Acceptance Criteria:**
- `flow_start(flow, params?)` resolves the flow YAML via search paths: `{project}/.solid-coder/harness/flows/` first, `{plugin}/harness/flows/` fallback
- Creates `~/.solid-coder/{slug}/runs/{run_id}/` directory
- Writes `workflow.yaml` snapshot (the resolved, fully-merged flow definition)
- Appends `run_started` event to `events.jsonl`
- Writes `~/.solid-coder/{slug}/runs/active-{session_id}.json` → `{ run_id }` (falls back to `active.json` when no session id is available, e.g. `--bare` contexts)
- Returns `{ run_id, steps: [{ step_id, instance_id, prompt, execution_intent }] }` — first ready steps with interpolated prompts
- Fails with a clear error if the active-run pointer for this session already exists (another run in progress for that session)

### US-2: Submit a step and get the next one

As an agent, I want to submit my step's outputs and receive the next instruction so I stay in a tight loop without tracking state myself.

**Acceptance Criteria:**
- `flow_next(outputs?)` reads this session's active-run pointer to locate the run
- If `outputs` provided: validates each output against its declared schema via `schema_validator`; returns `{ error, validation_errors }` on failure — no state transition
- On valid outputs: appends `step_completed` event with `{ instance_id, outputs, session_id }`
- Records `session_id → instance_id` mapping in `events.jsonl` (`session_step_recorded` event) for SubagentStop lookup
- Increments turn counter (appends `turn_counted` event)
- Calls `dag_runner.ready_steps` to compute newly unblocked steps
- Returns `{ status: "ready", steps: [...] }` with interpolated prompts and resolved `execution_intent`
- Returns `{ status: "done" }` when all steps complete; deletes this session's active-run pointer
- Returns `{ status: "timed_out" }` when `turn_count >= max_turns`; deletes this session's active-run pointer
- Called with no `outputs` (first call after `flow_start`) — returns next steps without validating or transitioning

### US-3: Read current state

As a stop hook or developer, I want to inspect the current run without modifying it.

**Acceptance Criteria:**
- `flow_status()` reads this session's active-run pointer; returns `{ status: "no_active_run" }` if absent
- Replays `events.jsonl` via `event_log.replay`
- Returns `{ flow, run_id, status, turn_count, max_turns, completed: [...], running: [...], pending: [...] }`
- Read-only — no events appended, no state changed

### US-4: Clear a stuck lock

As an agent, when a prior run's lock was left behind (the session that owned it ended without reaching a terminal state), I want to clear that lock after confirming which run I'm clearing, so I can start fresh without an operator having to delete files by hand.

**Acceptance Criteria:**
- `flow_clear_lock(run_id)` succeeds only when `run_id` exactly matches the currently active run's own identifier; a mismatched or guessed `run_id` is rejected with an error naming the actual active run, without clearing anything.
- On a match, the lock is cleared and `flow_start` can immediately be called again; the cleared run's own event log is left untouched on disk for later inspection.
- When no lock is currently active, calling this tool is a no-op that reports there was nothing to clear, rather than an error.
- This tool only ever clears the main run's lock — it has no isolated-run equivalent (see SPEC-028 for isolated run lifecycle, which is self-contained per run and does not need this recovery path).

## Technical Notes

- **This spec's original design for step execution mode (an `execution.intent` field resolved via a `CLAUDE_AGENT_TYPE`-style environment variable) was never implemented as designed and has been fully replaced.** No such environment variable exists — Claude Code never sets one, confirmed empirically. Execution mode is now an explicit, author-declared step property (`type: delegate`, `mode: subagent`/`session`) — see SPEC-028, which also owns the isolated-run mechanism (`isolated` on `flow_start`, `run_id` on `flow_next`/`flow_status`) referenced in the Tools list above.
- `session_id` is read via `McpRequestContextSessionReader` (`harness/mcp_request_context_session_reader.py`): `CLAUDE_CODE_SESSION_ID` env var for Claude, falling back to `_meta.threadId` or `_meta["x-codex-turn-metadata"]["session_id"]` from the current call's context for Codex. Drives both the `session_step_recorded` event tagging and the active-run pointer filename (`ActiveRunPointerStore` → `SessionScopedActivePathResolver`); empty string falls back to the unscoped `active.json` filename.
- **Live-verified against both backends** (`tests/harness/flow_engine/test_flow_session_scoping_live.py`, run explicitly — not part of the fast sweep): a real `claude -p` session and a real `codex exec` session (via the project-scoped dev-marketplace override) each produced a session-scoped `active-{id}.json` pointer, not the unscoped fallback. Codex's tool-naming convention needed the full `mcp__pipeline__flow_start` reference in the prompt (a bare `flow_start` reference was not recognized) — a prompting detail, not a defect.
- **Possible real gap found while live-testing, not investigated further**: under Codex, `flow_start(flow="e2e_test")` (a bare name, meant to resolve via the documented search paths) failed with `Flow file not found or unreadable`; using an absolute path to the same file worked. This suggests the flow search-path resolution (`{project}/.solid-coder/harness/flows/` etc.) may not correctly resolve `{project}` when the MCP server subprocess is spawned by `codex exec` — possibly the same `CLAUDE_PROJECT_DIR`-vs-cwd distinction noted in `hc_config_core.py`. Worked around in the live test with an absolute path; **not confirmed whether this would also bite a real Codex user calling `flow_start` with a bare flow name in production.**
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
- Integration: two sessions with different session ids sharing one runs directory can each `flow_start`/`flow_next` independently without colliding
- Unit: `flow_clear_lock` succeeds and clears the pointer when `run_id` matches the active run
- Unit: `flow_clear_lock` rejects a mismatched `run_id` and clears nothing
- Unit: `flow_clear_lock` is a no-op with a "nothing to clear" result when no lock is active
