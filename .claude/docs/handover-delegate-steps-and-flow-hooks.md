# Handover: delegate steps + isolated runs (done) → error handling + hooks (next)

**Status:** delegate step type + isolated run boxes built, unit-tested, and live-verified for both `mode: session` and `mode: subagent` (2026-07-24). Next session: error handling, then the flow-transition/flow-file-access hooks that got paused mid-design to do this verification.

## What shipped today

### The bug that started this

`execution.intent` / `ExecutionIntentResolver` / `ClaudeAgentTypeEnvDetector` (`mcp-server/harness/`) resolved isolated-intent steps to `mode: "subagent"` only when `os.environ.get("CLAUDE_AGENT_TYPE") == "claude-code"`. That env var does not exist — Claude Code never sets it. Confirmed empirically (`env | grep CLAUDE` in a live session shows `CLAUDE_CODE_ENTRYPOINT`, `CLAUDE_CODE_SESSION_ID`, `CLAUDE_CODE_CHILD_SESSION`, never `CLAUDE_AGENT_TYPE`). The spec itself (`SPEC-013`) hedged with "`CLAUDE_AGENT_TYPE` **or similar**" — a guess that was never verified against the real CLI. Net effect: isolated-intent steps always fell through to `mode: "session"`, and `FlowResultRenderer` only special-cased `mode: "subagent"`, so a `parallel_isolated` step just rendered as plain inline text — the agent called `flow_start` on the child flow in the *same* session, colliding with the parent's own active-run lock (`Flow run already active: ...`).

### The redesign

