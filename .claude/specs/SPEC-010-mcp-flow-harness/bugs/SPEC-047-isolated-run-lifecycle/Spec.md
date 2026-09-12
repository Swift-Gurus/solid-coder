---
number: SPEC-047
feature: isolated-run-lifecycle
type: bug
status: draft
parent: SPEC-010
blocked-by: []
blocking: []
---

# Isolated Run Lifecycle Uses Session-Scoped State and Ambiguous Paths

## Description

Normal workflow runs and isolated child runs intentionally have different discovery and concurrency semantics, but they must share the same flow-engine execution, replay, validation, scoring, persistence, and terminal-state machinery.

A normal run is owned by one model session and is discovered through `runs/active-<session-id>.json`. An isolated run is created under `runs/subagents/<run-id>/`, may be continued by a different model session, and is discovered through its explicit `run_id`. The current implementation partially treats an isolated run like a normal session-owned run. It writes a session-scoped active pointer inside the isolated run directory, uses that pointer during lookup, and asks whichever session reaches completion to delete its own session-scoped pointer.

This breaks the health-check sequence because the write hook starts the isolated run under the authoring session while a child Codex or Claude session performs the model-owned steps. It also overloads `base_dir` to mean both a run collection and an already resolved run directory. Terminal finalization therefore risks appending the run ID twice and persisting review results under `runs/subagents/<run-id>/<run-id>/` instead of the canonical run directory.

The health-check coordinator is not a second workflow engine. It only adapts a prospective write into flow parameters, starts an isolated run, asks a child model to complete agent steps, waits for the authoritative flow result, and translates that result into allow or deny. All run lifecycle behavior remains owned by the flow engine.

The isolated child intentionally receives a minimal inline MCP configuration instead of the complete plugin. That configuration must expose the current plugin root's flow-engine server and the bootstrap prompt must identify the continuation capability in a form the selected backend can call directly. Backend-neutral workflow YAML must not contain Codex- or Claude-specific generated tool names. The runner boundary owns that translation; a child must not scan source files or enumerate its tool registry merely to discover `flow_next`.

## Observed Failure

Given a Claude Code write attempt and a Codex-configured health-check backend:

1. The write hook starts `solid-gate-on-write` as an isolated run.
2. The run is stored at `runs/subagents/<run-id>/` and receives the correct persisted `target` parameter.
3. `review.prepare` completes successfully.
4. The child Codex session calls `flow_next` with the correct explicit `run_id` and a schema-valid step submission.
5. The child MCP process searches for an active pointer scoped to the child session, while the directory contains a pointer scoped to the parent session.
6. MCP returns `No isolated run found for run_id=<run-id>` even though the run directory exists.
7. The parent then calls `flow_status`. Status replay historically supplied empty parameters instead of the persisted run metadata, producing the misleading error `Unresolvable reference: parameter 'target' not found in context`.

The explicit-run lookup and persisted-parameter replay have partial fixes in the current worktree. The complete lifecycle and cleanup design remains unresolved by this spec.

## Expected vs Actual

| Concern | Expected | Actual |
|---|---|---|
| Normal-run discovery | Resolve the current session's main run through its session-scoped active pointer. | Works as intended. |
| Isolated-run discovery | Resolve an existing isolated run by its explicit, validated `run_id`, independent of the calling session. | Previously required the caller's session-scoped pointer; a partial lookup fix now bypasses it. |
| Isolated concurrency | Multiple isolated runs coexist without occupying or blocking a main-run pointer. | Run directories are independent, but each still receives a redundant session-scoped pointer. |
| Completion cleanup | Remove exactly the lifecycle state created for the run, regardless of which session completes it. | A child session attempts to delete its own pointer and may leave the parent's pointer stale. |
| Terminal finalization | Persist scoring and aggregate review results directly under the resolved run directory. | `base_dir / run_id` may append the ID twice for isolated runs. |
| Replay | Reconstruct with the parameters persisted in `run-metadata.json`. | Status previously replayed with `{}`; the current worktree contains a partial correction. |
| Stop enforcement | Inspect only the current session's normal active run unless an internal caller explicitly supplies an isolated run ID. | Session-scoped normal behavior exists, but isolated pointer artifacts blur the ownership model. |
| Session registry | `active-sessions.json` maps model sessions to project context only. | It is separate from flow locking, but its name can be confused with active-run pointers. |
| Child MCP capability | Register only the current plugin root's flow-engine continuation capability and identify it unambiguously to the selected backend. | The server is registered inline, but the prompt uses a display name that makes Codex enumerate its tool registry before resolving the generated callable name. |

## Required Lifecycle Model

### Normal Run

- Canonical directory: `runs/<run-id>/`.
- Discovery: `runs/active-<session-id>.json`, with `active.json` only when no session ID exists.
- Concurrency rule: at most one normal active run per session.
- Stop hook: resolves the current session's normal pointer and blocks while actionable work remains.
- Completion: persists results in `runs/<run-id>/` and removes the owning session's pointer.

### Isolated Run

- Canonical directory: `runs/subagents/<run-id>/`.
- Discovery: an explicit validated `run_id`, independent of parent or child session identity.
- Concurrency rule: each unique run directory is independent; isolated runs do not occupy the main-run pointer.
- Stop hook: does not treat a parent's isolated health run as that parent's normal active run.
- Completion: persists results in `runs/subagents/<run-id>/` and leaves no stale session-scoped pointer.
- Resume and status: remain available by explicit `run_id` after interruption and after terminal completion.

## Architecture Constraints

