---
number: SPEC-018
feature: lsp-fixtures
type: subtask
status: draft
parent: SPEC-013
blocked-by: [SPEC-014]
blocking: []
---

# LSP — Fixtures and Expectations

## Description

Create LSP fixture files, expectation manifests, and manifest.yaml under `tests/principles/LSP/`. Targets the LSP-1 type-check dispatch violation (SEVERE) and a polymorphic compliant example.

## Input / Output

|   | Detail |
|---|--------|
| Input | `references/principles/LSP/rule.md` — type_checking, contract_compliance, empty_methods metrics |
| Output | `tests/principles/LSP/fixtures/fixture-N.swift`, `tests/principles/LSP/expectations/*.json`, `tests/principles/LSP/manifest.yaml` |

## User Stories

### Story 1 — LSP fixtures cover type-check dispatch and polymorphic compliant

As the system, when `run_principle_tests.py --principle references/principles/LSP` runs, each fixture produces findings matching its expectation.

**Acceptance Criteria:**
- AC1: `fixture-1.swift` — function using `as?` casts to dispatch differently per subtype; expectation: LSP-1 SEVERE
- AC2: `fixture-2.swift` — same dispatch via protocol method, no casts; expectation: empty findings
- AC3: No violation hints in names or filenames
- AC4: `run_principle_tests.py --principle references/principles/LSP` exits 0

## Technical Requirements

- LSP severity bands are text-based — LLM scores
- Framework-forced casts (e.g. `response as? HTTPURLResponse`) are exceptions per rule.md — do NOT use these in fixture-1; use user-defined class hierarchy

## Connects To

| Relationship | Target | Notes |
|---|---|---|
| Depends on | SPEC-014 | |
| Validates | `references/principles/LSP/rule.md` | |

## Diagrams

```mermaid
graph LR
    F1[fixture-1.swift] -->|LSP-1 SEVERE| E1[lsp-1-severe.json]
    F2[fixture-2.swift] -->|COMPLIANT| E2[compliant.json]
```

## Test Plan

### Integration Tests (requires INTEGRATION=1)
- When fixture-1.swift is reviewed for LSP, output contains LSP-1 SEVERE
- When fixture-2.swift is reviewed for LSP, output contains no findings

## Definition of Done

- [ ] `tests/principles/LSP/fixtures/fixture-1.swift`
- [ ] `tests/principles/LSP/fixtures/fixture-2.swift`
- [ ] `tests/principles/LSP/expectations/lsp-1-severe.json`
- [ ] `tests/principles/LSP/expectations/compliant.json`
- [ ] `tests/principles/LSP/manifest.yaml`
- [ ] `run_principle_tests.py --principle references/principles/LSP` exits 0
