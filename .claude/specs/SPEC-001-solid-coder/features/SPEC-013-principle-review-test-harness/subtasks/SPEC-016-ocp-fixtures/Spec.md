---
number: SPEC-016
feature: ocp-fixtures
type: subtask
status: draft
parent: SPEC-013
blocked-by: [SPEC-014]
blocking: []
---

# OCP — Fixtures and Expectations

## Description

Create the OCP fixture files, expectation manifests, and manifest.yaml under `tests/principles/OCP/`. Covers the OCP-1 sealed variation point metric (SEVERE) and a protocol-injected compliant example.

## Input / Output

|   | Detail |
|---|--------|
| Input | `references/principles/OCP/rule.md` — OCP-1 sealed_variation_points, OCP-2 testability metrics |
| Output | `tests/principles/OCP/fixtures/fixture-N.swift`, `tests/principles/OCP/expectations/*.json`, `tests/principles/OCP/manifest.yaml` |

## User Stories

### Story 1 — OCP fixtures cover sealed-point violation and compliant injection

As the system, when `run_principle_tests.py --principle references/principles/OCP` runs, each fixture produces findings matching its expectation for both flows.

**Acceptance Criteria:**
- AC1: `fixture-1.swift` — class with at least one internally constructed, non-helper, non-factory concrete dependency; expectation: OCP-1 SEVERE
- AC2: `fixture-2.swift` — same class refactored with protocol-typed injected dependencies; expectation: empty findings
- AC3: No violation hints in fixture filenames or type names
- AC4: `run_principle_tests.py --principle references/principles/OCP` exits 0

## Technical Requirements

- OCP severity bands are text-based (no XML conditions) — the LLM applies scoring; expectation must match what the LLM reports
- Expectation `metrics` field is optional for OCP; include if the LLM reliably reports a count
- Helper exceptions (DateFormatter, JSONEncoder, etc.) must NOT be the sealed point — use a business-logic dependency

## Connects To

| Relationship | Target | Notes |
|---|---|---|
| Depends on | SPEC-014 — harness infrastructure | |
| Validates | `references/principles/OCP/rule.md` | |

## Diagrams

```mermaid
graph LR
    F1[fixture-1.swift] -->|OCP-1 SEVERE| E1[ocp-1-severe.json]
    F2[fixture-2.swift] -->|COMPLIANT| E2[compliant.json]
```

## Test Plan

### Integration Tests (requires INTEGRATION=1)
- When fixture-1.swift is reviewed for OCP, output contains OCP-1 SEVERE
- When fixture-2.swift is reviewed for OCP, output contains no findings

## Definition of Done

- [ ] `tests/principles/OCP/fixtures/fixture-1.swift` — sealed-point violation, no hints
- [ ] `tests/principles/OCP/fixtures/fixture-2.swift` — protocol-injected, no hints
- [ ] `tests/principles/OCP/expectations/ocp-1-severe.json`
- [ ] `tests/principles/OCP/expectations/compliant.json`
- [ ] `tests/principles/OCP/manifest.yaml`
- [ ] `run_principle_tests.py --principle references/principles/OCP` exits 0