- Do not create health-specific replay, scoring, completion, persistence, or locking implementations.
- Keep health coordination as a boundary adapter over the standard flow engine.
- Replace ambiguous path arguments with an explicit typed run location or equivalent typed normal/isolated lifecycle representation.
- A component receiving a resolved run location must not reconstruct `run_directory` by appending `run_id` again.
- Normal-run pointer ownership and isolated-run identity must be represented separately rather than inferred from path shape or optional values.
- `active-sessions.json` remains a project-context registry and must not become a run lock.
- Explicit `run_id` resolution must reject empty IDs, path traversal, nested path components, symlink escapes, and missing run directories.
- Model-facing tools remain limited to flow progression. Status and lock recovery remain internal.
- Keep workflow definitions backend-neutral. Resolve any Codex/Claude callable-name differences at the child-runner or bootstrap-prompt boundary.
- The isolated child must use the flow-engine server from the same plugin root that started the hook; it must not silently resolve an installed or cached plugin copy.

## Acceptance Criteria

### AC-1: Cross-session isolated continuation

Given a parent session starts an isolated workflow, when a child session with a different session ID calls `flow_next` using the returned explicit `run_id`, then the child continues the same run without requiring a child-scoped active pointer.

### AC-2: Persisted replay parameters

Given an isolated run whose workflow references `params.target`, when any internal caller requests status or resumes the run, then replay reads `target` and every other root parameter from that run's `run-metadata.json`.

### AC-3: Canonical result directory

Given an isolated review run reaches `done`, when deterministic rule scoring and aggregate review finalization execute, then every result is written beneath `runs/subagents/<run-id>/results/` and no `<run-id>/<run-id>/` directory is created.

### AC-4: Terminal result remains readable

Given a child session completes an isolated health run, when the parent health-check coordinator reads the authoritative result by `run_id`, then it receives the completed aggregate review result after terminal cleanup.

### AC-5: No stale isolated pointer

Given one session creates an isolated run and another completes, fails, or times it out, when terminal cleanup finishes, then the run directory contains no stale `active-<parent>.json`, `active-<child>.json`, or `active.json` lifecycle marker.

### AC-6: Normal-run locks remain session-scoped

Given two sessions start normal workflows in the same project, when both runs are active, then each session resolves only its own pointer and one session's Stop hook does not block on the other's run.

### AC-7: Isolated runs do not affect normal Stop enforcement

Given a session owns no normal workflow but has one or more isolated health runs, when the session attempts to stop, then the normal flow-transition Stop hook does not treat those isolated runs as its active main flow.

### AC-8: Explicit lookup is path-safe

Given an empty, missing, nested, traversal, or symlink-escaping run ID, when isolated lookup occurs, then it returns a typed not-found/invalid-run failure without reading outside `runs/subagents/`.

### AC-9: Health-check end-to-end completion

Given Claude or Codex attempts to write a prospective source buffer, when `solid-gate-on-write` is started by the hook and completed by a differently scoped child model session, then the workflow reaches a terminal state and the hook returns allow or deny from its scored result rather than an infrastructure error.

### AC-10: Existing model-facing behavior is preserved

Given an ordinary user-started workflow, when the model calls `flow_start` and `flow_next` without an isolated run ID, then existing session-scoped progression, replay, retries, and Stop enforcement remain unchanged.

### AC-11: Child continuation tool is unambiguous

Given the health checker selects either the Codex or Claude backend, when it launches the isolated child, then the child receives the current plugin root's flow-engine MCP server and can call the continuation tool directly from the bootstrap instruction without source discovery, filesystem search, or tool-registry enumeration.

## Required Tests

- Unit test: normal lookup still reads the current session's active pointer.
- Unit test: explicit isolated lookup succeeds when only a differently scoped parent pointer exists.
- Unit test: explicit isolated lookup rejects path traversal and symlink escape.
- Integration test: parent session starts an isolated run and a different child session completes it through `flow_next(run_id=...)`.
- Integration test: status replay preserves root parameters after reconstructing the orchestrator.
- Integration test: child completion removes all isolated lifecycle markers created at startup.
- Integration test: isolated rule finalization writes aggregate results to the canonical run directory.
- Integration test: completed isolated results remain readable after active state is released.
- Stop-hook test: isolated runs do not block the parent's normal Stop path.
- Live E2E: Claude authoring session with Codex health backend writes a SwiftUI buffer and receives a scored gate decision.
- Live E2E: Codex authoring session with Claude health backend exercises the same contract.
- Live E2E evidence: each backend's child transcript contains direct `flow_next` calls and no preliminary tool-discovery turn.
- Full non-live suite and existing Codex/Claude flow-engine live suite remain green.

## Affected Components

- `mcp-server/harness/run_initializer.py`
- `mcp-server/harness/active_run_locator.py`
- `mcp-server/harness/active_run_pointer_store.py`
- `mcp-server/harness/active_run_location.py`
- `mcp-server/harness/run_completion_checker.py`
- `mcp-server/harness/flow_status_reader.py`
- `mcp-server/harness/flow_run_orchestrator_factory.py`
- `mcp-server/hooks/flow_transition_gate_factory.py`
- `mcp-server/health/workflow_health_checker.py`
- `mcp-server/health/flow_review_result_reader.py`
- `mcp-server/health/gate_flow_prompt_builder.py`
- `mcp-server/health/codex/codex_command_builder.py`

## Deferred Fix Boundary

Do not redesign or implement the remaining lifecycle changes as part of the current health-gate experiment. Preserve the two current symptom fixes and the new regression coverage. Plan and implement the typed normal/isolated lifecycle as a focused change under this spec, then rerun the locked cross-model health-gate scenarios before declaring the workflow-based health checker production-ready.
