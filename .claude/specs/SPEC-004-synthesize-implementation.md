---
number: SPEC-004
feature: synthesize-implementation
status: draft
blocked-by: [SPEC-002, SPEC-003]
blocking: [SPEC-001]
---

# /synthesize-implementation — Implementation Plan Creator

## Description

As the `/implement` orchestrator, I need a sub-skill that takes the architect's decomposition, the validator's codebase findings, and the original spec — then produces a concrete, ordered implementation plan that `/code` can execute.

The synthesizer is the reconciliation point. It resolves conflicts between what the architect designed and what the validator found in the codebase.

## Flow

```
Input: spec, arch.json, validation.json
          │
          ▼
┌───────────────────────────────────┐
│ 1. Reconcile arch + validation    │
│    - reuse → no action needed     │
│    - create → plan new file(s)    │
│    - adjust → plan modifications  │
│    - conflict → resolve, document │
└──────────┬────────────────────────┘
           │
           ▼
┌───────────────────────────────────┐
│ 2. Order actions                  │
│    - Protocols/interfaces first   │
│    - Data models second           │
│    - Implementations third        │
│    - Wiring/composition last      │
└──────────┬────────────────────────┘
           │
           ▼
┌───────────────────────────────────┐
│ 3. Generate plan items            │
│    - Each item = one /code call   │
│    - file path + directive        │
│    - Dependencies between items   │
└──────────┬────────────────────────┘
           │
           ▼
Output: plan.json
```

## Requirements

### REQ-1: Reconciliation

- REQ-1.1: `reuse` components — emit no plan item. Reference existing file in notes.
- REQ-1.2: `create` components — emit plan item(s) to create file(s) with full type description from arch.json.
- REQ-1.3: `adjust` components — emit plan item(s) to modify existing file(s). Directive includes specific changes from validation.json adjustments.
- REQ-1.4: `conflict` components — synthesizer decides: prefer existing type and adapt the architecture around it, OR create new type with different name. Document the decision and reasoning.
- REQ-1.5: If validation listed multiple matches for one component, synthesizer picks the best fit (highest `match_confidence`) and documents why.

### REQ-2: Ordering

- REQ-2.1: Plan items are ordered by dependency — a type must be created before types that depend on it.
- REQ-2.2: Order: protocols → data models → implementations → views → composition root / wiring.
- REQ-2.3: Each plan item declares its `depends_on` (list of other plan item IDs that must complete first).

### REQ-3: Plan Item Format

- REQ-3.1: Each plan item is a directive for `/code`:
  ```json
  {
    "id": "plan-001",
    "action": "create",
    "file": "Sources/Network/ProductFetchService.swift",
    "directive": "Create ProductFetchService conforming to ProductReading protocol. Implements fetchAll() and fetchByCategory(_:). Uses URLSession for networking. See arch.json component 'ProductFetchService' for full responsibility.",
    "depends_on": ["plan-000"],
    "component": "ProductFetchService",
    "notes": "New file — no existing type found"
  }
  ```
- REQ-3.2: For `adjust` actions:
  ```json
  {
    "id": "plan-002",
    "action": "modify",
    "file": "Sources/Network/ProductFetchService.swift",
    "directive": "Add fetchByCategory(_: String) async throws -> [Product] to ProductReading protocol and implement in ProductFetchService.",
    "depends_on": [],
    "component": "ProductFetchService",
    "notes": "Existing file. Non-breaking change — no consumers use fetchByCategory yet."
  }
  ```

### REQ-4: Output Schema

- REQ-4.1: `plan.json` structure:
  ```json
  {
    "spec_summary": "one-line summary",
    "plan_items": [ ... ],
    "reconciliation_decisions": [
      {
        "component": "ProductCache",
        "decision": "skip — existing ProductFetchService has built-in caching",
        "reason": "Validator found conflict: redundant with existing caching in ProductFetchService"
      }
    ],
    "execution_order": ["plan-000", "plan-001", "plan-002", "plan-003"],
    "summary": {
      "create": 3,
      "modify": 2,
      "skip": 1
    }
  }
  ```

### Edge Cases

- EC-1: All components already exist (`reuse`) — plan.json has zero plan items. Orchestrator reports "nothing to implement."
- EC-2: Circular dependency between components — synthesizer must break the cycle (e.g., use a protocol to decouple) and document the decision.
- EC-3: Adjustment is breaking — synthesizer includes additional plan items to update affected consumers.
- EC-4: Spec requires modifying a type that also needs creation of new dependents — order creation before modification.

## Definition of Done

- [ ] Sub-skill exists with `user-invocable: false`
- [ ] Accepts `spec` + `arch.json` + `validation.json` as input
- [ ] Reconciles architecture with validation findings
- [ ] Resolves conflicts without looping back to architect
- [ ] Orders plan items by dependency
- [ ] Each plan item is a valid `/code` directive with file path
- [ ] Documents reconciliation decisions
- [ ] Produces `plan.json` matching the output schema
- [ ] Handles edge case of zero plan items (everything exists)
