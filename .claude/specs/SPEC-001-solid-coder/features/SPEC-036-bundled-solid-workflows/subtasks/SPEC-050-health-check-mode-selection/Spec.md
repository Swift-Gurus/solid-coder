---
number: SPEC-050
feature: health-check-mode-selection
type: feature
status: in-progress
parent: SPEC-036
blocked-by: []
blocking: []
---

# Select Legacy or Workflow Health Checking

## Description

Allow a maintainer to compare the actual legacy health prompt with the aggregated
workflow checker by changing one project configuration value. Both modes enter
through the existing pre-write hook and receive the same prospective source and
patch context. The model host and model profile remain independently configured.

```toml
[feature_flags]
flow_plain_text_response = true
health_check_mode = "workflow" # "legacy" or "workflow"
```

## Scope and Construction

- Add a typed selector under the existing feature-flags model; default to
  `workflow`, reject any other value, and preserve local-over-project precedence.
- Reuse the shared health-check service and factory contract. One object factory
  selects the implementation and its matching MCP capability profile together.
- `legacy` uses the existing principle loader, health prompt builder, review
  submission/scoring path, and `LEGACY_HEALTH` MCP profile.
- `workflow` uses `solid-gate-on-write`, its canonical aggregated file-review
  workflow, and the `GATE_FLOW` MCP profile.
- Convert the legacy construction function to an object factory and migrate its
  callers; do not retain an internal function shim or copy its construction.
- Normalize legacy results at their boundary into typed health findings consumed
  by the existing gate formatter. Preserve available reasoning, source evidence,
  and fix guidance; never invent missing evidence.
- Read configuration for the reviewed project on each invocation. Resolve the
  mode once for that invocation; changing TOML must affect a subsequent write.
- Keep write simulation, exclusions, per-file patch fan-out, atomic denial, and
  frontmatter handling shared. No automatic retry using the other mode.
- Preserve canonical operational artifacts under the user's
  `.solid-coder/<project-slug>/` directory and record the selected mode with the
  model, target identity, and source hash in existing gate audit logging.

## Acceptance Criteria

### AC-1: Configuration and Defaults

Given no selector is present, when the hook runs, then it uses `workflow`.
Given either accepted mode, when TOML is parsed, then a typed enum is produced.
Given an unknown mode or wrong type, when the gate starts, then it blocks with a
field-specific configuration error before launching a model.
Given project defaults and local overrides, when both declare the selector, then
the local value wins without discarding other feature flags.

### AC-2: Coupled Checker and Tool Selection

Given `legacy`, when a health checker is constructed, then only the legacy
checker and legacy MCP capability profile are selected.
Given `workflow`, when a health checker is constructed, then only the workflow
checker and flow-engine MCP profile are selected.
Given an unchanged LLM profile, when the mode changes, then backend, model, and
timeout remain unchanged and the next invocation reads the new mode.

### AC-3: Common Prospective Input and Gate Output

Given a new destination that does not exist, when either mode reviews a write,
then it receives the exact prospective content and path without writing it first.
Given an edit or multi-file patch, when either mode runs, then the existing
simulator and patch context supply the same source snapshots to the checker.
Given severe findings from either checker, when gate formatting runs, then typed
findings produce a useful denial including available evidence and fix guidance.
Given a completed clean review, then the gate allows the operation.

### AC-4: Failures Do Not Switch Modes

Given a timeout, missing submission, invalid output, or failed rule loading, when
the selected checker cannot complete, then the write is blocked with a diagnostic
and the other implementation is never invoked. An unavailable legacy review
must not be represented as an empty successful result.

### AC-5: Audit and Controlled Comparison

Given either mode executes, when audit evidence is inspected, then the selected
mode, backend/model, target path, and source hash identify what was reviewed.
Given an A/B experiment, when the same hook payload is replayed with only this
flag changed, then preserved evidence identifies both actual checker paths and
their model calls. Compare existing timing and token evidence; do not claim
accuracy parity merely because both processes completed.

Given a proposed comparison, when its two effective rule sets are checked, then
the experiment fixes the same reviewed target, selected principles, source and
candidate corpus, and model profile. It records each mode's effective metric
meanings and units, applicability, detection instructions, exceptions, and
severity thresholds; matching principle IDs do not imply identical semantics.
Given different rule semantics, when the results are compared, then both modes
retain their actual rules and the report presents outcomes, tokens, and time
alongside those differences. It does not rewrite legacy rules, require semantic
alignment, or attribute policy differences solely to the execution engine.
Given a comparison run, when both modes execute, then the audit
preserves the actual legacy prompt and workflow instructions, effective scoring
policy, rule/source hashes, exact source and candidate corpus, and locked model
profile. Hashes identify the evidence; they do not prove semantic equivalence.

