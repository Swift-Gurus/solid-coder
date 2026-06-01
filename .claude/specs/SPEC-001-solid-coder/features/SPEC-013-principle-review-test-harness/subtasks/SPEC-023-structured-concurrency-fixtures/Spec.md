---
number: SPEC-023
feature: structured-concurrency-fixtures
type: subtask
status: draft
parent: SPEC-013
blocked-by: [SPEC-014]
blocking: []
---

# StructuredConcurrency — Fixtures and Expectations

## Description

Create StructuredConcurrency fixture files, expectation manifests, and manifest.yaml under `tests/coding/apple/StructuredConcurrency/` — mirroring `references/coding/apple/StructuredConcurrency/`. Targets violations of Swift structured concurrency best practices (e.g. GCD usage, unstructured Task spawning) and compliant async/await examples.

## Input / Output

|   | Detail |
|---|--------|
| Input | `references/coding/apple/StructuredConcurrency/rule.md` — SC metrics and severity bands |
| Output | `tests/coding/apple/StructuredConcurrency/fixtures/fixture-N.swift`, expectations, manifest.yaml |

## User Stories

### Story 1 — StructuredConcurrency fixtures cover key violations

As the system, when `run_principle_tests.py --principle references/coding/apple/StructuredConcurrency` runs, each fixture produces findings matching its expectation.

**Acceptance Criteria:**
- AC1: At least one SEVERE fixture targeting a documented SC metric
- AC2: At least one COMPLIANT fixture using Swift structured concurrency correctly
- AC3: No violation hints in fixture filenames or type names
- AC4: `run_principle_tests.py --principle references/coding/apple/StructuredConcurrency` exits 0

## Technical Requirements

- Read `references/coding/apple/StructuredConcurrency/rule.md` before writing fixtures to identify current metrics
- Fixtures should use Swift async/await or DispatchQueue patterns as appropriate to trigger detection

## Connects To

| Relationship | Target | Notes |
|---|---|---|
| Depends on | SPEC-014 | |
| Validates | `references/coding/apple/StructuredConcurrency/rule.md` | |

## Test Plan

### Integration Tests (requires INTEGRATION=1)
- When fixture-1.swift is reviewed for StructuredConcurrency, output contains a SEVERE finding
- When fixture-2.swift is reviewed, output contains no findings

## Definition of Done

- [ ] `tests/coding/apple/StructuredConcurrency/fixtures/fixture-1.swift`
- [ ] `tests/coding/apple/StructuredConcurrency/fixtures/fixture-2.swift`
- [ ] `tests/coding/apple/StructuredConcurrency/expectations/sc-severe.json`
- [ ] `tests/coding/apple/StructuredConcurrency/expectations/compliant.json`
- [ ] `tests/coding/apple/StructuredConcurrency/manifest.yaml`
- [ ] `run_principle_tests.py --principle references/coding/apple/StructuredConcurrency` exits 0
