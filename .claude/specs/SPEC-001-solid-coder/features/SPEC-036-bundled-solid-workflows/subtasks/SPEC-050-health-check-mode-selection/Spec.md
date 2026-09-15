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
7. Run a controlled live A/B smoke through the actual hook using the same source
   fixture and locked model profile. Reuse existing session/fixture/evidence
   support; no alternate benchmark prompts or distributed test workflows.

## Relationships

- SPEC-036 continues to default to workflow-based gate execution. This explicit
  comparison flag is the sole opt-in legacy path; its prohibition on silent
  direct-prompt fallback remains in force.
- SPEC-041 owns prospective buffer and patch normalization.
- SPEC-047 owns the workflow gate's isolated-run lifecycle; selecting a mode does
  not introduce another lock mechanism or change run ownership.
- SPEC-049 governs object factories, cohesive packages, and retained contracts.

## Verification

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