### AC-6: Nested Applicability References

Given a file-scoped rule whose applicability reads fields of a prepared named
output inside a nested workflow, when those fields match, then the rule is
scheduled once and remains pending through replay until its outputs are supplied.
Given a nonmatching buffer, when the same rule is evaluated, then it is skipped
without creating the prospective destination.
Given a nested step-output expression, when its field exists, then the engine
resolves its value, including an explicit null; a missing field retains the full
reference in the diagnostic and remains absent for condition evaluation.
Whole-output bindings and collection-source declaration syntax remain unchanged.

## Tests and Execution Plan

1. Write failing configuration tests for default, both modes, invalid values,
   local precedence, and reloading between invocations.
2. Test the common construction boundary for matching checker/MCP selection,
   model independence, exact request forwarding, and failure isolation.
3. Test legacy result normalization against real scored-output shapes, including
   reasoning/evidence/fixes, clean output, and missing output.
4. Integrate incrementally, editing and validating one file at a time. Keep new
   tests under `tests/mcp-server/` mirroring their production capability.
5. Exercise both modes through the existing hook integration infrastructure with
   new files, edits, severe/clean results, and multi-file atomic denial.
6. Run all non-live tests, then the existing Codex/Claude flow-engine live tests.
7. Fix the comparison's common input, selected principles, and model profile,
   and record differences in metric sets, detection instructions, exceptions,
   applicability, and thresholds. Preserve both modes' actual rules.
8. Run a controlled live A/B smoke through the actual hook using the same source
   fixture and locked model profile. Reuse existing session/fixture/evidence
   support; no alternate benchmark prompts or distributed test workflows.

### Nested Applicability Tests

- When a new Swift test buffer matches the file-scoped test rule through prepared
  output fields, starting the real bundled gate schedules its aggregate review
  once, and replay reports pending work rather than completion.
- When a production buffer lacks test tags, starting the same filtered gate skips
  the test rule and leaves its destination absent.
- When a qualified step output contains nested fields or an explicit null,
  expression resolution returns those values; a missing field reports its full
  authored reference.

### As-Is Comparison Scope — 2026-10-19

The existing legacy comparison asserts principle IDs and prompt markers, which
does not establish rule equivalence. For example, legacy ISP retains conformer
coverage and a two-usage-group threshold; the bundled ISP workflow measures
definition/extension width, three independent responsibilities, and two
stakeholders. These are different review policies. The agreed experiment keeps
them unchanged and compares actual results, tokens, and time on the same input
and selected principles. Shared metrics are compared only where their meanings
match; changed or mode-specific metrics are reported separately rather than
treated as equivalent accuracy measurements. The existing real-hook workflow
smoke is execution evidence, not this pending A/B benchmark.

### Live Workflow Gate Checkpoint

This checkpoint tests workflow mode independently of the pending A/B comparison.
It calls the production pre-write hook with a fixed Write event; the hook launches
the configured model using its production prompt and MCP configuration. It does
not test an outer host's dispatch of a Write tool or multi-file apply_patch.

- When the fixed comparison source is proposed at an absent production-source
  path, running the hook with each locked Codex and Claude profile reviews the
  exact buffer without creating the destination.
- When workflow mode is selected in the isolated project's configuration, the
  audit records that mode, backend, model, source hash, and one isolated
  `solid-gate-on-write` run; no legacy fallback is accepted.
- When the model completes the review, the run contains engine-owned preparation,
  a combined submission completing multiple model steps, all seven applicable
  core rule results, and a terminal completion event.
- When the known fatal required method is reviewed, the persisted LSP-3 value is
  one with SEVERE severity, and the hook denies the write with that finding.
- When execution fails, times out, skips review, or produces only an infrastructure
  denial, the live test fails rather than counting the blocked write as success.
- When the test ends, its exact input, model profile, hook stdout/stderr, and copied
  canonical audit remain in the established backend-specific test artifact tree;
  the original user-level project audit remains available, including on failure.

The shared live entry point is
`tests/harness/flow_engine/test_solid_gate_on_write_live.py`. This checkpoint does
not establish clean-buffer allowance, multi-file atomicity, rule accuracy parity,
or the timing/token comparison required by the broader plan.

## Relationships

- SPEC-036 continues to default to workflow-based gate execution. This explicit
  comparison flag is the sole opt-in legacy path; its prohibition on silent
  direct-prompt fallback remains in force.
- SPEC-041 owns prospective buffer and patch normalization.
- SPEC-047 owns the workflow gate's isolated-run lifecycle; selecting a mode does
  not introduce another lock mechanism or change run ownership.
- SPEC-049 governs object factories, cohesive packages, and retained contracts.

## Verification

### Current status — 2026-10-19

