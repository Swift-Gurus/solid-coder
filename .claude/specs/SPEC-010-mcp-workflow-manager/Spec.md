---
number: SPEC-010
feature: MCP Workflow Manager
type: feature
status: draft
parent:
blocked-by: []
blocking: []
---

# MCP Workflow Manager

## Overview

Replace skill-driven orchestration (SKILL.md phase checklists executed by an LLM in its head) with an MCP server that owns workflow state. Agents execute atomic steps; the MCP resolves dependencies, handles branching, and enables resume from any interruption.

## Problem

Current pipeline orchestration has three weaknesses:

1. **No resume** — if an agent is interrupted mid-pipeline (context limit, timeout, user cancel), the run is lost. There is no way to pick up from where it stopped.
2. **State in the LLM's head** — the agent tracks "I'm on Phase 3.2" internally. This is invisible, unverifiable, and lost on interruption.
3. **Parallelism decided by prose** — SKILL.md says "launch ALL in a SINGLE message" but the LLM has to interpret this. Dependency ordering is re-derived every run from the same fixed text.

## Proposed Solution

A new MCP server (`mcp-server/workflow/server.py`) that:
- Holds workflow definitions as JSON graphs (steps + dependencies + branching)
- Creates and persists run state per execution
- Exposes three tools: `start_workflow`, `get_next_steps`, `complete_step`
- Agents loop: get steps → execute → complete → get next → repeat

## User Stories

### US-1: Resume interrupted run
As a developer, when a pipeline run is interrupted (context limit, timeout, error), I want to resume it from the last completed step so I don't re-run work that already succeeded.

**Acceptance Criteria:**
- `start_workflow` returns a `run_id`
- `get_next_steps(run_id)` returns only steps whose dependencies are complete
- If a run was interrupted, `resume_run(run_id)` returns remaining incomplete steps
- Completed step outputs are persisted and re-readable by later steps

### US-2: Dependency-aware parallelism
As an agent, when multiple steps have no dependency on each other, I want the MCP to tell me they can run in parallel so I don't have to interpret prose instructions.

**Acceptance Criteria:**
- `get_next_steps` returns a list — multiple entries = run in parallel
- Single entry = sequential
- Step B whose `depends_on: [A]` is never returned until A is complete

### US-3: Observable pipeline state
As a developer, when a run is in progress or failed, I want to inspect exactly which steps completed, which are pending, and what each step produced.

**Acceptance Criteria:**
- `get_run_status(run_id)` returns full state: completed steps with outputs, pending steps, failed steps
- State is persisted to `.solid_coder/runs/{run_id}/state.json`

## Technical Requirements

### Workflow Definition Schema

Workflow definitions are authored in **YAML** (`mcp-server/workflow/definitions/*.yaml`) and converted to JSON by the MCP at load time. YAML is the human-authoring format; JSON is the internal execution format.

```yaml
id: refactor
description: Full review → synthesize → implement pipeline
steps:
  - id: discover
    type: sequential
    action: discover_principles
    depends_on: []

  - id: prepare
    type: sequential
    action: prepare_review_input
    depends_on: [discover]

  - id: review
    type: parallel
    action: apply_principle_review
    fan_out: active_principles      # fan-out key from prior step output
    depends_on: [prepare]

  - id: validate
    type: sequential
    action: validate_findings
    depends_on: [review]

  - id: synthesize
    type: sequential
    action: synthesize_fixes
    depends_on: [validate]
    condition: has_severe_findings  # skip step if false
```

The MCP validates the definition at load time:
- Required fields present (`id`, `steps[]`, each step has `id` + `action`)
- No duplicate step IDs
- All `depends_on` references exist
- No dependency cycles (topological sort)
- `fan_out` key exists in prior step's output schema (if specified)

Step types:
- `sequential` — one instance, blocks until complete
- `parallel` — N instances fanned out over a list from prior output; all must complete before dependents run
- `conditional` — skipped if `condition` evaluates false against run state

