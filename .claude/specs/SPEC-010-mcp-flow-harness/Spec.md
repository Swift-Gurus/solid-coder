---
number: SPEC-010
feature: MCP-Driven Flow Orchestration (Harness)
type: feature
status: draft
parent:
blocked-by: []
blocking: [SPEC-012, SPEC-013, SPEC-014, SPEC-015]
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

- Flow definitions are YAML DAGs (`flows/`) with reusable step fragments (`steps/`)
- Each step carries a static NL prompt — the MCP returns it to the agent as the instruction for that step
- Agents loop: `flow_next(outputs)` → execute → `flow_next(outputs)` → repeat until `done`
- A Claude Code stop hook reads the run state file and re-injects the next step prompt if the flow is not complete
- Outputs are schema-validated by MCP before a step is marked complete
- Flow-level `max_turns` acts as a circuit breaker

This replaces skills as the orchestration layer. Skills keep domain logic where needed; the harness handles ordering, dependency resolution, fan-out, validation, and enforcement.

## User Stories

### US-1: MCP returns the next instruction

As an agent, when I call `flow_next`, I want to receive the NL prompt for my next step so I know exactly what to do without interpreting a SKILL.md checklist.

**Acceptance Criteria:**
- `flow_next()` returns a list of ready steps, each with a `prompt` string
- The prompt is the static text from the step's YAML definition with `{{variables}}` interpolated from prior step outputs
- Multiple entries in the list = run in parallel
- `{ status: "done" }` returned when all steps complete

### US-2: Stop hook prevents premature exit

As a flow, when an agent tries to stop before all steps are complete, I want the harness to re-inject the next step prompt so the agent cannot exit mid-flow.

**Acceptance Criteria:**
- A Claude Code stop hook reads `active.json` → replays `events.jsonl` to determine current state
- If flow is not `done`, hook exits non-zero and outputs the next ready step's prompt
- Hook respects `max_turns` — if the turn count exceeds the flow's limit, hook allows the agent to exit and marks the run `timed_out`
- If no active run, hook is a no-op

### US-3: Schema-validated output submission

As a flow, when an agent submits step outputs, I want MCP to validate them against the declared schema before transitioning so malformed outputs never reach downstream steps.

**Acceptance Criteria:**
- `flow_next(outputs)` validates each output against its declared schema (inline or file)
- Validation failure returns an error message — no state transition occurs
- Output type `data` validates against a JSON Schema
- Output type `file` validates the file exists at the declared path
- On failure the agent must correct and resubmit; the step is not marked complete

### US-4: Dynamic parallel fan-out

As a flow, when a step must run once per item in a prior step's output list (e.g. one review per principle), I want MCP to expand it into N parallel step instances so the agent does not have to interpret prose instructions about parallelism.

**Acceptance Criteria:**
- Steps with `for_each: "{{expr}}"` are expanded at runtime into N instances, one per item
- Each instance receives the item value interpolated into its prompt
- `flow_next` returns all N instances as a list when the step becomes ready
- All N must complete before dependent steps are unlocked
- The agent spawns one subagent or session per instance based on the step's `execution.intent`

### US-5: Resumable runs

As a developer, when a run is interrupted (context limit, crash, cancel), I want to resume from the last completed step so completed work is not re-run.

**Acceptance Criteria:**
- Each run writes an append-only `events.jsonl` — completed step outputs are durable
- `flow_next()` with an active run replays `events.jsonl` and returns only incomplete steps whose dependencies are satisfied
- `active.json` points to the current run; resuming a session picks up the same run automatically
- `flow_status()` returns the full state snapshot at any point

### US-6: User-defined custom flows

As a plugin consumer, I want to define my own flows (or override built-in ones) so I can adapt the harness to my project's pipeline without modifying the plugin.

**Acceptance Criteria:**
- User flows live in `{project}/.solid-coder/harness/flows/` and `{project}/.solid-coder/harness/steps/`
- Plugin built-in flows live in `{plugin}/harness/flows/` and `{plugin}/harness/steps/`
- Resolution: user path checked first, plugin path as fallback — first match wins, by filename
- User can override a built-in step by placing a file with the same name in their `steps/` folder

## Technical Requirements

### Harness Folder Structure