Selection, nested applicability and real workflow-gate execution are implemented
and verified. SPEC-064's final checkpoint supersedes the intermediate failures
below: 2,900 non-live tests and 228 subtests passed, with four existing skips;
the ten targeted live cases include successful real gate runs on Codex Terra
and Claude Opus. The cache method-return gap is fixed without changing LSP rules.

Keep `in-progress` for the controlled native-rule legacy/workflow A/B comparison.
Malformed model submissions and their recovery overhead remain a separate
investigation, not a completed fix inferred from terminal gate success. Preserve
both modes' rules and report differing semantics separately when comparing their
results, timing and tokens. Historical checkpoints below remain audit evidence.

### Approved timeout retry — 2026-10-19

- With user approval, `tests/models/claude.toml` now explicitly sets
  `timeout = 1000`, matching the existing Codex test profile. This changes the
  test profile only, not the production timeout default, model, prompts, rule
  semantics, or concurrency. The earlier 300-second failure remains recorded
  below; increasing the limit is not a review-speed optimization.
- All non-live test roots passed again before the live retry: 2,877 passed,
  4 skipped, and 208 subtests passed. The focused model-profile checks also
  passed: 18 tests and 2 subtests.
- The single Claude real-hook retry passed in 420.94 seconds. The hook audit
  spans 418 seconds; its workflow events span 405.944 seconds and end in
  `run_completed`, with 19 recorded turns, 102 completed internal steps, and
  37 scored metrics. Run ID: `6f13967375b14d848ea17e35c4f11a46`.
- The hook returned nine SEVERE findings rather than an infrastructure failure.
  LSP-1 remained explicitly unavailable because two inspected expressions lack
  supported identifier bindings. Completion therefore does not establish full
  metric availability or accuracy parity.
- The Claude transcript contains four malformed-JSON tool-input errors that
  were corrected before completion. No failed-attempt events were recorded;
  those events alone do not account for submission-retry overhead. Transcript:
  `~/.claude/projects/-private-var-folders-42-g1w-3hns2js4clrz6h42v0600000gp-T-solid-coder-review-comparison-i64wq9n8/1a8c7616-ca8f-49bf-a2cc-6677dba391e9.jsonl`.
- Preserved artifacts:
  `.solid-coder/.artifacts/test/claude/e2e/gate/solid-gate-on-write/20261019T211220Z-903a90af/`.
  Its `canonical-audit-path.txt` identifies the original user-level audit.
- Parallel rule sessions remain an experiment to evaluate, not enabled behavior.
  Reuse the existing bounded session fan-out where appropriate and verify its
  actual MCP integration, including the open SPEC-048 delegate-capability issue,
  before comparing isolated rule sessions with the sequential baseline. Hold
  input, rules, and model fixed; compare wall time, summed tokens, findings,
  completion, and retry overhead. The native legacy/workflow A/B comparison is
  still pending.

### Nested applicability fix and live recheck — 2026-10-19

- Reproduced both filtered test-code gate failures before changing production
  code. The prepared file had the correct test tags, but the expression resolver
  rejected fields below a named step output, so applicability skipped the rule
  and replay incorrectly reported completion.
- Nested output expressions now reuse the shared typed step-output parser and
  nested-value resolver. Both existing gate cases pass. Additional tests cover
  nested fields, explicit null, full-reference missing-field diagnostics, and
  skipping a non-test buffer without creating its destination. No rule YAML,
  detection instructions, thresholds, or model profiles changed.
- All non-live test roots completed: 2,877 passed, 4 skipped, and 208 subtests
  passed, with no failures. This supersedes the unresolved applicability defect
  recorded in the earlier real-hook checkpoint below.
- The Codex real-hook live test passed using `tests/models/codex.toml`
  (`gpt-5.6-terra`, 1,000-second timeout). Run ID:
  `5fafe4c858044f3d9df1c327245ffe55`; artifact copy:
  `.solid-coder/.artifacts/test/codex/e2e/gate/solid-gate-on-write/20261019T195917Z-bb3c9c7d/`.
- The following Claude attempt was interrupted by the desktop/session crash
  after 81 completed steps, without a terminal workflow result. It is not a
  pass or a completed timing sample. Its preserved run ID is
  `0b09218cc1764045b19cb32404a42538`; artifact directory:
  `.solid-coder/.artifacts/test/claude/e2e/gate/solid-gate-on-write/20261019T200342Z-6aea3486/`.
- Rerunning only the interrupted Claude test produced a genuine failure in
  304.44 seconds: the child session timed out after 300 seconds with LSP type
  inspection and relationship classification still pending. The hook denied
  the write for infrastructure failure, which the test correctly rejected.
  Run ID: `5ffe0368f6d74f65bcc3bc7dbf20f3bd`; artifact copy:
  `.solid-coder/.artifacts/test/claude/e2e/gate/solid-gate-on-write/20261019T201353Z-0d3b479c/`.
