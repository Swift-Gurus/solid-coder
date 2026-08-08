# Handover: Session-scoped run lock, live-verified on Claude + Codex (done, uncommitted) → parked items + a new Codex flow-resolution question (next)

**Branch:** `main` — this session's work is **not yet committed**. The `Frontmatter` principle (FM-1..FM-5, fixtures, everything described in `handover-stop-hook-consolidation-and-harness-fixes.md` section 7) is already committed as `0a09f1e` and is NOT part of this diff. `git status`/`git diff HEAD` show only the files listed below.

## Where this came from

Continuing from `handover-stop-hook-consolidation-and-harness-fixes.md`'s single "Next session" item: implement the session-scoped run lock (`active-{session_id}.json` instead of one shared `active.json`). This has been the original goal chased across **five** prior handover docs (`delegate-steps-and-flow-hooks` → `flow-hooks-and-timeout-consolidation` → `mcp-transport-decomposition` → `specs-wiring-test-collision-fix-and-packaging-scope` → `stop-hook-consolidation-and-harness-fixes`), each time deferred because a prerequisite refactor surfaced first (most recently: Stop-hook consolidation needed to exist before the Stop-hook side could thread a `session_id` through at all). All prerequisites are now in place; this session built the actual feature end to end.

## Done this session

### 1. `ActiveRunPointerStore` is now session-scoped

Path computation extracted into a new `SessionScopedActivePathResolving` protocol + `SessionScopedActivePathResolver` implementation (the gate demanded this split via an SRP-3 finding — `ActiveRunPointerStore` now only does file I/O, path scoping is a separate injected collaborator). Resolves `active-{session_id}.json` when a session id is available, falls back to the exact original `active.json` filename when not — so every existing caller that constructs `ActiveRunPointerStore()` with no arguments keeps today's behavior unchanged. Also picked up two other gate-forced extractions while the class was open: JSON encode/decode now goes through the existing `JsonSerializing`/`JsonSerializer` (root-level) and `JsonLoading`/`JsonLoader` (`harness/json_loading.py`, already existed — found it before duplicating) instead of bare `json.dumps`/`json.loads`.

### 2. `McpRequestContextSessionReader` — real implementation (was a permanent stub)

Now takes a `CallMetaProviding` + optional `env` dict. Resolution order: `CLAUDE_CODE_SESSION_ID` env var (Claude) → `threadId` on the current call's `_meta` (Codex) → `_meta["x-codex-turn-metadata"]["session_id"]` (Codex fallback) → `""`. **This exact env-var name and Codex meta shape were inherited as "agreed design" from `handover-mcp-transport-decomposition.md` and were never empirically re-verified this session** — see Known-unresolved below.

### 3. `StaticSessionIdReader` — new, for the Stop-hook side

The Stop-hook process gets `session_id` as a plain string already present on the parsed event (`event.get("session_id", "")`) — no live context to query, so it just wraps a fixed value. Lives in `harness/` since it implements the same `SessionIdReading` protocol as the MCP-side reader.

### 4. `FlowRunOrchestratorFactory` + new `FlowTransitionGateFactory` wired with session awareness

- `FlowRunOrchestratorFactory` gained a `session_reader: Optional[SessionIdReading] = None` constructor param (defaults to `StaticSessionIdReader()`, i.e. no scoping, preserving existing test behavior). The **same** reader instance now feeds both `ActiveRunPointerStore`'s path resolver and `OutputSubmissionAdvancer`'s `session_reader` (previously that one self-constructed a throwaway stub `McpRequestContextSessionReader()` — now shares the real one).
- `flow_transition_evaluating.py`'s module-level `build_default_flow_transition_gate()` function got flagged CS-1 the moment I added a `session_id` parameter to it (pre-existing code, first time it was ever touched). Extracted into a new `FlowTransitionGateFactory` class (own file, `mcp-server/hooks/flow_transition_gate_factory.py` — the gate then flagged CS-2 for having two classes in the *original* file, so it had to be a separate file, not just a class alongside `FlowTransitionGate`). The module-level function no longer exists; both call sites (`on_stop.py`, the integration test) now use `FlowTransitionGateFactory(...).build()` directly.

### 5. `on_stop.py` restructured to read the Stop event before building handlers

Previously `build_default_flow_transition_gate()` (now `FlowTransitionGateFactory`) was constructed before the event was ever parsed, so there was no `session_id` to give it. Fixed by calling `HookEventReader().read()` once at the top of `__main__`, extracting `session_id`, then wrapping the already-parsed event in a new `PreReadEventReader` adapter (own file, `pre_read_event_reader.py` — CS-2 forced this out of `on_stop.py` too) so `main()`'s existing `reader: StopEventReading` contract and its tests are completely unchanged.

