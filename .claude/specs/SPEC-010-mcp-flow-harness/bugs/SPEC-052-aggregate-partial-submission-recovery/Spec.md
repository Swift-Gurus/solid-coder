---
number: SPEC-052
feature: aggregate-partial-submission-recovery
type: bug
status: complete
parent: SPEC-010
blocked-by: [SPEC-045]
blocking: [SPEC-036]
---

# Aggregate Partial Submission Hides Actionable Validation Errors

## Description

An aggregate workflow can persist valid assignments and reject invalid siblings, then expose an item-specific nested `for_each` through duplicate aggregate addresses while rebuilding its remaining work. The resulting internal error hides the rejected addresses and recovery instructions, so the run remains `in_progress` and the gate blocks without explaining what JSON must be corrected.

## Steps to Reproduce

1. Start an aggregate workflow containing dynamically expanded nested rule workflows for several labeled items.
2. Submit one aggregate JSON object in which most assignments are valid and multiple assignments violate their declared output schemas.
3. Let the engine persist the valid assignments, execute its engine-owned work, and make an item-specific nested `for_each` ready alongside the rejected assignments.
4. Observe: the response reports `Aggregate item, workflow, and step addresses must be unique` instead of the rejected assignments and their validation errors.

## Expected vs Actual

| | Behavior |
|---|---|
| Expected | Item-specific nested fan-out retains its existing non-aggregate execution semantics. Valid aggregate assignments remain saved. The aggregate response identifies each rejected or still-missing item, workflow, and step; explains the exact validation error; states how to correct it; and instructs the model to submit one JSON object containing only the partial subset represented by the returned schema. |
| Actual | Rebuilding the aggregate turn raises an internal duplicate-address error. The model cannot tell which values failed, how to correct them, or whether to resend the complete original JSON. |

## Affected Component

Aggregate flow execution in the MCP flow harness, specifically reconstruction of the ready aggregate frontier and model-facing rendering after a partially valid submission.

## Root Cause

After partial validation, completed original steps are persisted correctly and invalid steps retain their rejection reasons. A newly ready nested `for_each` step is incorrectly treated as one aggregate authored step even though each iteration has separately rendered item context. Because no aggregate item label was authored for that internal fan-out, every iteration receives the same fallback item, workflow, and step address; the uniqueness guard then raises an internal invariant error before the unrelated aggregate recovery instructions can be rendered. The aggregate renderer also lacks the explicit retry contract already provided by ordinary batched steps, so even a valid remaining frontier does not clearly distinguish saved assignments from the partial subset requiring resubmission.

## Fix Plan

Keep an item-specific nested `for_each` step outside aggregate compilation so its existing fan-out runner preserves separately rendered item context and never invents a shared aggregate address. Preserve exactly one pending original step for every true aggregate address when reconstructing nested work. Keep accepted assignments completed and exclude them from both the next schema and the next submission contract. Render a recovery response that lists every rejected address with its validation reason, states that accepted values are already saved, and directs the model to submit one JSON object containing only the pending or rejected subset shown by the strict schema. Initial aggregate turns retain their existing neutral submission instruction.

## Diagrams

### Connections

```text
Aggregate submission mapper
            |
            v
per-step validation --> event persistence --> ready-frontier reconstruction
                                                    |
                                                    v
                                  aggregate prompt + strict response schema
```

### Corrected flow

```text
aggregate JSON
      |
      v
validate each addressed original step
      |
      +--> valid ------> persist once --------------------+
      |                                                   |
      +--> invalid ----> record address + reason ---------+--> rebuild unique pending frontier
                                                                  |
                                                                  v
                                                partial-only schema and correction guidance
```

### Recovery sequence

```text
Model               Flow engine                 Event log
  | aggregate JSON       |                          |
  |--------------------->|                          |
  |                      | persist valid ---------->|
  |                      | record rejected -------->|
  | partial-only schema  |                          |
  | exact errors         |                          |
  |<---------------------|                          |
  | corrected subset     |                          |
  |--------------------->|                          |
```

## Test Plan

### Regression Tests

- When a nested aggregate rule turn accepts some assignments and rejects several siblings, processing the submission returns one unique pending address per rejected step without an internal duplicate-address error.
- When engine-owned work makes an item-specific nested `for_each` ready, that fan-out retains ordinary execution and does not create duplicate aggregate addresses.
- When an aggregate submission contains invalid values, rendering the continuation names every rejected item, workflow, and step, includes each validation reason, and says to resubmit only the partial JSON subset shown by the returned schema.

### Related Tests

- When an aggregate submission omits an assignment without submitting an invalid value, the accepted assignments remain saved and the returned schema contains only the missing assignment.
- When a corrected partial submission is accepted, completed siblings are not reopened or duplicated in the event log.
- When an initial aggregate turn has no previous rejection, the renderer uses the ordinary full-submission instruction and does not claim that earlier assignments were saved.
- When replay reconstructs a partially completed aggregate run, it presents the same unique pending subset and retained rejection reasons.

## Definition of Done

- [x] The deterministic nested aggregate reproduction no longer raises a duplicate-address error.
- [x] Item-specific nested `for_each` steps retain ordinary fan-out execution outside aggregate compilation.
- [x] Every rejected assignment is returned with its exact model-facing address and validation reason.
- [x] Recovery text states what must be corrected and that only the returned partial JSON subset must be submitted.
- [x] The strict schema excludes previously accepted assignments.
- [x] Corrected partial submission completes without duplicating accepted completion events.
- [x] Aggregate focused tests, all non-live tests, and locked Codex and Claude flow-engine tests pass.
