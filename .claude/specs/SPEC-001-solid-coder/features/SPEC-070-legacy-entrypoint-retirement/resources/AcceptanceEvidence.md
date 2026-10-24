# Acceptance evidence — 2026-10-23

This is a retrospective record for the current checkout, not an installed-client or live-model completion claim. The versioned inventory and restoration ledger is [legacy-entrypoint-retirement-2026-10-23.json](../../../../../docs/legacy-entrypoint-retirement-2026-10-23.json). Raw logs live under `.solid-coder/.artifacts/legacy-retirement/2026-10-23/` and are ignored by Git; copy them separately when transferring machines.

| Acceptance criterion | Recorded evidence | Result / limit |
|---|---|---|
| US-1.1 | `tools-before.json`, `tools-after.json`, `rpc-verification.json`: four configured servers initialize; all 18 retained descriptors compare equal. | Verified over repository MCP RPC. |
| US-1.2 | `rpc-verification.json`: four docs and ten pipeline retired calls rejected as unknown tools. | Verified over repository MCP RPC. |
| US-1.3 | `test_configured_servers_keep_flow_health_dependencies_and_apple_without_specs`; manifest/source inspection. | Both manifests omit specs; preserved server and CLI files exist. CLI spec lookup/path resolution also ran during this spec creation. |
| US-1.4 | `test_health_session_allowed_tools_remain_registered` and `test_archived_prompt_still_builds_for_explicit_legacy_verification`. | Native session allowlists remain covered; archived prompt constructs and requests batch findings. No live model session performed. |
| US-2.1 | Archive ledger hashes, byte comparison against Git baseline, and `test_disabled_entrypoints_preserve_exact_copies_outside_discovery`. | All 24 instruction copies preserved exactly; 14 skill and ten agent active filenames removed. |
| US-2.2 | Discovery/dependency checks in `test_legacy_entrypoint_retirement.py`. | 11 active skills, six plugin agents, retained project review agent, no missing retained skill dependencies. |
| US-2.3 | Versioned ledger `archived_entrypoints`, `removed_server_registrations`, and `restore`; inspection against baseline. | Restoration data present. A destructive restore/re-retire drill was not run. |
| US-3.1 | Parametrized `test_registration_policy_filters_metadata_and_invocation_but_keeps_direct_functions`; registration/source diff inspection. | Unrestricted, filtered, and empty policies pass; direct functions preserved. Handler implementations, scripts, and schemas retained except the explicitly updated harness prompt selection/permission. |
| US-3.2 | Native health/workflow rule files and Apple tool contracts unchanged in retirement diff; retained descriptors equal baseline; non-live regression suite. | Verified within checkout/non-live scope. A fresh full legacy/workflow live comparison remains unperformed and is not implied. |
| US-3.3 | Change inventory restricted to repository paths; raw summary/ledger explicitly report no installed-cache changes and no live runs. | No global machine configuration or installed plugin cache changes made. |

## Verification runs

Earlier retirement verification recorded **3,197 non-live tests + 322 subtests passed**, with four existing skips; focused verification recorded **101 tests + 14 subtests passed**. Two fewer per-server subtests reflect the specs server removal from the two host manifests; no test functions were removed or weakened.

After adding these specs and restoring the approved permission-hook exemption:

- Permission-hook tests: **18 passed**.
- Retirement contract tests: **7 passed**.
- Standard harness/hooks/integration/validators/coding/testing non-live group: **171 tests + 18 subtests passed**, including the archived-prompt test.
- Whole repository Ruff: **zero findings**, both installed 0.17.2 and project-pinned 0.17.1.
- Write gate remains enabled; no local disabling override was created for this work.

These scoped checks supplement the earlier full non-live run; they are not a second full-suite run. Spec-only changes and the local lint comment do not change runtime behavior. No live checks were run.

## Launch and infrastructure observations

- An initial `.venv/bin/ruff` invocation failed because Ruff is a standalone mise tool, not installed in that virtualenv. No dependencies were installed to change that arrangement.
- An initial ad hoc mixed test invocation failed collection on `hc_runner_factory`; the established separate-process harness test group passed unchanged. No source or test behavior was changed to make it pass.
- `mise exec -- ruff check .` returned **Operation not permitted** in the sandbox. Running the existing pinned Ruff binary directly passed. The mise launch failure is reported, not repaired; this does not establish whether it reproduces outside the sandbox.

## Spec validation close-out

See `Validation.json`, `scope-assessment.json`, and `split-plan.json` beside this file. Structural/buildability checks pass, but strict cohesion measurement recommends splitting this retrospective record into five groups. Implementation acceptance evidence above is retained; the spec stays **in-progress** while the scope findings await disposition. This does not close SPEC-036 or any other historical backlog.
