---
number: SPEC-024
feature: unit-testing-fixtures
type: subtask
status: draft
parent: SPEC-013
blocked-by: [SPEC-014]
blocking: []
---

# Unit Testing — Fixtures and Expectations

## Description

Create unit-testing fixture files, expectation manifests, and manifest.yaml under `tests/testing/unit/swift/` — mirroring `references/testing/unit/swift/`. Targets violations of unit testing best practices and compliant test examples.

## Input / Output

|   | Detail |
|---|--------|
| Input | `references/testing/unit/swift/rule.md` — unit testing metrics and severity bands |
| Output | `tests/testing/unit/swift/fixtures/fixture-N.swift`, expectations, manifest.yaml |

## User Stories

### Story 1 — Unit testing fixtures cover key violations

As the system, when `run_principle_tests.py --principle references/testing/unit/swift` runs, each fixture produces findings matching its expectation.

**Acceptance Criteria:**
- AC1: At least one SEVERE fixture targeting a documented unit testing metric
- AC2: At least one COMPLIANT fixture — well-structured test file
- AC3: No violation hints in fixture filenames or type names
- AC4: `run_principle_tests.py --principle references/testing/unit/swift` exits 0

## Technical Requirements

- Read `references/testing/unit/swift/rule.md` before writing fixtures to identify current metrics
- Fixtures must import XCTest or Swift Testing framework to trigger context detection

## Connects To

| Relationship | Target | Notes |
|---|---|---|
| Depends on | SPEC-014 | |
| Validates | `references/testing/unit/swift/rule.md` | |

## Test Plan

### Integration Tests (requires INTEGRATION=1)
- When fixture-1.swift is reviewed for unit testing, output contains a SEVERE finding
- When fixture-2.swift is reviewed, output contains no findings

## Definition of Done

- [ ] `tests/testing/unit/swift/fixtures/fixture-1.swift`
- [ ] `tests/testing/unit/swift/fixtures/fixture-2.swift`
- [ ] `tests/testing/unit/swift/expectations/violation-severe.json`
- [ ] `tests/testing/unit/swift/expectations/compliant.json`
- [ ] `tests/testing/unit/swift/manifest.yaml`
- [ ] `run_principle_tests.py --principle references/testing/unit/swift` exits 0