### 6. Tests — 20 new, all passing

- `test_active_run_pointer_store.py` — 5 new tests for session-scoped filenames, two-sessions-don't-clobber, empty-session-id fallback.
- `test_session_scoped_active_path_resolver.py`, `test_static_session_id_reader.py`, `test_mcp_request_context_session_reader.py` — new unit test files (7 tests for the session reader alone, covering env-var precedence, Codex fallback, malformed `_meta` shapes, and the real-`os.environ` default path via `patch.dict` — the naive version of that last test was flaky since `CLAUDE_CODE_SESSION_ID` is actually set in this dev environment).
- `test_flow_harness_integration.py` — 2 new integration tests proving two `FlowRunOrchestratorFactory` instances with different session readers, sharing one `runs/` dir, don't collide and each only sees its own run.
- `tests/hooks/stop/test_flow_transition_handler_session_isolation.py` — new file, 1 test proving a Stop-hook gate scoped to session B allows the turn to end even while session A has a pending, unblocked flow run — the actual real-world scenario this whole feature exists to fix.

### 7. Gate friction worth remembering

- **Escalating spiral on `tests/hooks/stop/stop_handler_doubles.py`**: adding one new trivial stub class to an already-established 8-class "doubles.py" bundle (an explicitly agreed convention, not an accident) produced a **worse** finding on each of 3 identical-content retries — first a scoped split suggestion, then an unrelated DRY finding on a pre-existing class, then all 9 classes individually flagged for extraction. This matches the documented pre-write-gate-spiral pathology (`project_gate_stale_health_state.md`): retrying made it worse, not better. Worked around by keeping the new stub local to the one test file that needed it instead of touching the shared doubles file — didn't try to force the shared file through the gate.
- **One real DRY catch**: an initial local `_StubSessionReader` in the new session-isolation test file was correctly flagged as duplicating the new production `StaticSessionIdReader` — fixed by importing and reusing the production class directly instead of a parallel test double.
- **One SRP-3 false positive**: touching an unrelated function in `flow_transition_evaluating.py` caused the untouched `FlowTransitionGate` class in the same file to get re-flagged for "not having injected protocol-typed dependencies" — it already does (`status_reader`/`failure_recorder` are both constructor-injected protocols). Resolved by retrying since the finding was demonstrably wrong about the code as it stood.

## Full regression status (non-live suites only, per this repo's one-root-at-a-time convention)

| Suite | Result |
|---|---|
| `mcp-server/tests` | 170 passed, 4 skipped |
| `mcp-server/hooks/tests` (excl. e2e) | 533 passed |
| `scripts/tests` | 265 passed |
| `mcp-server/build/apple/tests` | 36 passed |
| `skills/**/scripts/tests` | 252 passed |
| `.claude/skills/version-bumper/scripts/tests` | 7 passed |
| `tests/harness/flow_engine` (excl. 2 live files) | 308 passed |
| `tests/harness/tests` | 69 passed |
| `tests/hooks/stop` | 39 passed |
| `tests/mcp/hook_dispatch` | 22 passed |

**Total: 1,701 passed, 4 skipped, 0 failed** — up from 1,681 before this session, exactly the 20 new tests. Live e2e/integration suites (`test_health_check_e2e.py`, `tests/harness/integration_tests/`, the two `*_e2e_live.py` files) were not re-run this session. A new live suite, `test_flow_session_scoping_live.py`, was added and run explicitly this session — see Live Verification below; both its tests pass as of the final prompt iteration.

## Live verification (done, after this doc was first written)

Added `tests/harness/flow_engine/test_flow_session_scoping_live.py` (not part of the fast sweep — spawns real sessions, run explicitly) and ran it against both backends:

- **Claude**: passed on the first real `claude -p` run (23s) — `CLAUDE_CODE_SESSION_ID` resolves correctly inside the MCP server subprocess.
- **Codex**: took 4 attempts to get a clean signal, all infra/prompting issues on the test's side, not the feature:
  1. First attempt hung and timed out at 180s — the known stale-global-plugin issue (`handover-flow-hooks-and-timeout-consolidation.md` section 2); my new test hadn't applied the project-scoped marketplace-override fix that `test_codex.py` already uses. Added it — fixed the hang.
  2. Second attempt: model reported "`flow_start` isn't available in this session" — my prompt referenced the bare tool name; Codex needs the full `mcp__pipeline__flow_start` reference (same convention the production health-check prompts already use in `mcp-server/prompts/health-check/workflow.md`, which I should have checked first).
  3. Third attempt: tool was found, but flow resolution failed — `Flow file not found or unreadable: 'e2e_test'`. Worked around with an absolute path instead of the bare name (see the new finding below — **this may be a real, separate bug**, not just a test issue).
  4. Fourth attempt: also failed my assertion, but for a good reason — the model ignored the "don't call other tools" instruction, drove the whole flow to completion via repeated `flow_next` calls, and `flow_next` correctly deleted the pointer file on completion before I could inspect its name. Strengthened the prompt to stop after exactly one call; on the 5th attempt it complied and the resulting pointer file was confirmed session-scoped. **Codex verified.**

