---
number: SPEC-003
feature: validate-plan
status: draft
blocked-by: [SPEC-002]
blocking: [SPEC-001]
---

# /validate-plan — Codebase Validation

## Description

As the `/implement` orchestrator, I need a sub-skill that takes the architect's decomposition and validates it against the existing codebase — finding reusable types, identifying conflicts, and annotating each component with its reuse status.

The validator does NOT redesign the architecture. It reports what exists, what fits, and what needs adjustment.

## Flow

```
Input: spec, arch.json
          │
          ▼
┌──────────────────────────────────┐
│ 1. For each component in arch:   │
│    - Grep solid-description and  │
│      solid-category for matches  │
│    - Search by type name         │
│    - Search by protocol name     │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│ 2. Classify each component:      │
│    - create: nothing exists      │
│    - reuse: exists and fits      │
│    - adjust: exists, needs changes│
│    - conflict: exists, incompatible│
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│ 3. For "adjust" components:      │
│    - List specific changes needed│
│    - Check if changes break      │
│      existing consumers          │
└──────────┬───────────────────────┘
           │
           ▼
┌──────────────────────────────────┐
│ 4. For "conflict" components:    │
│    - Document why it conflicts   │
│    - Suggest alternatives        │
└──────────┬───────────────────────┘
           │
           ▼
Output: validation.json
```

## Requirements

### REQ-1: Discovery

- REQ-1.1: Search using `solid-description` and `solid-category` grep — this is the primary discovery mechanism.
- REQ-1.2: Also search by type name and protocol name as fallback (for types without solid-frontmatter).
- REQ-1.3: For each match, read the file to verify it actually fits the architect's described responsibility — don't match on name alone.
- REQ-1.4: Search scope is all `Sources/` in the project.

### REQ-2: Classification

- REQ-2.1: `create` — no existing type matches the responsibility. Component must be built from scratch.
- REQ-2.2: `reuse` — existing type matches responsibility AND interface. No changes needed.
- REQ-2.3: `adjust` — existing type matches responsibility but needs changes (new method, extended protocol, additional conformance).
- REQ-2.4: `conflict` — existing type has same name or overlapping responsibility but incompatible design. Cannot be reused without major rework.

### REQ-3: Adjustment Analysis

- REQ-3.1: For `adjust` components, list each change as a concrete action: "add method `fetchByCategory(_:)` to protocol `ProductReading`".
- REQ-3.2: Check if the adjustment breaks existing consumers — grep for all call sites of the affected protocol/type.
- REQ-3.3: If adjustment breaks consumers, note `"breaking": true` with affected files.

### REQ-4: Output Schema

- REQ-4.1: `validation.json` structure:
  ```json
  {
    "components": [
      {
        "name": "ProductFetchService",
        "status": "adjust",
        "existing_file": "Sources/Network/ProductFetchService.swift",
        "existing_interfaces": ["ProductReading"],
        "match_confidence": "high",
        "adjustments": [
          {
            "action": "add_method",
            "target": "ProductReading",
            "detail": "add fetchByCategory(_: String) async throws -> [Product]",
            "breaking": false
          }
        ],
        "notes": "Existing service handles fetching but lacks category filtering"
      },
      {
        "name": "ProductListViewModel",
        "status": "create",
        "existing_file": null,
        "adjustments": [],
        "notes": "No existing ViewModel for product listing"
      }
    ],
    "summary": {
      "create": 3,
      "reuse": 1,
      "adjust": 2,
      "conflict": 0
    }
  }
  ```

### Edge Cases

- EC-1: Multiple existing types match a single architect component — list all matches, rank by `match_confidence`, let synthesizer decide.
- EC-2: Architect proposes splitting what is currently one monolithic type — classify as `adjust` with note about extraction.
- EC-3: No solid-frontmatter in codebase yet — fall back to type/protocol name search only.
- EC-4: Architect component is a leaf view — skip deep validation, leaf views are cheap to create.

## Definition of Done

- [ ] Sub-skill exists with `user-invocable: false`
- [ ] Accepts `spec` + `arch.json` as input
- [ ] Greps `solid-description` and `solid-category` for discovery
- [ ] Falls back to type/protocol name search
- [ ] Classifies each component as `create`, `reuse`, `adjust`, or `conflict`
- [ ] For `adjust`: lists concrete changes and checks for breaking consumers
- [ ] Produces `validation.json` matching the output schema
- [ ] Handles codebases with and without solid-frontmatter
