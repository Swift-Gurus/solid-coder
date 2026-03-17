---
number: SPEC-004
feature: synthesize-implementation
status: draft
blocked-by: [SPEC-002, SPEC-003, SPEC-006]
blocking: [SPEC-001]
---

# /synthesize-implementation — Implementation Plan Creator

## Description

A sub-skill that takes the architect's decomposition and the validator's codebase findings, then produces a concrete, ordered implementation plan that `/code` can execute.

The synthesizer is the reconciliation point. It resolves conflicts between what the architect designed and what the validator found in the codebase.

## Inputs / Outputs

- **Input**: `arch.json` path + `validation.json` path + `--output` path + `--refs-root` path (principle references directory)
- **Output**: `implementation-plan.json` — ordered list of `/code` directives with dependency tracking and reconciliation decisions

No raw spec needed — `arch.json` already contains `spec_summary` for context. Principles are loaded for informed decision-making but NOT embedded in the output — the `/code` agent loads its own principles at execution time.

## Input Schemas

- **`arch.json`** (from `/plan`, SPEC-002): see `skills/plan/arch.schema.json`
- **`validation.json`** (from `/validate-plan`, SPEC-003): see `skills/validate-plan/validation.schema.json`

## Flow

```
Input: arch.json, validation.json, --refs-root
          │
          ▼
┌───────────────────────────────────┐
│ 0. Discover & load principles     │
│    - Collect stack tags from      │
│      arch.json components         │
│    - discover-principles          │
│    - Load rule.md, fix/           │
│      instructions.md, examples    │
│    (used for decisions, NOT       │
│     embedded in output)           │
└──────────┬────────────────────────┘
           │
           ▼
┌───────────────────────────────────┐
│ 1. Reconcile arch + validation    │
│    - reuse → no action needed     │
│    - create → plan new file(s)    │
│    - adjust → plan modifications  │
│    - conflict → resolve, document │
│    - breaking → add consumer fixes│
│    - data_models → search & reuse │
│    - wiring → composition root    │
└──────────┬────────────────────────┘
           │
           ▼
┌───────────────────────────────────┐
│ 2. Order actions                  │
│    - Protocols/interfaces first   │
│    - Data models second           │
│    - Implementations third        │
│    - Views fourth                 │
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
Output: implementation-plan.json
```

## Requirements

### REQ-0: Principle Discovery & Loading

The synthesizer loads principle knowledge to make informed reconciliation decisions and write good directives — but does NOT embed constraints into the implementation-plan.json output. The `/code` agent loads its own principles at execution time.

- REQ-0.1: Collect all `stack` values from `arch.json` components into a flat, deduplicated list of tags (e.g., `["swiftui", "combine", "structured-concurrency"]`).
- REQ-0.2: Use skill **solid-coder:discover-principles** with `--refs-root <refs-root>` and `--matched-tags <comma-separated tags>`. If no stack tags exist, omit `--matched-tags` to get only always-active (tagless) principles.
- REQ-0.3: For each active principle, follow the same loading pattern as `synthesize-fixes` Phase 2:
  1. Use skill **solid-coder:parse-frontmatter** on `rule.md` to extract `examples` paths
  2. Use skill **solid-coder:load-reference** to load the `examples` paths from step 1
  3. Use skill **solid-coder:load-reference** to load `rule.md` and `fix/instructions.md`
- REQ-0.4: Build a lookup: `principle_id → { rule, fix_instructions, examples }` for use in reconciliation.
- REQ-0.5: Loaded principle knowledge informs:
  - Conflict resolution decisions (REQ-1.6) — prefer types that already satisfy principle constraints
  - Breaking change assessment — whether an adjustment violates principle rules
  - Directive quality — writing directives that describe the right patterns (e.g., "inject via protocol" not "use singleton")

### REQ-1: Reconciliation