- At this checkpoint the live test used `tests/models/claude.toml` (`claude-opus-4-5`), whose
  omitted timeout resolves to the production default of 300 seconds. The
  separate `tests/harness/integration_tests/models/opus.toml` declares 600
  seconds but was not the profile used here. Neither profile had been changed, and
  the failed run is not counted as a successful smoke.
- The failed Claude transcript contains 19 flow-continuation calls and two file
  reads. The observed continuation-call round trips total 5.482 seconds (maximum
  0.648 seconds), not the full 300-second session duration. Two submissions used
  output names (`evidence` and `assessment`) where a ready step identity was
  required, and one call contained malformed JSON. Claude corrected all three
  and continued. These errors are visible in the transcript even though the
  workflow event log contains no failed-attempt events. Comparison accounting
  must inspect tool responses as well as workflow events for retry overhead.
  The original transcript is
  `~/.claude/projects/-private-var-folders-42-g1w-3hns2js4clrz6h42v0600000gp-T-solid-coder-review-comparison-tma2xla7/f88563bf-8c54-4078-9080-ce31fa3bbcaf.jsonl`.
- Each artifact directory contains `canonical-audit-path.txt` identifying its
  original user-level audit. The same-hook legacy/workflow result, time, and
  token comparison remains pending; preserve both modes' native rules for it.

### Real-hook live checkpoint — 2026-10-19

- The shared live gate test passed with both existing profiles: Codex
  `gpt-5.6-terra` and Claude `claude-opus-4-5` (2 passed, 641.55 seconds total).
  Neither profile, production prompt, nor bundled workflow was modified.
- Both real hook executions completed `solid-gate-on-write`, accepted combined
  model submissions, persisted the seven applicable core rules, recorded the
  expected LSP-3 value of one with SEVERE severity, and denied the prospective
  buffer while its destination remained absent.
- Canonical run IDs are `15155d89c7084a6d9d1b1ee5fdb3ba14` (Codex) and
  `743e967e67eb4d7a841df1f41f4069ac` (Claude). Test artifact copies are under
  `.solid-coder/.artifacts/test/<backend>/e2e/gate/solid-gate-on-write/`, in
  `20261019T135704Z-328f7632` and `20261019T140253Z-d931f3ae` respectively.
  Each copy includes `canonical-audit-path.txt` identifying the original
  user-level project audit directory.
- The complete non-live check recorded 2,869 passed, 4 skipped, and 2 failures.
  Both failures are the already-recorded filtered test-code gate cases in
  `TestSolidGateOnWriteWorkflow`: new-buffer review and persisted-target replay.
  The generated applicability binding into a named output's nested fields
  remains unresolved; this live checkpoint does not close that defect.
- This is workflow-mode execution evidence, not the pending legacy/workflow
  accuracy or cost comparison. Clean-buffer allowance and outer-host tool
  dispatch are outside this checkpoint.

### Implementation checkpoint

- Added `HealthCheckMode` and the typed feature-flags field, defaulting to
  `workflow`.
- `ConfiguredHealthCheckerFactory` reloads the reviewed project's TOML for every
  request, selects exactly one checker, and builds the matching `LEGACY_HEALTH`
  or `GATE_FLOW` MCP capability profile without changing the configured model.
- The active `CodeHealthCheck` composition root now uses that selector. A focused
  hook integration test proves both modes receive the exact prospective source,
  path, session, and project root while a new destination remains unwritten.
- Legacy prompt generation, submission, scoring, and persistence remain intact.
  `LegacyHealthCheckerFactory` replaces the former module construction function,
  and `TypedLegacyViolationExtractor` adapts its dictionary-shaped boundary into
  `HealthViolation` objects. Because legacy output did not retain source evidence,
  its explicit fallback identifies that limitation per metric instead of inventing
  evidence.
- Configuration, selector, hook, legacy adapter, and migrated harness tests pass.
  The complete non-live suite passed with 1,737 tests and 4 intentional skips;
  only actual live model entry points and the model integration directory were
  excluded. Non-live live-session support tests remained included.
- The shared live flow-engine suite passed all three Codex scenarios and Claude's
  dynamic-include scenario. Claude's two classification scenarios failed before
  classification at the already-recorded delegated-session JSON boundary: both
  delegate instances twice returned output rejected as `Delegated session must
  return one JSON object`, after which each run recorded `run_failed`.
- The controlled same-source legacy/workflow A/B smoke and its timing/token
  comparison remain pending. Until that evidence is captured, this spec stays
  `in-progress` and makes no accuracy or cost-parity claim.
