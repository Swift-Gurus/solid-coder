---
number: SPEC-068
feature: flat-array-flow-submissions
type: feature
status: done
parent: SPEC-010
blocked-by: []
blocking: []
---

# Flat Array Flow Submissions

## Description

Experiment with a simpler model-facing submission envelope without changing authored workflows, classification instructions, observation schemas, scoring, execution phases, or coverage requirements. The existing nested format remains the default. The experiment tests whether less address nesting reduces construction errors, output tokens, and elapsed time; an improvement is not assumed.

## Input / Output

- Configuration: `[feature_flags] flow_submission_format = "nested" | "flat_array"`, default `nested`, using existing project configuration precedence.
- The tool contract remains `flow_next(outputs, run_id)`. Flat mode receives `outputs: {"submissions": [{"id": "a1", "result": {"actions": []}}]}`. Each result contains the original step's named outputs, not a new rule-specific representation.
- MCP presents the corresponding assignment IDs and original output schemas. IDs address original step instances, not array positions, display names, or guessed rule names.
- Valid records enter the existing validation, persistence, scoring, and readiness path. Audit records retain original identities alongside the submitted addressing information.
- The format and ID bindings survive process restarts and retries. Changing configuration does not change an existing run's contract. Older run metadata without this choice uses nested format.

## User Stories

### US-1 — Submit the current work through a simpler envelope

As a model client, I want to submit a list of addressed results so that I do not have to reconstruct nested item, rule, and step keys.

| Scenario | Given | When | Expected |
|---|---|---|---|
| F1 | Flat mode and a combined phase with several units and rules | The phase is presented | Each original step assignment has a short unique ID and its original output schema; authored instructions remain deduplicated |
| F2 | A single step, ordinary batch, combined-rule batch, or aggregate batch | Its results are submitted in flat mode | The same original assignments complete as in nested mode |
| F3 | Flat assignments with different observation schemas | Records arrive in a different array order | MCP validates by ID and processes dependencies in engine order, not array order |
| F4 | Nested mode or omitted configuration | A run starts | Existing presentation and submissions remain unchanged |
| F5 | An unsupported format value | Configuration loads | Configuration validation rejects the value rather than silently selecting a format |

### US-2 — Preserve recovery and completeness

As a workflow author, I want simpler addressing to retain existing coverage guarantees so that missing or invalid observations cannot become completed work.

| Scenario | Given | When | Expected |
|---|---|---|---|
| R1 | Several pending assignments | Only some valid records are submitted | Those complete; the remainder are presented with their original IDs and remain pending |
| R2 | One invalid result among valid records | Existing validation runs | Valid work is retained according to current partial-submission semantics; recovery identifies the failed ID, schema path, and expected shape and requests its complete named outputs |
| R3 | A malformed envelope, duplicate ID, unknown ID, stale ID, or future ID | Submission arrives | Address/envelope validation rejects it before recording any result and explains the correction |
| R4 | Accepted and pending assignments exist | The process restarts and configuration changes | Replay restores the run's format and bindings without rerunning completed work |
| R5 | Missing assignments remain | The model tries to stop | Existing Stop enforcement blocks completion with the pending-work explanation |
| R6 | A model result precedes an MCP-owned operation | It is accepted | The operation executes normally and only the resulting next phase becomes available |

### US-3 — Compare packaging without changing the workload

As a maintainer, I want a controlled comparison so that an apparent speedup cannot come from dropping rule requirements.

| Scenario | Given | When | Expected |
|---|---|---|---|
| M1 | The real gate workflow, identical fixture and locked model profile | Nested and flat runs execute for Codex and Claude | Preserve prompts, submissions, original step completions, findings, and canonical audit locations |
| M2 | Both formats complete | Results are compared | Report wall time and engine time separately, input/cached/output tokens, accepted turns, attempted submissions, and validation/local-script failures |
| M3 | A run fails or semantic results differ | Measurements are reported | Preserve and explain the difference; do not label incomplete runs faster or claim equal accuracy from completion alone |

## Connects To

- SPEC-010: flow lifecycle, output validation, event replay, and Stop enforcement.
- SPEC-067: aggregate phases and turn diagnostics remain unchanged.
- Existing health-check feature flags and project configuration precedence.
- Existing submission mapping and result rendering capabilities; this is not a second execution engine.

## Diagrams

```mermaid
flowchart LR
  Ready[Current original assignments] --> Present[Selected presentation format]
  Present --> Model[Model results]
  Model --> Map[Address validation and original-instance mapping]
  Map --> Existing[Existing schema validation and completion]
  Existing --> Score[Existing MCP scoring and readiness]
  Score --> Ready
```

## Technical Requirements

- Freeze the format per run and preserve stable bindings without mutable process-global state.
- Do not expose hidden ready work or authorize future steps through the new envelope.
- Reuse existing rendering/submission interfaces and compose strategies in existing factories.
- Use typed internal structures; dictionaries remain JSON boundary representations only.
- Keep the flat mode opt-in in production. No bundled workflow modifications are required.
- Preserve audit output under the existing user-level project run folder; test copies remain under ignored test artifacts.

## Test Plan

- Write failing tests for configuration selection, flat presentation, and ID-to-original-result mapping before implementation.
- Exercise F1–F5 and R1–R6 through shared engine integration tests, including replay in a fresh engine instance.
- Compare canonical event results and scores between formats using deterministic submissions.
- Run the complete non-live suite, then the locked Codex and Claude real gate comparisons for M1–M3.

## Definition of Done

- [x] Configuration and presentation/submission strategies satisfy F1–F5.
- [x] Recovery, replay, and Stop integration tests satisfy R1–R6.
- [x] All non-live tests pass without exclusions introduced by this feature.
- [x] Codex and Claude comparisons preserve artifacts and report M1–M3 honestly; see [measurement report](resources/Measurement-2026-10-21.md).
- [x] Author-facing configuration documentation describes the opt-in flag and unchanged workflow contract.
