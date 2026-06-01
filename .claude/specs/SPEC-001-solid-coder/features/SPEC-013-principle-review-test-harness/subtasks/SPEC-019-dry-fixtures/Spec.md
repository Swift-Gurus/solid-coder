---
number: SPEC-019
feature: dry-fixtures
type: subtask
status: draft
parent: SPEC-013
blocked-by: [SPEC-014]
blocking: []
---

# DRY — Fixtures and Expectations

## Description

Create DRY fixture files, expectation manifests, and manifest.yaml under `tests/principles/DRY/`. Targets the DRY-2 inlined-duplication metric (SEVERE) and a shared-abstraction compliant example.

## Input / Output

|   | Detail |
|---|--------|
| Input | `references/principles/DRY/rule.md` — reuse_misses, inlined_duplications, missing_abstractions metrics |
| Output | `tests/principles/DRY/fixtures/fixture-N.swift`, `tests/principles/DRY/expectations/*.json`, `tests/principles/DRY/manifest.yaml` |

## User Stories

### Story 1 — DRY fixtures cover inlined duplication and shared abstraction

As the system, when `run_principle_tests.py --principle references/principles/DRY` runs, each fixture produces findings matching its expectation.

**Acceptance Criteria:**
- AC1: `fixture-1.swift` — two functions with identical 6+ line logic blocks differing only in label/tag; expectation: DRY-2 SEVERE
- AC2: `fixture-2.swift` — same logic extracted to a shared private helper; expectation: empty findings
- AC3: No violation hints in names or filenames
- AC4: `run_principle_tests.py --principle references/principles/DRY` exits 0

## Technical Requirements

- DRY severity bands are text-based — LLM scores
- The duplication in fixture-1 must be structural (same algorithm, not just similar variable names)
- Expectation `metrics` may include `inlined_duplications: 1` if LLM reliably reports it

## Connects To

| Relationship | Target | Notes |
|---|---|---|
| Depends on | SPEC-014 | |
| Validates | `references/principles/DRY/rule.md` | |

## Diagrams

```mermaid
graph LR
    F1[fixture-1.swift] -->|DRY-2 SEVERE| E1[dry-2-severe.json]
    F2[fixture-2.swift] -->|COMPLIANT| E2[compliant.json]
```

## Test Plan

### Integration Tests (requires INTEGRATION=1)
- When fixture-1.swift is reviewed for DRY, output contains DRY-2 SEVERE
- When fixture-2.swift is reviewed for DRY, output contains no findings

## Definition of Done

- [ ] `tests/principles/DRY/fixtures/fixture-1.swift`
- [ ] `tests/principles/DRY/fixtures/fixture-2.swift`
- [ ] `tests/principles/DRY/expectations/dry-2-severe.json`
- [ ] `tests/principles/DRY/expectations/compliant.json`
- [ ] `tests/principles/DRY/manifest.yaml`
- [ ] `run_principle_tests.py --principle references/principles/DRY` exits 0