```
{plugin}/harness/              ← built-in defaults (shipped with plugin)
  flows/
    review.yaml
    implement.yaml
    plan.yaml
  steps/
    prepare-input.yaml
    load-principles.yaml
    run-reviews.yaml
    validate-findings.yaml
    synthesize-fixes.yaml

{project}/.solid-coder/harness/   ← user custom / override (first-match wins)
  flows/
    my-flow.yaml
  steps/
    load-principles.yaml          ← overrides plugin's step of same name
```

### Flow Definition Schema

```yaml
name: review
description: Full principle review pipeline
max_turns: 60           # circuit breaker — stop hook backs off after this many turns

steps:
  - uses: steps/prepare-input.yaml

  - uses: steps/load-principles.yaml

  - id: run_reviews
    prompt: |
      Run principle reviews in parallel.
      Spawn one isolated execution per principle using these params:
      Principles: {{steps.load_principles.outputs.principles}}
    depends_on: [load_principles]
    execution:
      intent: parallel_isolated
    for_each: "{{steps.load_principles.outputs.principles}}"
    outputs:
      - name: findings
        type: data
        schema_file: ./schemas/findings.schema.json

  - uses: steps/validate-findings.yaml
    depends_on: [run_reviews]

  - uses: steps/synthesize-fixes.yaml
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

### Execution Intent

Steps declare environment-agnostic intent. MCP resolves the mechanism at runtime based on the caller environment:

| Intent | Claude Code | Codex / local |
|---|---|---|
| `inline` | Same agent turn | Same agent turn |
| `parallel_isolated` | Agent tool (subagents) | New sessions |
| `sequential_isolated` | Agent tool (single subagent) | New session |

### Template Interpolation

`{{expr}}` is interpolated in `prompt`, `for_each`, and output `path` fields. Available context:

- `{{steps.<id>.outputs.<name>}}` — output value from a completed step
- `{{steps.<id>.outputs.<name> | length}}` — length filter
- `{{item}}` — current item in a `for_each` expansion
- `{{output_dir}}` — run output directory path

### Active Run Pointer

Runs live in the plugin's user data directory, derived via `solid_coder_project_dir()` from `hook_utils.py` — same slug convention used throughout the plugin (`/path/to/project` → `-path-to-project`):

```
~/.solid-coder/{project-slug}/runs/
  active.json                         ← { "run_id": "review-20260625-143022" }
  review-20260625-143022/
    events.jsonl                      ← append-only event log
    workflow.yaml                     ← snapshot of flow definition at start time
```

`active.json` is written by `flow_start` and deleted when the run reaches `done` or `timed_out`. If the file exists on session start, MCP resumes the existing run.

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

**`flow_start(flow, params?)`**
- Resolves flow definition (user path first, then plugin path)
- Creates run directory, writes `workflow.yaml` snapshot
- Writes `run_started` event to `events.jsonl`
- Writes `active.json`
- Returns `{ run_id, steps: [{ step_id, prompt, execution_intent, params? }] }` — first ready steps

**`flow_next(outputs?)`**
- Reads `active.json` to locate run
- Replays `events.jsonl` to determine current state
- If `outputs` provided: validates against declared schema; on failure returns `{ error, validation_errors }` with no state transition
- On success: appends `step_completed` event, increments turn counter
- Computes newly unblocked steps, expands `for_each` if applicable
- Returns `{ status: "ready", steps: [...] }` or `{ status: "done" }`

**`flow_status()`**
- Reads `active.json`, replays `events.jsonl`
- Returns `{ flow, run_id, status, turn_count, max_turns, completed: [...], running: [...], pending: [...] }`
- Returns `{ status: "no_active_run" }` if `active.json` absent

### Stop Hook

A Python handler `mcp-server/hooks/on_flow_stop.py`, registered in `hooks/hooks.json` under the `Stop` event alongside `on_stop.py` and `on_agent_stop.py`. Follows the same dispatcher pattern: reads from stdin, writes to stderr, exits 2 to block.

```python
# mcp-server/hooks/on_flow_stop.py

class FlowHarnessStopHandler:
    """Blocks agent stop when an active flow run is incomplete."""

    def run(self, event: dict) -> None:
        if event.get("stop_hook_active"):
            return
        project_dir = solid_coder_project_dir()
        active_path = project_dir / "runs" / "active.json"
        if not active_path.exists():
            return
        run_id = json.loads(active_path.read_text())["run_id"]
        events_path = project_dir / "runs" / run_id / "events.jsonl"
        result = replay_events(events_path)   # pure function — replays log, returns status + next_prompt
        if result["status"] in ("done", "timed_out"):
            active_path.unlink(missing_ok=True)
            return
        sys.stderr.write(f"Flow not complete. Continue:\n{result['next_prompt']}")
        sys.stderr.flush()
        sys.exit(2)
