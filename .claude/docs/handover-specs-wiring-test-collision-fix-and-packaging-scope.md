# Handover: mcp_transport decomposition complete (all 4 servers wired, protocol.py deleted) + tests/harness/flow_engine collection bug (fixed) + internal-packaging scope (decision deferred)

**Branch:** `refactor/na/wire-mcp-servers-to-transport-factory` (created this session off `main`, uncommitted — `main` itself carries all the prior sessions' uncommitted decomposition work too, since `fix/Na/flow-error-handling` was fast-forward merged into it earlier).

## Where this came from

Continuing from `handover-mcp-transport-decomposition.md`'s item 1 — the one concrete blocker on finishing the `protocol.py` → `mcp_transport.py` swap was `specs/server.py`'s wiring edit repeatedly tripping the pre-write SOLID gate's full-file review (pre-existing debt: duplicated frontmatter-parsing/subprocess patterns, a dead `_maybe_chunk` stub). This session resolved that blocker.

## Done this session

### 1. `specs/server.py` wired to `mcp_server_factory`/`mcp_transport` — done, tested, live-verified

- `from protocol import MCPServer` → `from mcp_server_factory import MCPServerFactory`; `server = MCPServer(...)` → `server = MCPServerFactory().build(...)`.
- Fixed the pre-existing debt the gate kept flagging, across 4 gate rounds (each round's finding was real, not noise — see [[feedback_gate_findings_fix_dont_retry]]):
  - Deduped the two copies of frontmatter-parse-and-error-handle logic (`parse_spec` / `load_spec_context`) into `_parse_frontmatter_or_error`.
  - Replaced the local `_run()` subprocess wrapper with the project's existing shared `hook_utils.SubprocessJsonRunner(SubprocessAdapter())` (confirmed this is the established pattern — used by `hook_utils.py` re-exports, tested in `hooks/tests/test_new_hook_utils.py`), consolidated into one `_run_json_tool(cmd) -> (ok, result_or_error)` helper used by all three subprocess-calling tools (`query_specs`, `load_spec_context`, `update_spec_status`).
  - Split `load_spec_context`'s three cohesion groups (input validation, subprocess loading, text formatting) into `_resolve_spec_number` / `_load_ancestors` / `_format_spec_context`, with `load_spec_context` now a thin coordinator.
  - Removed the dead `_maybe_chunk` stub and unused `_CHUNK_SIZE` constant, and the redundant local `from pathlib import Path as _Path` shadow.
- One SRP finding (asking to split `MCPServer` itself in `mcp_transport.py` into 4 stakeholder-protocol types) was correctly rejected as a false positive — `MCPServer` already delegates each of its 4 responsibilities to a separately-injected protocol-typed collaborator (`tool_registering`, `call_meta_provider`, `transport_runner`); the finding asked for exactly the state that already exists. Did not act on it; `mcp_transport.py` is untouched.
- Fixed `tests/test_protocol.py::TestLoadSpecContextAnnotation` (broken by the wiring, since it read the old `MCPServer._tools` private dict, which the new facade doesn't expose) by dispatching a real `tools/list` RPC through `specs_server.server._transport_runner._dispatcher.dispatch("tools/list", 1, {})` instead — exercises the actual wire-format code path a real client hits, not a private-attribute peek.
- **Verified live**: all four servers (`pipeline`, `docs`, `specs`, `build/apple`) still smoke-import cleanly; `specs/server.py` specifically re-verified via direct tool calls (`parse_spec`, `query_specs('types')`, `load_spec_context()` error path) after the rewrite.
- Two gate-subprocess timeouts (300s, `claude` timed out) occurred during this work — confirmed as infra flakiness, not content findings (matches [[project_srp_gate_lessons]]); resolved on retry both times.

### 2. Real, pre-existing test-collection bug in `tests/harness/flow_engine/` — found and fixed

Per explicit instruction this session ([[feedback_no_preexisting_excuse]]): a failing/uncollectable test suite is never "pre-existing, unrelated, leave it" — always root-cause and fix it in the same session, same as a SOLID gate finding on a touched file.

**Bug:** ~65 test files under `tests/harness/flow_engine/**` (checkers/coordinators/handlers/recorders/resolvers) failed to even collect via bare `pytest` from repo root: `ModuleNotFoundError: No module named 'harness.<x>'` for every single one.

**Root cause:** `tests/harness/__init__.py` plus 6 empty `__init__.py` markers under `tests/harness/flow_engine/**` made `tests/harness` a real Python package. Since repo-root `tests/` itself has no `__init__.py`, pytest's ancestor walk for e.g. `tests/harness/flow_engine/resolvers/test_flow_loader.py` stops there and computes the dotted module name as `harness.flow_engine.resolvers.test_flow_loader` (no `tests.` prefix). Importing that name requires first importing bare `harness` — which resolves to `tests/harness` (a real package, found via pytest's own path insertion) *before* the test file's own `sys.path.insert(0, mcp-server)` line ever executes. `sys.modules['harness']` gets cached pointing at `tests/harness`, so the later `from harness.active_run_location_assembler import X` reuses the wrong cached package and fails — regardless of import mode (`prepend` or `importlib`), and regardless of `PYTHONPATH`.

**Fix:** deleted all 7 empty `__init__.py` files (`tests/harness/__init__.py` + the 6 under `flow_engine/**`). Confirmed via grep that nothing anywhere imports `tests.harness.flow_engine.*` or `flow_engine.<subdir>.*` dotted — they were pure vestigial markers, zero external references. Do not re-add `__init__.py` to any of these — that's exactly what reopens the collision. Full writeup in memory: [[project_test_directory_conventions]].

**Verified, no regressions** (every suite rerun standalone post-fix):

| Suite | Result |
|---|---|
| `tests/harness/flow_engine` (excl. 2 live `_e2e_live.py` files) | 289 passed (was: 65 files uncollectable) |
| `tests/harness/tests` | 60 passed (unchanged) |
| `mcp-server/tests` | 170 passed, 4 skipped (unchanged) |
| `mcp-server/hooks/tests` | 545 passed (unchanged) |
| `scripts/tests` | 265 passed (unchanged) |
| `skills/*/scripts/tests` | 252 passed (unchanged) |

**Total: 1581 passed, 4 skipped, 0 failed**, excluding live tests (`tests/harness/flow_engine/test_flow_e2e_live.py`, `tests/harness/flow_engine/test_flow_transition_gate_e2e_live.py`, `tests/harness/integration_tests/test_{codex,haiku,llm,opus,sonnet}.py` — these call real Claude/Codex models).

**Known remaining limitation (not fixed, explicitly out of scope by user decision):** all 5 test roots still can't run in a single combined `pytest` invocation — a *separate*, lower-stakes collision: `mcp-server/tests/conftest.py` and `tests/harness/tests/conftest.py` both compute to module name `tests.conftest` (both sit in a directory literally named `tests`). This only matters if someone tries to combine all roots into one command, which isn't how this repo's tests are actually invoked anywhere (every real reference scopes pytest to one root at a time). Not touched.

### 3. Internal-packaging root-cause investigation — scoped, decision deferred to next session

The `tests/harness` vs `mcp-server/harness` collision (and the `tests.conftest` collision above) both stem from the same structural issue: **no repo has any real Python packaging** (no `pyproject.toml`/`setup.py`/`setup.cfg` anywhere) — every cross-directory import relies on manual `sys.path.insert()` (**200 calls repo-wide**: 81 in `mcp-server/`, 90 in `tests/`, 12 elsewhere) plus bare, generic top-level names (`harness`, `tests`, `hooks`, `common`...) that only avoid colliding by accident. Confirmed other latent duplicate-name risks beyond the two already hit: `hooks/` exists at repo root *and* under `mcp-server/`; `tests/` appears in 12 different places; `server.py`/`interfaces.py`/`conftest.py`/`_path_bootstrap.py`/`models.py` are each duplicated 2-4x across directories that currently only avoid colliding by luck of which ones get imported together in a given process.

**Two options investigated:**

1. **Full installable package** (`pyproject.toml`, `pip install -e .`, rewrite every bare import to `mcp_server.harness.X` style). **Ruled out for distribution**: confirmed via `claude-code-guide` research that Claude Code's plugin install is a pure file copy/clone — no post-install hook, no dependency-resolution step, whatever `python3` is on the user's PATH gets spawned as-is. A `pip install`-dependent plugin would silently break for every user who installs it without an undocumented manual step. Also confirmed the true scope is far larger than initially estimated: **757 bare cross-module imports** of the 16 top-level dir names across `mcp-server/`+`tests/` (628 of those are `harness` alone), **plus a third, previously-invisible import class** — subdirectories like `hooks/`, `gate/`, `session/`, `output/`, `patch/` import their own siblings by bare filename (not `from hooks.X import Y`, just `from X import Y`, relying on Python auto-adding a directly-run script's own directory to `sys.path`); `hooks/` alone has 88 of these, and the pattern likely repeats across most of the other ~14 subdirs, meaning the real total is probably **1000+ import statements across ~500 files**. Plus **126 files outside `mcp-server/`** reference the literal string `"mcp-server"` (77 in `tests/`, 18 in `scripts/`, 10 specs, 9 docs, 8 skills), plus the 3 files that are actual runtime wiring (`.claude-plugin/plugin.json`, `.mcp.json`, `hooks/hooks.json`, 16 launch-path occurrences total).
2. **Surgical rename** (recommended, not yet done): rename `tests/harness` (the unrelated principle-review test-harness framework) to something specific like `tests/principle_review_harness`. Its internals already use `sys.path.insert` + bare imports via its own `conftest.py`/`_path_bootstrap.py`, not `tests.harness.X` dotted imports, so this is small and contained — it removes the only generic name currently in actual conflict, without touching `mcp-server/` (~500 files) at all.

**Decision explicitly deferred** — user asked for this handoff doc instead of picking now. Do not implement either option without the user re-confirming direction next session.

### 4. `mcp_transport.py` decomposition — fully finished this session

Continuation of the same session, same handoff doc, after the packaging scope conversation was parked. Completed items 2-4 from this doc's original "Next session" list:

- **Wired `pipeline/server.py`, `docs/server.py`, `build/apple/server.py`** to `mcp_server_factory`/`mcp_transport` — same two-line swap as `specs/server.py` (`from protocol import MCPServer` → `from mcp_server_factory import MCPServerFactory`; construction line → `MCPServerFactory().build(name, version)`). `pipeline/server.py` and `docs/server.py` took the swap cleanly, no gate findings.
- **`build/apple/server.py` hit 18 SEVERE gate findings** on the same 2-line touch (full-file re-review) — genuine pre-existing debt in an 881-line file with real subprocess/watchdog/crash-detection logic (DRY duplication across `_run_tuist_build`/`_run_xcode_build`/`_run_swift_build` and across `_run_tuist_test`/`_run_xcode_test`; SRP violations on the watchdog's three inline closures; OCP if/elif dispatch in `build()`/`test()`). Given the stakes (real process-killing/SIGKILL/crash-detection code) and this session's [[feedback_no_preexisting_excuse]] rule, fixed all 18 rather than deferring:
  - Extracted `_run_and_summarize`, `_run_logged_step`, `_xcode_target_ref`, `_finalize_test_result` to kill the DRY duplication across build/test runners — each new helper verified byte-for-byte behavior-preserving against the original inline code before writing.
  - Extracted `_run_with_watchdog`'s three inline closures (`reader`/`crash_watcher`/`stall_watcher`) into `_ProcessOutputReader`/`_CrashWatcher`/`_StallWatcher` classes — **mechanically identical** (same shared `state` dict, same timing/logic), zero behavioral change, per explicit advisor caution that this is the one extraction where a "cleaner" rewrite could introduce a real threading bug.
  - Replaced `build()`/`test()`'s if/elif dispatch with dict-based runner lookup tables (matches this file's existing all-functions style rather than introducing formal Protocol classes the gate didn't actually require once tried).
  - Added `mcp-server/build/apple/tests/test_build_test_runners.py` (36 new test cases) covering every extracted helper plus the dispatch tables, per `scripts-and-tests.md`'s "no test = not done" — there was **zero existing coverage** of the units being refactored (the pre-existing `test_crash_detection.py` only covers crash-detection/watchdog primitives, not the build/test runner functions themselves).
  - Verified against the pre-existing `test_crash_detection.py` (21 tests, including real subprocess+timing integration tests for the watchdog's crash/stall detection) throughout — this was the actual safety net for the risky closure→class extraction, not the new tests.
- **Fixed `tests/test_protocol.py`'s remaining `protocol.MCPServer` dependency** (`_server_with_tool` helper) to build via `MCPServerFactory().build(...)` and query tools via the real `tools/list` RPC dispatch instead of any private attribute.
- **Renamed `tests/test_protocol.py` → `tests/test_mcp_transport.py`** per this doc's original suggestion (module being tested is now `mcp_transport`, not `protocol`).
- **Deleted `mcp-server/protocol.py`** — confirmed zero remaining references anywhere in the repo first.
- **Two gate-subprocess 300s timeouts** hit again during this pass (on `docs/server.py`'s import swap, and on `tests/test_protocol.py`'s edit) — same known infra flakiness, resolved on retry both times, no content issue.
- **One flaky false-positive CS-2 finding** on the new `test_build_test_runners.py` (asking to split its 6 test classes into 6 separate files + a conftest.py) — contradicted the sibling `test_crash_detection.py`'s already-accepted identical 6-class-in-one-file structure; resolved on retry, confirming flakiness rather than a real convention violation.

**Full regression sweep after every step, all green, no regressions**:

| Suite | Result |
|---|---|
| `mcp-server/tests` (now incl. `test_mcp_transport.py`) | 170 passed, 4 skipped |
| `mcp-server/hooks/tests` | 545 passed |
| `mcp-server/build/apple/tests` (now incl. new file) | 36 passed |
| `tests/harness/flow_engine` (excl. 2 live files) | 289 passed |
| `tests/harness/tests` | 60 passed |
| `scripts/tests` | 265 passed |
| `skills/*/scripts/tests` | 252 passed |

**Total: 1617 passed, 4 skipped, 0 failed.** All four MCP servers (`pipeline`, `docs`, `specs`, `build/apple`) smoke-import cleanly and register their tools correctly through the new `mcp_transport`/`mcp_server_factory` stack, confirmed via direct `tools/list` RPC dispatch on each.

### 5. Live smoke test — done, both Claude and Codex, all four servers

Spawned a real Claude session (`claude --plugin-dir <repo> --allowedTools "ToolSearch mcp__..."`) and a real Codex session (`codex exec --profile solid-coder-smoke-test`, scratch profile registering all four servers with real absolute paths into this repo, deleted after the run) each calling one representative tool per server:

| Server | Tool called | Claude | Codex |
|---|---|---|---|
| `specs` | `query_specs(action="types")` | ✅ `["bug","feature","epic","subtask"]` | ✅ same |
| `docs` | `get_candidate_tags()` | ✅ real tag list | ✅ same |
| `pipeline` | `get_output_path(operation="review")` | ✅ real output_root path | ✅ same |
| `build/apple` | `detect_build_system()` | ✅ `system: unknown` (repo root, no build system — expected) | ✅ same |

All 8 calls succeeded end-to-end through the new `mcp_transport`/`mcp_server_factory` stack. On the Codex side, all `Stop` hooks also completed cleanly (no crash) during this run.

**Real bug found and fixed along the way (unrelated to the transport work, but discovered while investigating a live Codex "agent could not stop" failure the user hit separately)**: `mcp-server/health/codex/codex_profile_manager.py` built hook paths as `<plugin_root>/hooks/*.py`, but hook scripts actually live at `<plugin_root>/mcp-server/hooks/*.py` (the bare `hooks/` dir only ever contains `hooks.json`, never the scripts) — this broke the `solid-coder-health.config.toml` Codex profile's `Stop`/`SessionStart`/`PreToolUse` hook commands. Fixed the one-line path bug and added two regression tests (`test_hook_script_paths_point_at_real_files`, `test_mcp_server_paths_point_at_real_files` in `hooks/tests/test_hc_profile_toml_validity.py`) that assert generated paths point at real files on disk — neither existed before, which is exactly why this shipped undetected. Confirmed this fix self-heals automatically: `hc_codex_runner.py` calls `CodexProfileManager(...).ensure_profile()` fresh on every real health-check run, so no manual regeneration of the already-stale `~/.codex/solid-coder-health.config.toml` was needed — it will be rewritten correctly the next time the health-check flow actually runs. (Separately confirmed: OpenAI Codex has an open upstream bug, [openai/codex#16430](https://github.com/openai/codex/issues/16430), about plugin-bundled `hooks/hooks.json` discovery being unreliable — relevant background, but NOT the cause of the specific stuck session investigated here, which was fully explained by the path bug above plus a stale/incomplete plugin-cache directory the profile had been generated against.)

**Not done — explicitly still open**: items 6 and 7 below. Nothing has been committed; everything in this section is currently only on the working tree on branch `refactor/na/wire-mcp-servers-to-transport-factory`.

## Three memories worth reading before resuming

- [[feedback_no_preexisting_excuse]] — new this session: never label a failing test/build/lint/SOLID-gate-violation as "pre-existing" and defer it; always root-cause and fix in the same session, exactly as if we broke it.
- [[project_test_directory_conventions]] — updated this session with the full root-cause writeup and fix for the `tests/harness/flow_engine` collection bug; also documents the still-open `tests.conftest` combined-run limitation.
- Codex plugin hooks distribution is a known, separate open question (upstream bug openai/codex#16430) — worth its own memory if it resurfaces; not written up as one yet since this session's instance turned out to be fully explained by our own path bug + stale cache, not the upstream issue.

## Next session, in order

1. **Commit the work** — nothing from this session (or the two prior sessions' decomposition work still sitting on `main`) has been committed. Branch `refactor/na/wire-mcp-servers-to-transport-factory` is ready — code-complete, unit-test-green (1617 passed), and now live-smoke-tested on both Claude and Codex.
2. **Decide on the packaging question** (surgical rename vs. full rewrite vs. leave as-is) — see the numbers in section 3 above. Recommendation stands: surgical rename of `tests/harness` → `tests/principle_review_harness` gets the real protection at a fraction of the cost of the full rewrite. Purely deferred, not blocking anything.
3. **Then, finally, implement the actual original goal**: the session-scoped run lock (`active-{session_id}.json` instead of the single shared `active.json`). Full design already agreed with the user in an earlier session — keys off `CLAUDE_CODE_SESSION_ID` env var for Claude, `_meta.threadId`/`x-codex-turn-metadata.session_id` for Codex, falls back to today's exact `active.json` filename when neither is present. Not built at all — this whole `mcp_transport.py` decomposition detour happened before implementation of this started, two sessions ago.