### MCP Tools

**`start_workflow(workflow_id, params)`**
- Loads and validates the YAML definition, converts to JSON internally
- Creates run directory, writes initial event to `events.jsonl`
- Returns `{ run_id, next_steps[] }`

**`get_next_steps(run_id)`**
- Replays `events.jsonl` to reconstruct current state
- Returns steps ready to execute (all dependencies complete), with resolved inputs
- Returns empty list when workflow is complete

**`complete_step(run_id, step_instance_id, output, status)`**
- Appends a `step_completed` or `step_failed` event to `events.jsonl`
- Returns next ready steps (same as `get_next_steps`)
- `status`: `"done"` | `"failed"` | `"skipped"`

**`resume_run(run_id)`**
- Replays `events.jsonl` to find incomplete steps whose deps are satisfied
- Returns them ready to execute — no recomputation needed

**`get_run_status(run_id)`**
- Replays `events.jsonl`, returns full state snapshot: completed steps with outputs, pending, failed

### State Storage — Event Log (JSONL)

```
.solid_coder/runs/{run_id}/
  events.jsonl        — append-only event log (one JSON object per line)
  workflow.json       — snapshot of the parsed workflow definition at start time
```

`run_id` = `{workflow_id}-{timestamp}`

Each line in `events.jsonl` is one event:

```jsonl
{"ts": "2026-04-24T10:00:00Z", "event": "run_started", "workflow_id": "refactor", "params": {...}}
{"ts": "2026-04-24T10:00:01Z", "event": "step_started", "step_id": "discover", "instance_id": "discover-1"}
{"ts": "2026-04-24T10:00:05Z", "event": "step_completed", "instance_id": "discover-1", "output": {...}}
{"ts": "2026-04-24T10:00:06Z", "event": "step_started", "step_id": "prepare", "instance_id": "prepare-1"}
```

Benefits of JSONL over mutable state.json:
- **No full rewrites** — append-only, safe from partial-write corruption
- **Resume by replay** — current state = replay all events in order
- **Audit trail** — full history with timestamps, no information lost
- **Concurrent-safe** — multiple subagents appending simultaneously is safe (file append is atomic on most OS)

### MCP Tools

**`start_workflow(workflow_id, params)`**
- Creates a new run, writes initial state to disk
- Returns `{ run_id, pending_steps[] }`

**`get_next_steps(run_id)`**
- Returns steps ready to execute (all dependencies complete)
- Each step includes `action`, `inputs` (resolved from prior step outputs), `step_instance_id`
- Returns empty list when workflow is complete

**`complete_step(run_id, step_instance_id, output)`**
- Marks step complete, persists output
- Returns next ready steps (same as `get_next_steps`)

**`resume_run(run_id)`**
- Loads persisted state, returns incomplete steps whose deps are satisfied
- Enables resuming after interruption

**`get_run_status(run_id)`**
- Returns full state snapshot: completed, in-progress, pending, failed steps

### State Storage

```
.solid_coder/runs/{run_id}/
  state.json          — step statuses, metadata
  steps/
    {step_instance_id}.output.json   — persisted output per step
```

`run_id` = `{workflow_id}-{timestamp}`

### Agent Integration — Hierarchical Workflows

Any agent — main or subagent — can start and drive its own workflow. Workflows nest: a step in a parent workflow spawns a subagent that runs its own child workflow to completion, then reports back. The parent never knows what the subagent did internally.

```
main:       start_workflow("refactor", params) → run_id_A
main:       get_next_steps(run_id_A) → [step: "prepare"]
main:       execute prepare inline
main:       complete_step(run_id_A, "prepare-1", output)
main:       get_next_steps(run_id_A) → [step: "review-srp", "review-ocp", ...]  # parallel
main:       spawn subagent-srp(run_id_A, "review-srp-1", params)
            spawn subagent-ocp(run_id_A, "review-ocp-1", params)

subagent:   start_workflow("apply-principle-review", params) → run_id_B
subagent:   get_next_steps(run_id_B) → [step: "load-rules"]
subagent:   ... drives run_id_B to completion ...
subagent:   complete_step(run_id_A, "review-srp-1", output)   # reports back to parent
subagent:   exits

main:       (waits for all parallel subagents)
main:       get_next_steps(run_id_A) → [step: "validate"]
main:       ...
```

