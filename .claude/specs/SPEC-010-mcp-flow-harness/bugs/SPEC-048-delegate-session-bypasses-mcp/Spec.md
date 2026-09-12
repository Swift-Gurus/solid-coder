---
number: SPEC-048
feature: delegate-session-bypasses-mcp
type: bug
status: draft
parent: SPEC-010
blocked-by: []
blocking: [SPEC-037]
---

# Delegate Session Bypasses MCP and Writes Run State into the Project

## Description

A `type: delegate`, `mode: session` child may start without the flow MCP tools it was instructed to use. The runner currently does not prove that the configured flow server registered successfully and does not prevent the child model from using general filesystem or shell tools. When the expected MCP tools are unavailable, the model can inspect the repository, import flow-engine implementation classes directly, construct its own run-directory resolver, and simulate the requested child workflow.

This fallback is invalid. It bypasses the model-facing MCP contract, makes live E2E results appear successful without exercising the deployed integration, and writes run state into the source checkout. Observed child attempts created both `<project>/runs/subagents/<run-id>/` and `<project>/.solid-coder/runs/subagents/<run-id>/` by explicitly constructing resolvers rooted in the repository.

Production flow state belongs under `~/.solid-coder/<project-slug>/runs/`. Test evidence may be copied under the established `.solid-coder/.artifacts/test/<backend>/...` hierarchy, but neither production nor live-test execution may create operational run state beneath the repository.

## Evidence

During the shared Claude flow-engine live E2E, a delegated child received an instruction to start `e2e-session-child`. Its transcript contains no MCP flow call. Instead, it:

1. Searched the repository for `flow_start`, `flow_next`, and the child workflow YAML.
2. Read flow-engine production files.
3. Executed inline Python that imported `FlowRunOrchestratorFactory`.
4. Supplied a custom resolver rooted at `plugin_root / "runs"`.
5. In later attempts, supplied `RunsBaseDirResolver(project_dir_fn=lambda: plugin_root / ".solid-coder")`.
6. Advanced the resulting local run and returned a response that the parent delegate step could mistake for valid MCP-backed execution.

The preserved transcript is:

`/Users/crowea/.claude/projects/-Users-crowea-Developer-Swift-Gurus-solid-coder/899d099e-a7d6-4e35-a209-c45a8d859faf.jsonl`

## Steps to Reproduce

1. Run the shared live flow-engine workflow containing a `type: delegate`, `mode: session` step.
2. Allow the configured delegate backend to start without a usable flow MCP tool registration.
3. Observe the child searching the checkout for flow implementation details.
4. Observe the child invoking Python or shell commands to construct and drive a flow directly.
5. Observe new run directories beneath `<project>/runs` or `<project>/.solid-coder/runs`.
6. Observe that the outer live test can consume the child's final JSON despite MCP never being exercised.

## Expected vs Actual

| Concern | Expected | Actual |
|---|---|---|
| Delegate capability | The child receives the exact backend-callable `flow_start` and `flow_next` tools from the configured current-checkout MCP server. | The child can start without those tools and receives no deterministic capability failure. |
| Tool scope | A session delegate can use only the capabilities required to drive its child flow and produce its declared response. | General `Read` and `Bash` tools allow repository discovery and direct engine execution. |
| Missing MCP behavior | The delegate fails closed before or during its first attempted flow call. | The model improvises a non-MCP implementation. |
| Run persistence | Operational state is written only to `~/.solid-coder/<project-slug>/runs/`, with isolated children under `subagents/<run-id>/`. | Model-authored resolver construction writes into the repository. |
| Live E2E authority | Passing tests prove the configured MCP integration was used. | A test may pass after the model bypasses MCP. |
| Evidence | Backend-native evidence proves which tools were invoked. | Delegate transcripts are not correlated and asserted as part of the live contract. |

## Required Behavior