```

`hooks/hooks.json` entry:
```json
{
  "Stop": [
    { "hooks": [{ "type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/mcp-server/hooks/on_stop.py\"" }] },
    { "hooks": [{ "type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/mcp-server/hooks/on_agent_stop.py\"" }] },
    { "hooks": [{ "type": "command", "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/mcp-server/hooks/on_flow_stop.py\"" }] }
  ]
}
```

`replay_events(path)` is a pure function that reads `events.jsonl`, reconstructs state, checks turn count against `max_turns` from the snapshotted `workflow.yaml`, and returns `{ status, next_prompt }`.

### Validation at Load Time

When `flow_start` loads a flow definition, MCP validates:
- Required fields present (`name`, `steps[]`, each step has `id` + `prompt`)
- No duplicate step IDs
- All `depends_on` references exist
- No dependency cycles (topological sort)
- All `uses:` file references resolve (user path or plugin path)
- All `schema_file` references resolve relative to the step file

### DAG Validation

MCP validates the DAG at `flow_start` time:
- Topological sort to detect cycles
- `for_each` expression references a step that is a transitive dependency
- Parallel steps' `for_each` output must be an array type in its declared schema

## Test Plan

- Unit: `flow_start` creates correct `events.jsonl` and `active.json`
- Unit: `flow_next` with valid outputs appends event and returns next ready steps
- Unit: `flow_next` with invalid outputs returns validation error, no state transition
- Unit: `flow_next` respects `depends_on` — blocked steps not returned
- Unit: `for_each` expansion returns N step instances for N items
- Unit: all N parallel instances must complete before dependent step is unblocked
- Unit: replay from interrupted `events.jsonl` returns correct pending steps
- Unit: turn counter increments and `timed_out` triggers at `max_turns`
- Unit: user `steps/` file overrides plugin file of same name
- Integration: full review flow runs to `done` via MCP tools
- Integration: stop hook re-injects next step prompt on premature exit
- Integration: interrupted run resumes correctly from `active.json`

## Design Decisions

- **MCP returns NL prompts** — agents don't interpret SKILL.md checklists. The step's `prompt` field is the instruction. Prompts are static + interpolated, version-controlled in YAML.
- **Single tool loop** — `flow_next(outputs?)` is the only call agents make during a run. Calling it signals the prior step is done (if outputs provided) and requests the next. No separate `complete_step` + `get_next_steps` round-trip.
- **Active run pointer, no run_id passing** — agents never track or pass a `run_id`. `active.json` is the pointer. One active run at a time per project. Lives in `~/.solid-coder/{slug}/runs/` via `solid_coder_project_dir()` — same slug convention used throughout the plugin.
- **Stop hook is Python, not bash** — `on_flow_stop.py` follows the same `StopHandler` pattern as `on_agent_stop.py`. It reads `active.json` and replays `events.jsonl` directly — no MCP protocol call needed. Writes to stderr + exits 2 to block, matching the established dispatcher convention. Registered in `hooks/hooks.json` alongside existing Stop handlers.
- **JSONL event log** — append-only, replay-based state. No full-file rewrites. Safe for concurrent subagent writes. Resume = replay. Audit trail included.
- **Schema validation blocks transition** — `flow_next` with bad outputs returns an error and makes no state change. Agent must correct and resubmit. No `on_error` config needed — the harness enforces correctness.
- **`max_turns` is a flow-level circuit breaker** — prevents infinite loops. When exceeded, stop hook allows exit and marks run `timed_out`. No per-step retry config.
- **Extends solid-coder-pipeline** — no new MCP server. Three new tools added to the existing server.
- **Execution intent is environment-agnostic** — YAML declares `inline` / `parallel_isolated` / `sequential_isolated`. MCP resolves to subagent or new session based on runtime environment detected at `flow_start`.
- **Flow definition snapshotted at start** — `workflow.yaml` written to run directory at `flow_start`. Resume always uses the original definition, not a newer version shipped with a plugin update.
- **User harness overrides plugin** — first-match-wins by filename. User can override any built-in step or flow without forking the plugin.