**New finding, not investigated further**: attempt 3's `Flow file not found` for a bare flow name under Codex might be a real gap in flow search-path resolution (possibly the same `CLAUDE_PROJECT_DIR`-vs-cwd distinction already noted in `hc_config_core.py`), not just a test-harness quirk. Filed in `SPEC-031-flow-mcp-tools/Spec.md`'s Technical Notes — **not confirmed whether a real Codex user calling `flow_start` with a bare flow name would hit this in production.**

## Known-unresolved / explicitly deferred

- **Codex bare flow-name resolution** — see the new finding directly above. Worth a dedicated investigation: does `flow_start(flow="some_name")` (not a path) actually work for real Codex usage, or only when Codex happens to be invoked with a cwd that matches `{project}`?
- **Packaging question** (`tests/harness` rename vs. full `mcp_server` rewrite vs. leave as-is) — still parked, fourth handover in a row with zero movement. See `handover-specs-wiring-test-collision-fix-and-packaging-scope.md` section 3 for the cost/benefit numbers.
- **`ParallelHookDispatcher` generalization for `PermissionRequest`** — still not started, no urgency, now has two proven use cases (Stop) to model from if picked up.
- **Full live sweep of ISP/LSP/OCP across all backends** — only SRP (partial) and FM (claude only) were live-verified per the prior handover; not a blocker, just incomplete coverage.
- **This session's work is uncommitted.** Everything above exists only in the working tree on `main`.
- **`SPEC-031-flow-mcp-tools/Spec.md` was stale** (`status: draft` despite being fully built; acceptance criteria described the unscoped `active.json` literally) — updated this session to `status: done` and to describe the session-scoped filename.
- **`SPEC-032-agent-stop-hook/Spec.md` is significantly stale, NOT fixed this session.** Still describes a pre-consolidation design — a separate `on_flow_stop.py` script using raw stderr + exit-code-2 blocking — that no longer exists. The real implementation is `FlowTransitionHandler`/`FlowStopEvaluator` (`flow_transition_handler.py`) dispatched through the generic `ParallelHookDispatcher`/`HookDecision` mechanism inside the single consolidated `on_stop.py`, per `handover-stop-hook-consolidation-and-harness-fixes.md`. Its `status: draft` is actually correct in spirit (this exact design was never built) but misleading (the *feature* it describes — blocking main-agent stop on an incomplete flow — is done, just differently); needs a rewrite to match reality rather than a status flip.
- **`SPEC-033-subagent-stop-hook/Spec.md` describes a feature that was never built at all**, not just a stale description. `hooks.json`'s `SubagentStop` array has exactly one entry (`check_code_agent_tested.py`, matched to `solid-coder:code-agent` — an unrelated code-agent-testing check), no `on_flow_subagent_stop.py` or equivalent exists anywhere. Whether this gap matters depends on whether the `delegate` step type's `SessionDelegateRunner` already handles premature-subagent-exit synchronously (it runs the delegate call and waits for its result inline) — if so this hook may be unnecessary safety-net work rather than a real gap. Worth a deliberate decision (build it, or close SPEC-033 as superseded) rather than leaving it silently unbuilt.

## Next session, in order

1. **Commit this session's work** (session-scoped lock + the 20 unit/integration tests + the new live test + doc updates) — it's finished, green, and now live-verified on both backends, but not durable yet.
2. **Investigate the Codex bare-flow-name resolution finding** (see above) — determine whether `flow_start(flow="some_name")` genuinely fails for real Codex usage or only under this test's specific invocation shape, and fix the search-path resolution if it's real.
3. **Rewrite `SPEC-032-agent-stop-hook/Spec.md`** to describe the actual `FlowTransitionHandler`/`ParallelHookDispatcher` implementation instead of the superseded `on_flow_stop.py` design.
4. **Decide on `SPEC-033-subagent-stop-hook`**: build the SubagentStop flow-blocking hook for real, or close the spec as superseded if `SessionDelegateRunner`'s synchronous wait already covers the scenario it was meant to guard against.
5. Optionally: decide the packaging question (see above) — purely deferred, no urgency.
6. Optionally: generalize the dispatcher for `PermissionRequest` — no urgency.