**Key properties:**
- Each level has its own `run_id` and `events.jsonl` — fully independent state
- The parent workflow step completes when the subagent calls `complete_step(parent_run_id, ...)`
- The subagent's internal workflow (`run_id_B`) is an implementation detail — parent never references it
- A subagent that doesn't need a workflow (simple step) just executes and calls `complete_step` directly — no workflow required
- Depth is unbounded — a subagent's workflow can itself spawn sub-subagents with their own workflows

**Step definition for sub-workflow steps:**
```yaml
- id: review
  type: parallel
  action: apply-principle-review    # maps to a workflow definition OR a direct action
  fan_out: active_principles
  depends_on: [prepare]
```

The `action` field maps either to a registered workflow ID or to a direct MCP tool call. The MCP resolves which at runtime.

Existing SKILL.md phase checklists are replaced by workflow definitions. Skills keep domain logic; the MCP handles ordering, dependency resolution, fan-out, and resume.

### Workflow Definitions to Migrate

Initial set of workflows to define:

| Workflow ID | Current Skill | Steps |
|---|---|---|
| `refactor` | `skills/refactor/SKILL.md` | discover → prepare → review(parallel) → validate → synthesize → implement(parallel) → iterate |
| `implement` | `skills/implement/SKILL.md` | plan → validate-plan → synthesize-impl → code(parallel) → validate-impl → refactor |
| `review` | `skills/review/SKILL.md` | wrapper over refactor with review-only flag |

### Relationship to Plan Chunking

When a workflow step is `type: parallel` with `fan_out: plan_items`, the MCP hands out chunks directly — no LLM interpretation needed. This resolves the plan chunking question: MCP decides chunk boundaries, not the agent.

## Test Plan

- Unit test: `start_workflow` creates correct initial state
- Unit test: `get_next_steps` respects dependency ordering
- Unit test: `complete_step` persists output and unlocks dependent steps
- Unit test: `resume_run` returns correct pending steps from interrupted state
- Unit test: parallel fan-out returns N step instances for N items
- Unit test: conditional step is skipped when condition is false
- Integration test: full refactor workflow runs to completion via MCP tools

## Design Decisions

- **YAML authoring, JSON execution** — YAML for human-readable workflow definitions; MCP converts to JSON at load time for internal use. Requires `pyyaml` in `requirements.txt`.
- **JSONL event log** — append-only, replay-based state. No full file rewrites. Safe for concurrent subagent writes.
- **Hierarchical workflows** — any agent (main or subagent) can start and drive its own workflow. Parent steps complete when the subagent calls `complete_step` on the parent `run_id`. Each level is self-contained with its own `events.jsonl`. Depth is unbounded.
- **Workflow definition snapshotted at start** — `workflow.json` written to run directory at `start_workflow` time. Resume always uses the original definition, not a newer version.
- **Failed steps block dependents** — `complete_step(status="failed")` prevents dependent steps from being returned by `get_next_steps`. Agent can call `retry_step` or `skip_step` to unblock.

## Open Questions

1. **Skill migration order** — migrate refactor first (most complex), then implement, then review? Or build new skills alongside existing ones?
2. **Backwards compatibility** — existing SKILL.md orchestrators continue to work during migration. Workflow manager is additive, not a hard cutover.
3. **Condition evaluation** — how does the MCP evaluate `condition: has_severe_findings`? Options: (a) agent passes a `conditions` dict in `complete_step`, (b) MCP evaluates against the step output JSON using a JSONPath expression, (c) agent calls `set_condition(run_id, key, value)` explicitly.
