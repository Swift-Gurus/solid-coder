# Handover: Stop-hook consolidation + HookResponding fix + test-harness bug fixes + version-bumper skill (done, committed+pushed) → session-scoped run lock (next, still the original goal)

**Branch:** `main` — committed as `0a09f1e` ("refactor: wire mcp servers to transport factory" — the commit message is stale/inherited from the branch name and does not describe this session's actual content) and pushed by the user directly. Nothing from this session is pending in the working tree.

## Where this came from

Continuing from `handover-specs-wiring-test-collision-fix-and-packaging-scope.md`'s "Next session, in order" item 3 — implement the session-scoped run lock. That work requires `FlowTransitionHandler`/the Stop-hook path to have access to the event's `session_id`, which the *old* 3-separate-scripts Stop-hook architecture didn't cleanly support (the `flow_transition_gate.py` script discarded the event entirely: `lambda _event: active_gate.evaluate()`). The user rejected the idea of bolting session-awareness onto that architecture and asked for a real consolidation first. **The session-scoped lock itself is still not implemented** — this entire session was the precursor plus several real bugs found along the way while building and testing it.

## Done this session

### 1. Stop-hook consolidation — 3 separate scripts → 1 dispatcher-based entry point

Old: `hooks/on_stop.py` (Slack only), `hooks/on_agent_stop.py` (session validation, exit(2)+stderr), `hooks/flow_transition_gate.py` (flow blocking) — three independently-registered `Stop` hooks in `hooks.json`, each spawning its own process.

New, generic (reusable for future events like `PermissionRequest`), all in `mcp-server/` root unless noted:
- `hook_decision.py` — `HookDecision(allow: bool, reason: Optional[str], additional_context: Optional[str])`, frozen dataclass.
- `hook_handling.py` — `HookHandling` protocol: `should_handle(event) -> bool`, `handle(event) -> HookDecision`.
- `parallel_hook_dispatcher.py` — coordination facade: `ParallelHookDispatcher(executor, aggregator=HookDecisionAggregator())`. `.dispatch(event) -> HookDecision`.
- `concurrent_handler_executor.py` — filters handlers by `should_handle`, runs applicable ones concurrently via `ThreadPoolHandlerRunner` (one thread per handler), delegates invocation through `SafeHandlerRunner` (fail-open on exception, logs via `StderrLogger`).
- `handler_executing.py` / `handler_pool_running.py` / `safe_handler_running.py` / `hook_decision_aggregating.py` — narrow protocols backing the above.
- `hook_decision_aggregator.py` — denies if any decision denies; concatenates reasons **and** `additional_context` from every handler that provided one, not just the first (parallel fan-out, full-result aggregation — explicit design requirement).

Three Stop-specific handlers under `mcp-server/hooks/`:
- `slack_stop_handler.py` — `SlackStopHandler` wraps the existing `SlackStopNotifier` (unmodified) as a `HookHandling` adapter; `should_handle` folds in the `SOLID_CODER_SESSION_TYPE` internal-session disable check (previously a separate `ManagedSessionGuard` wrapper); never denies.
- `session_validation_handler.py` — replaces `on_agent_stop.py`. Split into `SessionStopApplicabilityChecker` (stop_hook_active / session_id presence) + `SessionStopValidator` (calls `session_registry.validate_session_stop`) + `SessionValidationHandler` facade — this split was forced by the pre-write gate's SRP finding on the combined version.
- `flow_transition_handler.py` — replaces `flow_transition_gate.py`. `FlowStopApplicabilityChecker` + `FlowStopEvaluator` (wraps `FlowTransitionGate.evaluate()`, called **exactly once** per event — critical for the 3-attempt exhaustion counter) + `FlowTransitionHandler` facade.

`hooks/on_stop.py` rewritten as the single entry point: `HookEventReader` (reuses `hook_utils.parse_json_safely`, was almost a 4th reimplementation the gate correctly flagged) → `ParallelHookDispatcher` → `StopHookResponder`. `hooks/hooks.json`'s `Stop` array reduced from 3 entries to 1.

Deleted: `hooks/on_agent_stop.py`, `hooks/flow_transition_gate.py`, `hook_utils.run_stop_hook_gate`/`StopHookEvent`/`parse_stop_hook_event` (dead once the script that used them was gone), and their now-obsolete tests.

New tests: `tests/mcp/hook_dispatch/` (22 tests — the generic primitives) + `tests/hooks/stop/` (38 tests — the three handlers, `on_stop.py`, `StopHookResponder`, plus the crown-jewel `test_flow_transition_handler_integration.py` migrated intact from the old `test_flow_transition_gate_integration.py`, including the "three blocked attempts then exhaustion allows" real on-disk lifecycle test). **New test-location convention established and saved to memory** (`project_test_directory_conventions.md`): `tests/hooks/<event>/` for event-specific handlers, `tests/mcp/<group>/` for generic dispatch infra — confirmed with the user, simpler than mirroring `tests/harness/flow_engine/`'s per-role subfolder scheme. Each cluster needs its own uniquely-named `doubles.py` (e.g. `hook_dispatch_doubles.py`, `stop_handler_doubles.py`) — two bare `doubles.py` files anywhere in the tree collide in `sys.modules` since none of these dirs have `__init__.py`.

**Verified live**: both `tests/harness/flow_engine/test_flow_transition_gate_e2e_live.py` and `test_flow_e2e_live.py` pass against a real Claude session using `--plugin-dir` (this dev repo, not the installed plugin cache).

### 2. `HookResponding` design fix — real bug found and fixed

User's design correction: `HookResponding.allow()`/`allow_with_update()` being two methods for one concept was an OCP violation. Merged into one: `allow(additional_context: str = "", updated_input: Optional[dict] = None)`. This eliminated the need for a separate `SimpleHookResponding` protocol entirely (deleted) — `StopHookResponder` now implements the same unified `HookResponding` that `HookResponder`/`HookGate` do, just ignoring `updated_input` (Stop events carry no tool_input).

Propagated through the real call chain: `HookResponder` (PreToolUse), `HookGate`, `hooks/frontmatter_correction_orchestrator.py`, `gate/write_gate_coordinator.py` (gained an extracted `ToolInputUpdater`/`ToolInputUpdating` — the gate demanded this extraction when the coordinator was touched even trivially).

**Real bug this surfaced**: `StopHookResponder.allow()` had a stray `return` after writing the `additional_context` payload, so it never called `self._exit(0)` in that branch — caught by a new test, not by inspection.

### 3. Pre-write gate spiral — encountered twice, documented, not a code issue

Two separate incidents this session where the live pre-write gate, on trivial/mechanical edits, produced an escalating chain of contradictory SRP/DRY/OCP findings (fractal decomposition of 2-line code, findings referencing classes that didn't exist in the submitted content, one finding literally reversing a design decision the gate had itself accepted minutes earlier). Per advisor consultation both times: recognized as gate-state/reasoning pathology, not real findings — held the line rather than complying with unbounded extraction, reverted the affected files to clean state, and (second incident) asked the user to clear `~/.solid-coder/<slug>/health-*` state, which cleared it immediately on the next identical-content retry. **Updated memory**: `project_gate_stale_health_state.md` now documents both the original symptom (wrong file paths in errors) and this new one (mutually contradictory SEVERE findings on byte-identical content, including self-reversal). Standing guidance unchanged: ask the user to clear it, don't try to fix it yourself, and don't comply with a fractal-decomposition demand just because it's phrased as a gate finding.

### 4. Test-harness timeout-defaulting bug — found live, fixed at the root

While live-testing the codex backend, a fixture hard-crashed with a `claude` subprocess timeout at 120s. Root cause: `tests/run_principle_tests.py --timeout` defaulted to a hardcoded `120`, completely ignoring `tests/models/<name>.toml`'s own `[llm] timeout` (codex.toml: 300, local.toml: 600 — declared specifically because those backends are slower). Fixed at the actual source of truth: `ModelProfileLoader.load()` now validates the parsed `[llm]` section through `mcp-server/health/config/llm_config.py`'s `LlmConfig` (the same class the real production gate uses), so `ModelProfile.llm["timeout"]` is *always* populated — defaulting to production's real `300` when a profile (e.g. `claude.toml`) doesn't declare one at all, exactly matching how the live gate resolves it. `--timeout` CLI default changed from `120` to `None` (explicit-override sentinel; falls back to the profile's own value when unset). 8 new tests (`test_model_profile_loader.py`, `test_harness_runner_behavior.py`).

### 5. Metric-prefix-resolution bug — found live, fixed at the root

`tests/harness/harness_factory.py` assumed a principle's metric-ID prefix always equals its folder name (`principle_name=principle_folder.name`). True for `SRP`/`DRY`/`ISP`/`LSP`/`OCP`, **false** for `frontmatter` (prefix `FM`) and `code-smells` (prefix `CS`) — so testing either principle's `health` flow silently discarded every real finding before comparison (the gate genuinely found `FM-1`, but `HealthFlowInvoker._filter_by_principle()`'s prefix check `"FM-1".startswith("FRONTMATTER-")` was always False). Neither principle had test fixtures until this session, so it was invisible. Fixed with a new `MetricPrefixResolver` (`tests/harness/metric_prefix_resolver.py`) that reads the actual prefix from `rule.md`'s `bands:` YAML section instead of guessing — wired into `harness_factory.py`, 4 new tests including one pinning the exact frontmatter→FM case.

### 6. Gate-exclusion gap — found live, fixed

The pre-write gate's `exclude` list (`.solid-coder/config.toml` + `config.local.toml`) had `tests/fixtures/**`, `tests/harness/**`, `hooks/tests/**` — but the *actual* principle-fixture convention is `tests/principles/<Principle>/fixtures/**` (per `tests/README.md`), a path none of the three patterns cover. Fixture files (deliberately-violating test content) were being reviewed by the live gate as if they were production code. Added `tests/principles/**` to both config files' exclude lists.

### 7. `frontmatter` (FM) principle — test fixtures created and verified

`tests/principles/frontmatter/{fixtures,expectations}/fixture-{1,2,3}.swift` — one type per file (multi-type-per-file fixtures trip the gate's own SRP/OCP review, since it reviews fixture content as if it were real code): fixture-1 (no frontmatter at all → FM-1), fixture-2 (frontmatter present but wrong name/category/stack/description → FM-2/3/4/5, description deliberately over-specified with algorithm detail and a named-collaborator implementation requirement to reliably trigger FM-5), fixture-3 (fully compliant). All 3 verified passing live against the real gate (claude backend) after fixes 5 and 6 above.

### 8. `version-bumper` skill — new, cross-tool

`.claude/skills/version-bumper/` (`SKILL.md` + `scripts/bump-plugin-version.py` + `scripts/tests/`) — bumps `version` across `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` together, refuses to guess if they've drifted apart, preserves existing JSON formatting. `--part {major,minor,patch}` (default `patch`) or `--set X.Y.Z`. 7 tests, subprocess-invoked against the real CLI.

Cross-tool notes (verified via docs research, not assumed): Claude Code's `${CLAUDE_SKILL_DIR}` is a Claude-only extension — the open Agent Skills standard Codex implements recommends plain relative paths instead, and there is no Codex equivalent variable. Since one shared file can't use both mechanisms, the `SKILL.md` body hardcodes the real repo-root-relative path (`.claude/skills/version-bumper/scripts/bump-plugin-version.py`) directly rather than either tool's substitution syntax — works for both since Bash runs with cwd = repo root either way. `.agents/skills/version-bumper` is a real symlink to `.claude/skills/version-bumper` (confirmed via docs that Claude Code follows skill symlinks and loads once even when reachable from two paths) so Codex's `.agents/skills/` scanner can discover the same skill with zero duplication.

Used it once for real: `1.7.7 → 1.7.8` on both manifests.

## Full regression status (all green, verified per-root per this repo's documented one-root-at-a-time pytest convention)

| Suite | Result |
|---|---|
| `mcp-server/hooks/tests` | 540 passed |
| `mcp-server/tests` | 170 passed, 4 skipped |
| `mcp-server/build/apple/tests` | 36 passed |
| `tests/harness/tests` | 69 passed |
| `tests/harness/flow_engine` (excl. 2 live files) | 289 passed |
| `tests/hooks/stop` + `tests/mcp/hook_dispatch` | 60 passed |
| `.claude/skills/version-bumper/scripts/tests` | 7 passed |

**Total: 1171 passed, 4 skipped, 0 failed**, plus 2 live e2e tests (flow + flow-transition-gate) and a partial live principle-review sweep (SRP on claude/codex/local backends, FM on claude) all confirming no regression.

## Known-unresolved / explicitly deferred

- **`ParallelHookDispatcher` generalization for `PermissionRequest`** — the two existing hooks (`allow_plugin_file_access.py`, `on_permission_request.py`) are a natural next candidate now that the Stop-event pattern is proven, but explicitly not started. No urgency.
- **Internal-packaging question** (surgical `tests/harness` rename vs. full `mcp_server` package rewrite vs. leave as-is) — still parked from the prior handover, still not decided. See `handover-specs-wiring-test-collision-fix-and-packaging-scope.md` section 3 for the full cost/benefit numbers; nothing new this session.
- **Live LSP-style sweep of the local LLM backend across the other 4 principles** (ISP, LSP, OCP, plus the FM fixtures on codex/local) — only SRP (claude/codex/local, partial) and FM (claude only) were actually run live this session; the rest of the matrix (per the user's "all flows, all backends" ask) was descoped once the local backend's infra was confirmed sound (health flow works, timeout now correctly deferred to `local.toml`'s `600`). Not a blocker, just incomplete coverage if a full live sweep is wanted later.

## Next session, in order

1. **Implement the actual original goal — the session-scoped run lock** (`active-{session_id}.json` instead of the single shared `active.json`). This is now meaningfully easier than before this session: `FlowTransitionHandler.handle(event)` already receives the full Stop-hook event dict (including `session_id`), so threading session-awareness through the Stop-hook side no longer requires any architecture change — just wiring. Remaining work:
   - Add `session_id_reader: SessionIdReading` to `ActiveRunPointerStore`, compute `active-{session_id}.json` vs `active.json` (fallback when no session id is available, preserving today's exact behavior for callers that don't have one).
   - Wire a **real** (non-stub) session ID reader into `pipeline/server.py`'s composition root — `mcp-server/harness/mcp_request_context_session_reader.py`'s `McpRequestContextSessionReader` is currently a stub that always returns `""`. Needs to bridge `CLAUDE_CODE_SESSION_ID` env var for Claude and `_meta.threadId`/`x-codex-turn-metadata.session_id` (via `get_current_call_meta()`) for Codex.
   - Update the **two** independent `ActiveRunPointerStore()` construction sites (`harness/flow_run_orchestrator_factory.py:77`, `hooks/flow_transition_evaluating.py:72` — now indirectly via `flow_transition_handler.py`'s `build_default_flow_transition_gate()`) to use the same session-aware construction, so both the MCP-tools side and the Stop-hook side agree on the same lock file for a given session.
   - `FlowTransitionHandler`/`FlowStopEvaluator` already has the event's `session_id` available (`event.get("session_id", "")`) — just needs threading into whatever `session_id_reader` shape gets chosen for the hook side (no bridging needed there, unlike the MCP-tools side).
2. Optionally: decide the packaging question (see above) — purely deferred, no urgency.
3. Optionally: generalize the dispatcher for `PermissionRequest` — no urgency, but now that a second concrete use case would exist, worth revisiting if it comes up naturally.