- REQ-1.1: `reuse` components — emit no plan item. Record in `reconciliation_decisions` with the existing file path.
- REQ-1.2: `create` components — emit plan item(s) to create file(s) with full type description from `arch.json`.
- REQ-1.3: `adjust` components — emit plan item(s) to modify existing file(s). Directive includes the concrete actions from `validation.json` `adjustments[].detail`.
- REQ-1.4: `conflict` components — apply the conflict resolution rule (REQ-1.6). Document the decision and reasoning in `reconciliation_decisions`.
- REQ-1.5: If validation listed multiple matches for one component (`matches[]` has >1 entry), use `matches[0]` — the array is sorted by `match_confidence` descending. Document the choice in `reconciliation_decisions`.

### REQ-1.6: Conflict Resolution Rule

Prefer existing type when ALL of the following are true:
- `match_confidence` is `high`
- Number of `adjustments[]` on the best match is ≤ 2

Otherwise, create a new type with a differentiated name. Document the decision:
- If rejected due to low confidence: "Existing type has different purpose"
- If rejected due to too many adjustments: "Existing type needs too many changes — cheaper to create new"

### REQ-1.7: Breaking Change Handling

When an `adjust` component has any adjustment with `breaking: true`:
- Generate the primary plan item for the adjustment itself
- For each file in `affected_files[]`, generate an additional plan item (action: `fix-consumer`) to update the call site
- Consumer fix items `depends_on` the adjustment item (adjustment must land first)
- Consumer fix directive describes the specific interface change the consumer must adapt to

### REQ-1.8: Data Model Reconciliation

`validation.json` includes a `data_models[]` array (added by SPEC-006) with the same `create`/`reuse`/`adjust` classification as components. The synthesizer processes them identically to components:

- REQ-1.8.1: `reuse` data models — emit no plan item. Record in `reconciliation_decisions`.
- REQ-1.8.2: `adjust` data models — emit a `modify` plan item. Directive includes the field delta from `validation.json` (`field_delta.missing`, `field_delta.type_mismatch`).
- REQ-1.8.3: `create` data models — emit a `create` plan item for a new model file.
- REQ-1.8.4: Data model plan items are ordered before implementation components (REQ-2.2).

### REQ-1.9: Wiring & Composition Root

`arch.json` contains `wiring[]` and `composition_root` fields describing how components connect.

- REQ-1.9.1: After all component and data model plan items are generated, emit plan item(s) for the composition root — the entry point that wires dependencies together.
- REQ-1.9.2: The composition root plan item's directive describes which types to instantiate, how to inject dependencies (based on `wiring[].via`), and the assembly order.
- REQ-1.9.3: The composition root plan item `depends_on` all component plan items it wires together.
- REQ-1.9.4: If a composition root file already exists (check codebase), emit a `modify` action to extend it rather than creating a new one.

### REQ-2: Ordering

- REQ-2.1: Plan items are ordered by dependency — a type must be created before types that depend on it.
- REQ-2.2: Category order: protocols → data models → implementations → views → composition root / wiring.
- REQ-2.3: Each plan item declares its `depends_on` (list of other plan item IDs that must complete first).
- REQ-2.4: Consumer fix items (from REQ-1.7) are ordered after the adjustment they depend on.

### REQ-3: Plan Item Format

- REQ-3.1: Each plan item is a directive for `/code`:
  ```json
  {
    "id": "plan-001",
    "action": "create",
    "file": "Sources/Network/ProductFetchService.swift",
    "directive": "Create ProductFetchService conforming to ProductReading protocol. Implements fetchAll() and fetchByCategory(_:). Uses URLSession for networking.",
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
    "notes": "Existing file. Non-breaking change."
  }
  ```
- REQ-3.3: For `fix-consumer` actions (breaking changes):
  ```json
  {
    "id": "plan-003",
    "action": "fix-consumer",
    "file": "Sources/Views/ProductListViewModel.swift",
    "directive": "Update call to ProductReading.fetchAll() — method signature changed to async throws. Wrap in Task if needed.",
    "depends_on": ["plan-002"],
    "component": "ProductFetchService",
    "notes": "Consumer of breaking change in plan-002"
  }
  ```

