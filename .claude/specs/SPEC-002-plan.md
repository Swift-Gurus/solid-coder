---
number: SPEC-002
feature: plan (architect)
status: draft
blocked-by: []
blocking: [SPEC-001]
---

# /plan — Architecture Decomposition

## Description

A sub-skill that reads a feature spec and produces a high-level architecture decomposition — what components are needed, their responsibilities, interfaces, dependencies, and how they wire together.

The architect is a **black-box**: it does NOT check the codebase for existing types. It designs the ideal solution from the spec alone. Codebase reconciliation (finding duplicates, reusing existing types) is the responsibility of the validator (SPEC-003).

When called by `/implement`, the orchestrator provides the output path. When called standalone for testing, the caller provides the output path directly.

## Input

- **spec**: a prompt string OR a filepath to a markdown spec file. If a filepath is provided, the skill reads the file. If a prompt string is provided, the skill uses it directly.
- **output-path**: filepath where `arch.json` will be written (e.g. `./arch.json` or `.solid_coder/implement-001-xxx/arch.json`). Parent directories are created automatically by the Write tool.

## Flow

```
Input: spec (prompt or markdown filepath) + output-path
          │
          ▼
┌─────────────────────────────┐
│ 1. Parse spec               │
│    - Extract user stories    │
│    - Extract data models     │
│    - Extract behaviors       │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ 2. Decompose into components│
│    - Identify types needed   │
│    - Assign responsibilities │
│    - Define interfaces       │
│    - Map dependencies        │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│ 3. Define wiring             │
│    - Who injects what        │
│    - Data flow direction     │
│    - Entry points            │
└──────────┬──────────────────┘
           │
           ▼
Output: arch.json → written to output-path
```

## Requirements

### REQ-1: Component Decomposition

- REQ-1.1: Each component has: `name`, `category` (from `solid-category` vocabulary — see `/create-type` SKILL.md Phase 3.2), `responsibility` (one sentence), `interfaces` (protocols it exposes), `dependencies` (protocols it consumes), `produces` (data types it outputs).
- REQ-1.2: Follow `/create-type` naming conventions (SKILL.md Phase 1): actor protocols use `-ing` suffix, subject protocols use `-able` suffix, general contracts use `-Providing` suffix.
- REQ-1.3: Every dependency between components must be through a protocol — no concrete type references in the wiring.
- REQ-1.4: Leaf SwiftUI views (pure data → view, no ViewModel) are listed as components but flagged as `"leaf": true` — no protocol injection required for them.

### REQ-2: Wiring

- REQ-2.1: Each wiring entry specifies: `from` (consumer), `to` (protocol), `via` (injection method: `init`, `environment`, `closure`).
- REQ-2.2: The architect must identify the composition root — where concrete types are assembled and injected.

### REQ-3: Output

- REQ-3.1: The skill writes `arch.json` to the path specified by the `output-path` argument.
- REQ-3.2: `arch.json` structure:
  ```json
  {
    "spec_summary": "one-line summary of what's being built",
    "components": [
      {
        "name": "ProductFetchService",
        "category": "network",
        "responsibility": "Fetches product data from REST API with pagination",
        "interfaces": ["ProductReading"],
        "dependencies": ["URLSessionProviding", "JSONDecoding"],
        "produces": ["Product", "ProductPage"],
        "leaf": false
      }
    ],
    "wiring": [
      {
        "from": "ProductListViewModel",
        "to": "ProductReading",
        "via": "init"
      }
    ],
    "composition_root": "ProductListFactory or AppAssembly",
    "data_models": [
      {
        "name": "Product",
        "category": "model",
        "fields": ["id: String", "name: String", "price: Decimal"]
      }
    ]
  }
  ```

### Edge Cases

- EC-1: Spec mentions UI but no data layer — architect still proposes ViewModel + protocol boundary, even if the data source is TBD.
- EC-2: Spec is a single sentence — architect produces minimal decomposition (may be just one component + one protocol).
- EC-3: Spec references external SDKs — architect lists them as dependencies but does not design their internals.

## Definition of Done

- [ ] Sub-skill exists with `user-invocable: false`
- [ ] Accepts spec as input (prompt string or markdown filepath)
- [ ] Accepts `output-path` argument for where to write `arch.json`
- [ ] Produces `arch.json` matching the output schema
- [ ] All component names follow `/create-type` naming conventions (SKILL.md Phase 1)
- [ ] All `category` values use `/create-type` solid-category vocabulary (SKILL.md Phase 3.2)
- [ ] All inter-component dependencies are protocol-typed
- [ ] Leaf views are flagged as `leaf: true`
- [ ] Composition root is identified
- [ ] Testable standalone: `/plan "build a todo list app" --output ./arch.json`
