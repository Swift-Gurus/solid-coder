---
number: SPEC-010
feature: MCP-Driven Flow Orchestration (Harness)
type: feature
status: in-progress
parent:
blocked-by: []
blocking: [SPEC-030, SPEC-031, SPEC-032, SPEC-033, SPEC-035, SPEC-037]
---

# MCP-Driven Flow Orchestration (Harness)

## Overview

Replace skill-driven orchestration (SKILL.md phase checklists interpreted by an LLM) with an MCP-backed harness that owns flow state, drives agents with NL step prompts, and enforces completion via a stop hook. Agents execute atomic steps by following MCP instructions; the harness resolves dependencies, validates outputs, handles fan-out, and prevents premature exit.

## Problem

Current pipeline orchestration has four weaknesses:

1. **State in the LLM's head** — agents track "I'm on Phase 3.2" internally. Invisible, unverifiable, lost on interruption.
2. **No resume** — an interrupted run is lost. No way to pick up from where it stopped.
3. **Parallelism decided by prose** — SKILL.md says "launch ALL in a SINGLE message" but the LLM interprets this each time. Dependency ordering is re-derived from fixed text every run.
4. **No output validation** — agents submit outputs that downstream steps silently consume even if malformed.

## Proposed Solution

A harness built on top of the existing `solid-coder-pipeline` MCP server:

- Flow definitions are YAML DAGs discovered from project and plugin workflow packages; legacy flat `flows/` and `steps/` roots remain compatibility inputs
- Each step carries a static NL prompt — the MCP returns it to the agent as the instruction for that step
- Agents loop: `flow_next(outputs)` → execute returned agent-owned work → `flow_next(outputs)` until a terminal status; isolated child runs additionally pass their explicit `run_id`
- The shared Stop dispatcher checks the current session's active run and blocks premature exit while actionable work remains
- Outputs are schema-validated by MCP before a step is marked complete
- Flow-level `max_turns` and per-step `max_attempts` bound stalled runs and repeated failures

This replaces skills as the orchestration layer. Skills keep domain logic where needed; the harness handles ordering, dependency resolution, fan-out, validation, and enforcement.

## User Stories

### US-1: MCP returns the next instruction

As an agent, when I call `flow_next`, I want to receive the NL prompt for my next step so I know exactly what to do without interpreting a SKILL.md checklist.

**Acceptance Criteria:**
- `flow_next()` returns a list of ready steps, each with a `prompt` string
- The prompt is the static text from the step's YAML definition with `{{variables}}` interpolated from prior step outputs
- Multiple entries in the list = run in parallel
- A terminal `done`, `failed`, or `timed_out` status is returned instead of ready work when the run reaches that state

### US-2: Stop hook prevents premature exit

As a flow, when an agent tries to stop before all steps are complete, I want the harness to re-inject the next step prompt so the agent cannot exit mid-flow.

**Acceptance Criteria:**
- The shared Stop dispatcher resolves the current session's active-run pointer and replays `events.jsonl` to determine current state
- If the run is `in_progress` with pending work, the flow-transition check returns a structured deny decision naming the run and pending steps
- Each denial consumes an attempt through the same per-step attempt mechanism used by execution failures; exhaustion transitions the run to `failed`
- The check respects `max_turns`, terminal `done`/`failed`/`timed_out` states, and stop-hook re-entry
- If no active run, hook is a no-op

### US-3: Schema-validated output submission

As a flow, when an agent submits step outputs, I want MCP to validate them against the declared schema before transitioning so malformed outputs never reach downstream steps.

**Acceptance Criteria:**
- `flow_next(outputs)` accepts outputs keyed by ready `instance_id` and validates each addressed instance against its declared schemas
- Validation failure records a failed attempt for the addressed instance, returns an actionable error, and does not mark that instance complete or unblock its dependents
- Output type `data` validates against a JSON Schema
- Output type `file` validates the file exists at the declared path
- While attempts remain, the agent must correct and resubmit; exhaustion transitions the run to `failed`

### US-4: Dynamic parallel fan-out

As a flow, when a step must run once per item in a prior step's output list (e.g. one review per principle), I want MCP to expand it into N parallel step instances so the agent does not have to interpret prose instructions about parallelism.

**Acceptance Criteria:**
- Steps with `for_each: "{{expr}}"` are expanded at runtime into N instances, one per item
- Each instance has a stable `instance_id`, receives the item value interpolated into its prompt, and retains its source index for deterministic fan-in
- `flow_next` returns the incomplete agent-owned instances together when the step becomes ready; a caller may submit any addressed subset without completing or repeating its siblings
- Script and command instances execute inside MCP through their existing handlers; they are drained before the next agent-owned instances are returned
- All instances must complete before dependent steps are unlocked, and each declared output becomes an ordered array in source-item order regardless of completion order
- An empty source array completes inside MCP with empty arrays for the declared outputs and consumes no agent turn
- Validation failures and retry limits are tracked per instance, so one failing item does not consume another item's attempts or reopen a completed item
- Replaying the event log restores completed instances and returns only unfinished instances