- Session-delegate construction receives the resolved project root from the owning flow composition; it must not use ambient `Path.cwd` as an implicit project identity.
- The delegate runner provides a strict MCP configuration containing the current plugin root's flow server and ignores unrelated user, project, cached-plugin, and marketplace MCP registrations.
- Backend-specific invocation guidance names the exact callable flow tools. Workflow YAML remains backend-neutral.
- General filesystem and process tools are unavailable to the child unless the delegated workflow explicitly declares a separate capability that requires them. MCP absence cannot be repaired through repository inspection.
- The child must fail closed when the required flow tools do not register, cannot be invoked, or return an incompatible response.
- A delegate result is accepted only after the correlated isolated child run reaches its authoritative terminal state through MCP. A final JSON object alone is not proof that the flow ran.
- Normal and isolated run persistence continues to use `~/.solid-coder/<project-slug>/runs/`; optional backend/model dimensions belong only in the established artifact/evidence hierarchy and must not alter project identity.
- Live E2E cleanup may remove its own canonical test runs after preserving evidence, but runtime code must never create `<project>/runs` or `<project>/.solid-coder/runs`.

## Acceptance Criteria

### AC-1: Exact MCP capability is available

Given a Claude or Codex session delegate starts, when its prompt is delivered, then the selected backend exposes the exact current-checkout `flow_start` and `flow_next` callables and the child invokes them without tool discovery or source inspection.

### AC-2: Missing MCP fails closed

Given the configured flow MCP server fails to register or its required tools are absent, when a session delegate runs, then the delegate returns a controlled infrastructure failure and performs no filesystem search, shell execution, direct engine construction, or synthetic result submission.

### AC-3: Project identity is injected

Given a parent flow belongs to a resolved project root, when it constructs a session delegate runner, then the same typed project root is supplied to the child runner and its MCP server rather than inferred from ambient process working directories.

### AC-4: Canonical persistence only

Given a session delegate starts and completes an isolated child flow, when its run state is inspected, then it exists only under `~/.solid-coder/<project-slug>/runs/subagents/<run-id>/` and neither `<project>/runs` nor `<project>/.solid-coder/runs` is created.

### AC-5: Authoritative child completion

Given the delegated model returns a schema-valid JSON response, when the parent accepts that response, then the engine has independently correlated it with the same isolated child run reaching `done`; a model-only simulation cannot satisfy the delegate step.

### AC-6: Auditable live tests

Given the shared Codex or Claude session-delegate E2E completes, when its preserved evidence is asserted, then the transcript contains the expected MCP flow calls, contains no Bash/Read fallback used to drive the flow, identifies the canonical run directory, and proves no repository-local run directory was created.

### AC-7: Existing delegate lifecycle remains intact

Given valid MCP-backed session delegates fan out over multiple items, when they complete in any order, then bounded concurrency, per-instance retries, source-ordered fan-in, replay, and downstream dependency release remain unchanged.

## Required Tests

- Unit test: the default session delegate runner receives the owning flow's injected project-directory resolver.
- Unit test: backend command construction enables strict MCP configuration and excludes fallback filesystem/process tools.
- Unit test: missing or failed flow-tool registration produces a controlled rejected `StepRunOutcome`.
- Integration test: a delegated child can start and complete only through the configured flow MCP callables.
- Integration test: a schema-valid response without correlated child completion is rejected.
- Integration test: child run state is created only beneath the user-level project slug.
- Live Codex E2E: transcript contains direct child `flow_start`/`flow_next` calls and no direct Python orchestration.
- Live Claude E2E: transcript contains direct child `flow_start`/`flow_next` calls and no Bash/Read fallback.
- Live E2E: repository-local `runs` and `.solid-coder/runs` remain absent before and after execution.
- Full non-live suite and existing flow-engine live contracts remain green.

## Affected Components

- `mcp-server/harness/session_delegate_runner.py`
- `mcp-server/harness/delegate_instruction_builder.py`
- `mcp-server/harness/flow_run_orchestrator_factory.py`
- `mcp-server/health/config/mcp_config_builder.py`
- `mcp-server/health/claude_runner_strategy.py`
- `mcp-server/health/codex_runner_strategy.py`
- `tests/harness/flow_engine/flow_engine_e2e_live_base.py`
- Shared Codex and Claude delegate-session live-test support and artifact preservation.

## Relationship to Existing Specs

- `SPEC-037` owns session-delegate fan-out and its incomplete cross-model live contract; this bug blocks that completion.
- `SPEC-038` addresses concurrent selection of the wrong run artifact, not model bypass of MCP.
- `SPEC-047` addresses isolated health-gate lifecycle and direct continuation, not `mode: session` delegate capability enforcement.