Replaced intent/env-detection with an explicit schema, decided at flow-authoring time (see `.solid-coder/harness/flows/e2e_test.yaml`'s `delegate` step for the reference example):

```yaml
- id: delegate
  type: delegate
  mode: subagent   # or: session
  prompt: 'Call flow_start with flow="...".'
  outputs:
    - name: child_value
      type: data
      schema: {type: integer}
  depends_on: [...]
```

- **`models.py`**: `StepDef.mode: str | None` replaces `ExecutionSpec`/`StepDef.execution`.
- **`step_shape_validator.py`** is now a pure router (`StepShapeValidator(validators: dict[str, StepFieldValidating], default)`) delegating to `AgentStepShapeValidator` / `ScriptStepShapeValidator` / `DelegateStepShapeValidator` (new, one file each) — `delegate` requires `prompt` + `mode` in `{subagent, session}`, forbids `command`.
- **`step_result_builder.py`**: `execution` dict is now computed directly from `step_def.type`/`step_def.mode` (`{"mode": step_def.mode}` for delegate, else `{"mode": "inline"}`) — no resolver, no `detected_env` threaded through anywhere (`FlowStarter`/`FlowStepper`/`ReadyStepsResolver`/`RunMetadata`/`StartupContext` all had the field removed).
- **`delegate_step_handler.py`** (new): routes by `step_def.mode`. `subagent` → delegates to the *same* `AgentStepHandler` instance already registered for `type: agent` (awaiting_input=True, rendered as an instruction for the calling LLM to act on). `session` → `SessionDelegateRunner`, which auto-executes synchronously (like a script step) by reusing the **existing** health-check gate's backend-agnostic runner factory (`mcp-server/health/hc_runner_factory.py::make_llm_runner`, already supports claude/codex/local via `[llm].backend`) — deliberately not a new claude-specific mechanism, so switching to codex needs zero new code.
- **`delegate_instruction_building.py`** (new): `build_delegate_instruction(prompt)` appends a fixed `_ISOLATION_HINT` ("pass isolated=true... keep calling flow_next until done/failed/timed_out") to whatever the flow author wrote — used by both the subagent render path and the session runner, so authors never have to hand-write that boilerplate.
- **Isolated run storage**: `runs/subagents/<run_id>/` — a self-contained box (own `active.json` + `events.jsonl`, same shape as the main run), never touching the single main-session lock. `RunInitializer.initialize(..., self_contained=True)` writes `active.json` *inside* the run's own directory instead of the shared parent. `ActiveRunLocator.locate(run_id=None)` — omitted resolves the main run (unchanged); given, resolves `runs/subagents/<run_id>/` directly (no lookup needed, already self-describing). `flow_next`/`flow_status` MCP tools gained an optional `run_id` param; `flow_start` gained `isolated: bool`. `FlowResultRenderer.render_start()` discloses `run_id` in the rendered text **only** when `result.isolated` — the main session's response is untouched (still no internal ids shown).

### Why two different mechanisms for the two modes (not solved by env detection)

Researched via a dedicated agent against docs.claude.com: **there is no protocol-level signal an MCP server can use to tell "called from main session" vs "called from a subagent"** — no session id, no `_meta`, nothing (`Task`/`Agent` calls are documented as behaving differently internally — e.g. "Claude Code backgrounds only main-conversation calls" — but that distinction never reaches the MCP layer). So isolation *has* to be decided by the flow engine at authoring time and explicitly told to whatever executes the step, via the prompt text it's handed. That's what `build_delegate_instruction` is for.

### `--bare` and the `Task`/`Agent` tool — a real, confirmed CLI constraint

`--bare` mode (used by `tests/harness/flow_engine/test_flow_e2e_live.py`, and per Anthropic's own docs the direction scripted/SDK callers are headed) **never registers the `Task`/`Agent` tool**, regardless of `--allowedTools`. Confirmed two ways: (1) live run showed `Error: No such tool available: Task. Task exists but is not enabled in this context`; (2) direct manual test with the *correct* tool name (`Agent`, confirmed via a non-bare session's own `tools` list in its init event) still failed identically under `--bare`. This means `mode: subagent` can never be exercised by a `--bare` harness — only `mode: session` can. **This session's e2e test now runs without `--bare`** (see below) specifically so `mode: subagent` could be tested at all.

### Live verification (both modes work end-to-end)

- `mode: session`: parent flow's `delegate` step spawned a nested bare session via `SessionDelegateRunner` → `make_llm_runner`, which drove `e2e_subagent_child.yaml` (2 steps) to completion in its own isolated box, while the parent continued and reached `done`. Verified via both event logs.
- `mode: subagent`: real `Task`-tool spawn confirmed (not just rendered text) — the top-level agent launched a subagent with the rendered instruction, the subagent called `flow_start(isolated=true)` and drove the child flow itself, and **the top-level agent correctly relayed a value back**: `delegate`'s own declared output (`child_value: integer`) was populated with `42` — the literal value the child flow's `child_step_two` produced — proving output-relay works through the `Task` boundary via the normal agent-type step contract (no special plumbing needed; `AgentStepHandler`/`OutputSchemaPromptAnnotator` already handle it).
- To make `delegate`'s completion ordering deterministic when using `mode: subagent` (it's a normal agent-type step now, not auto-run — so it becomes "ready" simultaneously with anything else sharing its dependencies, and the agent might address the other one first, or never get to it), `delegate`'s `depends_on` was changed from `[count_words]` to `[review]` — it now becomes ready *alone*, forcing the agent to deal with it before `summarize` (which also depends on it) can ever become ready.

## Known-unresolved: intermittent early-stop, independent of this work

Across many live runs today, the spawned top-level session sometimes calls `flow_start`, receives the `greet-1` prompt, **echoes it back verbatim (as the generic MCP wrapper text instructs: "Show the following output to the user exactly as-is... then proceed") and ends its turn** — never producing an actual greeting, never calling `flow_next`. Confirmed via transcript inspection multiple times; not a code bug — the tool call and its result are both correct every time this happens.