### US-5: Resumable runs

As a developer, when a run is interrupted (context limit, crash, cancel), I want to resume from the last completed step so completed work is not re-run.

**Acceptance Criteria:**
- Each run writes an append-only `events.jsonl` — completed step outputs are durable
- `flow_next()` with an active run replays `events.jsonl` and returns only incomplete steps whose dependencies are satisfied
- `active-<session_id>.json` points to the current session's main run; `active.json` is the fallback only when no session identifier is available
- Isolated child runs are resumed by passing their explicit `run_id` to `flow_next`/`flow_status`; they never occupy the main-run pointer
- `flow_status()` returns the full state snapshot at any point

### US-6: User-defined custom flows

As a plugin consumer, I want to define my own flows so I can adapt the harness to my project's pipeline without modifying the plugin.

**Acceptance Criteria:**
- User workflow packages live recursively under `{project}/.solid-coder/workflows/`
- Plugin built-in workflow packages live recursively under `{plugin}/workflows/`
- Every public package contains `workflow.yaml` with a stable ID; optional package resources live in conventional `prompts/`, `schemas/`, `steps/`, `subflows/`, and `scripts/` folders
- User and plugin flows must have distinct identifiers; a collision is an error rather than an override
- `{project}/.solid-coder/harness/flows/`, `{project}/.solid-coder/harness/steps/`, and their plugin equivalents remain compatibility roots only

## Technical Requirements

### Workflow Package Structure

```
{plugin}/workflows/
  review/solid-review/
    workflow.yaml
    prompts/
    schemas/
    steps/
    subflows/
    scripts/

{project}/.solid-coder/workflows/
  <client-defined categories>/
    my-review/
      workflow.yaml
      prompts/
      schemas/
      steps/
      subflows/
      scripts/
```

SPEC-035 owns discovery, stable IDs, collision rejection, package-relative resources, and compatibility with the legacy flat roots.

### Flow Definition Schema

```yaml
id: review
name: Review
description: Full principle review pipeline
max_turns: 60           # circuit breaker — stop hook backs off after this many turns

steps:
  - uses: prepare-input.yaml

  - uses: load-principles.yaml

  - id: run_reviews
    type: delegate
    mode: subagent
    prompt: |
      Run the review flow for {{item}} in an isolated child run and return its findings.
    depends_on: [load_principles]
    for_each: "{{steps.load_principles.outputs.principles}}"
    max_attempts: 3
    outputs:
      - name: findings
        type: data
        schema_file: findings.schema.json

  - uses: validate-findings.yaml
    depends_on: [run_reviews]

  - uses: synthesize-fixes.yaml
    depends_on: [validate_findings]
```

`uses:` references a step fragment file. The step file's `id` becomes the step's DAG node. Inline step definitions and `uses:` steps are interchangeable.

### Step Definition Schema

```yaml
id: load_principles
prompt: |
  Load matching principles and return them as a JSON array of principle names.
  Call mcp tool get_candidate_tags with the input tags from review-input.json.
depends_on: [prepare_input]
max_attempts: 3
outputs:
  - name: principles
    type: data
    schema:
      type: array
      items: { type: string }
      minItems: 1
```

Output types:
- `type: data` — inline JSON value. Validated against `schema` (inline JSON Schema) or `schema_file` (relative path to a `.schema.json` file).
- `type: file` — output is a file path. MCP checks the file exists at `path` (supports `{{interpolation}}`).

### Step Execution Ownership

Step type and delegate mode explicitly determine who executes ready work:

| Declaration | Owner | Behavior |
|---|---|---|
| `type: agent` or omitted | Calling agent | Returned by `flow_start`/`flow_next`; completed by submitting outputs keyed by `instance_id` |
| `type: script` | MCP engine | Executes a declared script file through an allowlisted executor |
| `type: command` | MCP engine | Executes declared command text through an allowlisted executor |
| `type: delegate`, `mode: subagent` | Calling agent plus spawned subagent | Returned with explicit launch/isolation instructions; parent receives relayed outputs |
| `type: delegate`, `mode: session` | MCP engine | Runs synchronously through the configured Claude, Codex, or local backend |

SPEC-027 owns process steps and attempts. SPEC-028 owns delegate modes and isolated child runs. The engine never tries to infer execution mode from an environment variable.

### Template Interpolation

`{{expr}}` is interpolated through the shared expression resolver. Current context includes:

- `{{steps.<id>.outputs.<name>}}` — output value from a completed step
- `{{steps.<id>.outputs.<name> | length}}` — length filter
- `{{params.<name>}}` — parameter passed to `flow_start`
- `{{item}}` — current item in a `for_each` expansion

SPEC-037 owns the pending extension for nested item paths such as `{{item.language}}` and declarative conditions.

### Active Run Pointer

Runs live in the plugin's user data directory, derived via `solid_coder_project_dir()` from `hook_utils.py` — same slug convention used throughout the plugin (`/path/to/project` → `-path-to-project`):

```
~/.solid-coder/{project-slug}/runs/
  active-<session-id>.json            ← current main run for one session
  active.json                         ← fallback only when no session ID is available
  <run-id>/
    events.jsonl                      ← append-only event log
    workflow.yaml                     ← snapshot of flow definition at start time
    run-metadata.json                 ← persisted parameters
  subagents/
    <isolated-run-id>/
      events.jsonl
      workflow.yaml
      run-metadata.json
      active-<session-id>.json        ← self-contained isolated-run marker
```

Main-run pointers are session-scoped so concurrent Claude/Codex sessions do not collide. They are cleared when the run reaches `done`, `failed`, or `timed_out`; `flow_clear_lock` provides run-ID-checked recovery for a stale main pointer. Isolated runs live under `subagents/<run-id>/`, are addressed explicitly, and do not share the main-run lock.

### State Storage — Event Log (JSONL)

Append-only, replay-based. No full-file rewrites. Safe for concurrent subagent appends (file append is atomic on most OS).

```jsonl
{"ts": "...", "event": "run_started", "flow": "review", "params": {...}}
{"ts": "...", "event": "step_started", "step_id": "prepare_input", "instance_id": "prepare_input-1"}
{"ts": "...", "event": "step_completed", "instance_id": "prepare_input-1", "outputs": {...}}
{"ts": "...", "event": "step_started", "step_id": "load_principles", "instance_id": "load_principles-1"}
{"ts": "...", "event": "turn_counted", "total": 4}
```

Current state = replay all events in order. Resume = replay and return incomplete steps whose deps are satisfied.

### MCP Tools (added to solid-coder-pipeline)

**`flow_start(flow, params?, isolated?)`**
- Resolves an explicit path or a collision-checked workflow ID
- Creates run directory, writes `workflow.yaml` snapshot
- Writes `run_started` event to `events.jsonl`
- Writes the current session's main pointer, or a self-contained marker when `isolated=true`
- Returns first ready agent-owned steps with `step_id`, `instance_id`, rendered prompt, and execution metadata; isolated starts additionally disclose the `run_id` that subsequent calls must pass

**`flow_next(outputs?, run_id?)`**
- Resolves the current session's main run when `run_id` is absent, or the named isolated run when present
- Replays `events.jsonl` to determine current state
- If outputs are provided: validates each addressed `instance_id`; invalid instances consume attempts without completing, while valid addressed instances transition
- Drains ready MCP-owned script, command, and session-delegate steps before returning agent-owned work
- Returns ready steps or terminal `done`, `failed`, or `timed_out` status

**`flow_status(run_id?)`**
- Resolves the main or named isolated run and replays `events.jsonl`
- Returns `{ flow, run_id, status, turn_count, max_turns, completed: [...], running: [...], pending: [...] }`
- Returns `{ status: "no_active_run" }` if no current-session main pointer exists

**`flow_clear_lock(run_id)`**
- Clears only the current session's main-run pointer and only when the supplied ID matches the active run
- Rejects mismatches without changing state; reports a no-op when no main run is active
- Leaves the cleared run's persisted event log and snapshot intact

### Stop Enforcement

`hooks/hooks.json` registers the existing `mcp-server/hooks/on_stop.py` entry point. That entry point uses the generic concurrent Stop dispatcher: applicable checks run independently, any denial wins, all denial reasons are retained, and an internal check error fails open. SPEC-032's completed flow-transition check resolves the current session's main run, records attempt consumption through the engine, and returns a structured allow/deny response. It is not a standalone `on_flow_stop.py` script and does not communicate through raw stderr/exit-code control.

SPEC-033 is the deferred counterpart for a subagent attempting to abandon an isolated child run. It resumes as separate work after the main conditional flow is stable and is not required to complete this main-flow harness.

### Validation at Load Time

When `flow_start` loads a flow definition, MCP validates:
- Required workflow fields are present, each step has an ID, and each step satisfies the content fields required by its declared type
- No duplicate step IDs
- All `depends_on` references exist
- No dependency cycles (topological sort)
- All `uses:` references resolve through package resource rules or the legacy compatibility roots
- All `schema_file` references resolve relative to the step file
- Step shape matches its declared `agent`, `script`, `command`, or `delegate` type
- Process executors are allowlisted and package resources remain inside their owning package

### DAG Validation