### REQ-4: Output Schema

- REQ-4.1: A formal JSON schema must exist at `skills/synthesize-implementation/implementation-plan.schema.json` defining the `implementation-plan.json` structure. The schema is created as part of this spec's implementation.
- REQ-4.2: `implementation-plan.json` must conform to the schema. Key top-level fields:
  - `spec_summary` — from arch.json
  - `plan_items[]` — ordered list of plan items (REQ-3 format)
  - `reconciliation_decisions[]` — each entry:
    ```json
    {
      "component": "ProductFetchService",
      "validation_status": "reuse|create|adjust|conflict",
      "action": "reuse|create|modify",
      "reason": "Human-readable explanation of why this decision was made",
      "existing_file": "Sources/Network/ProductFetchService.swift or null"
    }
    ```
    `validation_status` is the status from `validation.json`. `action` is the resolved outcome: `reuse` (no plan item), `create` (new file), or `modify` (change existing). For `conflict` components, `action` is either `create` or `modify` depending on resolution (REQ-1.6).
  - `execution_order[]` — ordered list of plan item IDs
  - `summary` — counts by action type (`create`, `modify`, `fix-consumer`, `reuse`). `reuse` counts components with no plan item emitted (REQ-1.1).
- REQ-4.3: The skill creates structured output `implementation-plan.json` that corresponds to `${SKILL_DIR}/implementation-plan.schema.json`

### Edge Cases

- EC-1: All components already exist (`reuse`) — `implementation-plan.json` has zero plan items. Orchestrator reports "nothing to implement."
- EC-2: Circular dependency between components — synthesizer breaks the cycle by injecting a synthetic protocol plan item (`action: create`). Rule: break the edge where the dependency is weakest (fewest methods on the consumed protocol). Name the synthetic protocol `<Consumer>To<Provider>Bridge`. Document in `reconciliation_decisions` which edge was broken and why. If multiple cycles exist, break one edge per cycle.
- EC-3: Breaking adjustment with many consumers — generate a `fix-consumer` item for each `affected_files[]` entry. If >5 consumers, flag in notes that this is a high-impact change.
- EC-4: Spec requires modifying a type that also needs creation of new dependents — order creation before modification.
- EC-5: Conflict resolution creates a new type whose name collides with another existing type — append a distinguishing suffix and document.
- EC-6: `composition_root` is an empty string — skip wiring plan items entirely. Single-component features may not need a composition root.
- EC-7: `arch.json` or `validation.json` is malformed (missing required fields) — abort with a clear error message listing the missing fields. Do not attempt partial reconciliation.

## Agent

- **Agent wrapper**: `synthesize-implementation-agent`
- **Model**: opus (reasoning-heavy reconciliation task)
- **Tools**: Read, Write, Glob, Grep (needs codebase access for conflict resolution context)

## Dependencies on Other Skills

- **`/code` Phase 1.1** already recognizes the `file` + `directive` format — no changes needed.

## Definition of Done

- [ ] Output schema exists at `skills/synthesize-implementation/implementation-plan.schema.json`
- [ ] Sub-skill exists with `user-invocable: false`
- [ ] Agent wrapper exists at `agents/synthesize-implementation-agent.md`
- [ ] Accepts `arch.json` + `validation.json` as input (no raw spec)
- [ ] Reconciles architecture with validation findings
- [ ] Applies conflict resolution rule (confidence + adjustment count)
- [ ] Auto-generates `fix-consumer` plan items for breaking adjustments
- [ ] Resolves conflicts without looping back to architect
- [ ] Orders plan items by dependency and category
- [ ] Each plan item is a valid `/code` directive with file path
- [ ] Documents all reconciliation decisions
- [ ] Produces `implementation-plan.json` matching the output schema
- [ ] Handles edge case of zero plan items (everything exists)