- Happens both with and without `--bare` (3/3 fails with `--bare` in one streak; 1 pass + 1 fail without `--bare` in another) — inconclusive on `--bare` as the cause. Most likely: the test's outer prompt is deliberately minimal (`Call flow_start with flow="e2e_test".`, no "keep calling flow_next" reminder — stripped out in an earlier session as an experiment to see if the model would continue unprompted), and nothing in what the model receives back explicitly says "now call flow_next" (that instruction only lives in `flow_start`'s tool *description*, read once before the call, not in its *result*).
- **User's explicit direction: don't fix this via more prompt tuning — this is exactly what the planned Stop hook is for.** A hook that blocks the agent from ending its turn while `flow_status()` reports `in_progress` + a pending step is the correct, durable fix (retry the same turn instead of silently completing with an abandoned flow), not another round of prompt wording changes.
- The test file has a test-local `_run_claude_non_bare()` helper (in `tests/harness/flow_engine/test_flow_e2e_live.py`, not in `hook_utils.py` — deliberately kept out of shared/production code per explicit instruction) used for the current (non-bare) invocation. `hook_utils.run_claude_bare()` itself was **not** modified.

## Next session

1. **Error handling** (user's stated priority — scope not yet defined, pick up fresh).
2. **The hooks work**, paused mid-plan for today's verification — plan file at `/Users/crowea/.claude/plans/abundant-meandering-scott.md`, needs revision given what's now confirmed:
   - `flow_transition_gate` (Stop hook): block ending the turn while `flow_status()` is `in_progress` with pending steps. This is now not just a nice-to-have but the concrete fix for the early-stop issue above.
   - `flow_transition_subagent_gate` (SubagentStop): the plan's original design disambiguated "per-step worker subagent" (exempt) vs "flow-driving subagent" (not exempt) by scanning the subagent's transcript for `flow_start`/`flow_next` tool calls. That distinction is now *concretely* meaningful — today's `mode: subagent` verification is exactly the "flow-driving subagent" case the gate needs to catch.
   - `flow_file_access_gate` (PreToolUse): block `Read`/`Grep`/`Bash cat` on flow YAML source + the run's persisted `workflow.yaml` snapshot while a run is active. Still fully applicable, untouched by today's work — the `BashReadGate` gap (only checks paths inside the project root, misses `~/.solid-coder/.../runs/...` and plugin-bundled flows) still needs closing.
   - Given `runs/subagents/<run_id>/workflow.yaml` now also exists (isolated boxes persist their own resolved snapshot the same way the main run does), the file-access gate's protected-path set should cover both `runs/` and `runs/subagents/` when checking "is this the active workflow snapshot."

## Files touched today (for reference, not exhaustive — see `git diff`)

New: `mcp-server/harness/{delegate_step_handler,delegate_step_shape_validator,agent_step_shape_validator,script_step_shape_validator,delegate_instruction_building,session_delegate_runner,session_delegate_running,isolated_run_paths,step_field_validating,step_building}.py`
Removed (dead): `mcp-server/harness/{execution_intent_resolver,execution_intent_resolving,claude_agent_type_env_detector,env_detecting}.py`
Modified: `models.py`, `step_builder.py`, `step_shape_validator.py`, `step_result_builder.py`, `ready_steps_resolver(ing).py`, `flow_starter.py`, `flow_starting.py`, `flow_stepper.py`, `flow_stepping.py`, `flow_status_reader.py`, `flow_status_reading.py`, `active_run_locator.py`, `active_run_locating.py`, `run_initializer.py`, `run_initializing.py`, `run_provisioner.py`, `run_provisioning.py`, `run_metadata.py`, `run_metadata_store.py`, `startup_context.py`, `startup_context_resolver.py`, `flow_run_orchestrator.py`, `flow_run_orchestrator_factory.py`, `flow_result_renderer.py`, `flow_start_result.py`, `pipeline/server.py`
YAML: `.solid-coder/harness/flows/e2e_test.yaml` (delegate step), `.solid-coder/harness/flows/e2e_subagent_child.yaml` (new, 2-step child flow)
Test: `tests/harness/flow_engine/test_flow_e2e_live.py` (expected sequence, timeout, non-bare local helper) + ~15 unit test files updated/added — full suite (247 flow-engine unit tests + 523 hook tests) green as of this handover.