MCP validates the DAG at `flow_start` time:
- Topological sort to detect cycles
- `for_each` expression references a step that is a transitive dependency
- Parallel steps' `for_each` output must be an array type in its declared schema
- `for_each` expressions use the exact `{{steps.<id>.outputs.<name>}}` form

## Test Plan

- Unit: `flow_start` creates the correct event log, snapshot, metadata, and session-scoped main pointer
- Unit: `flow_next` with valid outputs appends event and returns next ready steps
- Unit: `flow_next` with invalid outputs records an instance attempt, returns a validation error, and does not complete the instance
- Unit: `flow_next` respects `depends_on` — blocked steps not returned
- Unit: `for_each` expansion returns N step instances for N items
- Unit: partial instance submission keeps only unfinished siblings ready and does not unlock the dependent step
- Unit: out-of-order completion publishes output arrays in source-item order before unblocking the dependent step
- Unit: an empty source collection publishes empty output arrays and unblocks the dependent step without an agent turn
- Unit: retries are instance-scoped and completed siblings remain complete
- Unit: replay from interrupted `events.jsonl` restores completed instances and returns only unfinished instances
- Integration: a process-backed `for_each` step executes entirely inside MCP and returns only its downstream agent step
- Unit: turn counter increments and `timed_out` triggers at `max_turns`
- Unit: a client/plugin workflow ID collision is rejected; package-relative step fragments never override fragments in another package
- Integration: a representative review flow runs to `done` via MCP tools
- Integration: the shared Stop dispatcher denies premature exit with the active run and pending steps identified
- Integration: an interrupted main run resumes through its session-scoped active pointer
- Unit/integration: session-scoped main pointers do not collide and isolated runs require explicit `run_id`
- Integration: the shared Stop dispatcher blocks an abandoned main flow and exhausts attempts through the common failure path
- Deferred SPEC-033 follow-up: a subagent cannot abandon an in-progress isolated child flow
- Pending SPEC-037: deterministic conditions, skipped-state replay, explicit child-workflow inputs/outputs, and ordered branch aggregation

## Design Decisions

- **MCP owns orchestration state** — agents receive rendered instructions but do not decide dependency order, fan-out membership, process execution, or completion state.
- **One advance operation** — `flow_next` both submits addressed instance outputs and returns newly ready work; there is no separate complete/get-next round trip.
- **Session-scoped main runs, explicit isolated runs** — main calls omit `run_id` and resolve through the current session's pointer; isolated child calls must carry their exact `run_id`.
- **Shared Stop dispatch** — flow enforcement is one independently applicable check in the generic Stop dispatcher, not a separate hook program or response protocol.
- **Append-only replay** — `events.jsonl` is the durable audit and resume source; completed `for_each` instances, attempts, rejections, and terminal transitions replay deterministically.
- **Validated, bounded transitions** — outputs are schema-validated; `max_attempts` bounds instance failures and `max_turns` bounds the complete flow.
- **Explicit execution ownership** — step type and delegate mode select the handler; no environment-based subagent/session inference exists.
- **Snapshotted definitions** — each run persists its fully resolved workflow and parameters so plugin/package changes do not alter an in-progress run.
- **Collision rejection, not overrides** — project and plugin workflow IDs share one catalog and duplicates fail deterministically.

## Completion State

Completed child contracts: SPEC-030 core engine and `for_each` lifecycle, SPEC-031 MCP tools and session-scoped locks, SPEC-032 main-agent Stop enforcement, and SPEC-035 workflow packages/discovery. SPEC-027 and SPEC-028 additionally provide process steps, attempts, delegate modes, and isolated runs.

Remaining main-flow work:

- SPEC-037 — deterministic conditional routing, skipped branch state, explicit included-workflow inputs/outputs, and result aggregation.

Deferred follow-up, not a SPEC-010 completion condition:

- SPEC-033 — guard a subagent's own attempt to abandon an isolated child flow after the main flow is finalized.

## Definition of Done

- [x] MCP tools start, advance, inspect, and recover flow runs through persisted state.
- [x] Output schemas, dependencies, attempts, terminal states, and resume behavior are engine-enforced.
- [x] `for_each` supports partial completion, ordered fan-in, empty collections, replay, process-owned execution, and instance-scoped retries.
- [x] Main runs are session-scoped; isolated child runs are explicitly addressed and cannot collide with main locks.
- [x] The main-agent Stop check blocks abandoned active flows through the shared dispatcher.
- [x] Project and plugin workflow packages compose through collision-checked stable IDs.
- [x] Subagent Stop enforcement is tracked as separate deferred work in SPEC-033 and does not block the main-flow harness.
- [ ] Conditional workflow routing and aggregation are complete per SPEC-037.
- [ ] All active main-flow child-spec test plans pass, including their required Claude/Codex live coverage.
