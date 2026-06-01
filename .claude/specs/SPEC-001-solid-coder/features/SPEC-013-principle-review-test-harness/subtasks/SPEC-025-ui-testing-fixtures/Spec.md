---
number: SPEC-025
feature: ui-testing-fixtures
type: subtask
status: draft
parent: SPEC-013
blocked-by: [SPEC-014]
blocking: []
---

# UI Testing — Fixtures and Expectations

## Description

Create UI-testing fixture files, expectation manifests, and manifest.yaml under `tests/validators/apple/ui-testing/` — mirroring `references/validators/apple/ui-testing/`. Targets violations of UI testing best practices and compliant examples.

## Input / Output

|   | Detail |
|---|--------|
| Input | `references/validators/apple/ui-testing/rule.md` — UI testing metrics and severity bands |
| Output | `tests/validators/apple/ui-testing/fixtures/fixture-N.swift`, expectations, manifest.yaml |

## User Stories

### Story 1 — UI testing fixtures cover key violations

As the system, when `run_principle_tests.py --principle references/validators/apple/ui-testing` runs, each fixture produces findings matching its expectation.

**Acceptance Criteria:**
- AC1: At least one SEVERE fixture targeting a documented UI testing metric
- AC2: At least one COMPLIANT fixture — well-structured UI test file
- AC3: No violation hints in fixture filenames or type names
- AC4: `run_principle_tests.py --principle references/validators/apple/ui-testing` exits 0

## Technical Requirements

- Read `references/validators/apple/ui-testing/rule.md` before writing fixtures to identify current metrics
- Fixtures must use XCUIApplication or XCUIElement patterns to trigger context detection

## Connects To

| Relationship | Target | Notes |
|---|---|---|
| Depends on | SPEC-014 | |
| Validates | `references/validators/apple/ui-testing/rule.md` | |

## Test Plan

### Integration Tests (requires INTEGRATION=1)
- When fixture-1.swift is reviewed for UI testing, output contains a SEVERE finding
- When fixture-2.swift is reviewed, output contains no findings

## Definition of Done

- [ ] `tests/validators/apple/ui-testing/fixtures/fixture-1.swift`
- [ ] `tests/validators/apple/ui-testing/fixtures/fixture-2.swift`
- [ ] `tests/validators/apple/ui-testing/expectations/violation-severe.json`
- [ ] `tests/validators/apple/ui-testing/expectations/compliant.json`
- [ ] `tests/validators/apple/ui-testing/manifest.yaml`
- [ ] `run_principle_tests.py --principle references/validators/apple/ui-testing` exits 0
