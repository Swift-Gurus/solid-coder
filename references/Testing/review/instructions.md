---
name: testing-review
type: review
rules: PRINCIPLE_FOLDER_ABSOLUTE_PATH/rule.md
output_schema: output.schema.json
---

### Phase 0: Load Examples for context.
- [ ] **0.1 Read all examples** — Glob `PRINCIPLE_FOLDER_ABSOLUTE_PATH/Examples/*` and read every file found

#### Phase 1: Detection (TEST-1 through TEST-5 run independently and in parallel if possible)

- [ ] **1.1 TEST-1: Detect Isolation Violations**
    - [ ] 1.1.1 Scan for shared mutable state — class-level vars not reset in setUp/init, static vars mutated across tests

      | Property | Scope | Reset in setUp? | Violation? |
      |----------|-------|-----------------|------------|
      |          |       |                 |            |

    - [ ] 1.1.2 Scan for singleton/global access without injection

      | Access Pattern | Location | Injected? | Violation? |
      |----------------|----------|-----------|------------|
      |                |          |           |            |

    - [ ] 1.1.3 Scan for test interdependencies — tests referencing other tests' state, order-dependent assertions

      | Test Method | Depends On | Reason |
      |-------------|-----------|--------|
      |             |           |        |

    - [ ] 1.1.4 Count isolation violations
      Isolation violations: ___

- [ ] **1.2 TEST-2: Detect Structure Violations**
    - [ ] 1.2.1 Scan for logic in tests — if/else, switch, for/while loops, try? swallowing, conditional assertions

      | Test Method | Logic Type | Code | Violation? |
      |-------------|-----------|------|------------|
      |             |           |      |            |

    - [ ] 1.2.2 Check for clear Arrange-Act-Assert phases — interleaved assertions, missing assertions, phase comments instead of blank lines

      | Test Method | Has Arrange? | Has Act? | Has Assert? | Interleaved? | Violation? |
      |-------------|-------------|----------|-------------|-------------- |------------|
      |             |             |          |             |              |            |

    - [ ] 1.2.3 Detect multiple behaviors — 4+ unrelated assertions, multiple independent code paths

      | Test Method | Assertion Count | Behaviors Tested | Violation? |
      |-------------|----------------|-----------------|------------|
      |             |                |                 |            |

    - [ ] 1.2.4 Detect sleep-based waiting — Thread.sleep, Task.sleep, sleep(), usleep(), hardcoded delays

      | Test Method | Sleep Call | Location | Violation? |
      |-------------|-----------|----------|------------|
      |             |           |          |            |

    - [ ] 1.2.5 Count structure violations
      Structure violations: ___

- [ ] **1.3 TEST-3: Detect Naming Violations**
    - [ ] 1.3.1 List all test method names and assess descriptiveness

      | Test Method | Describes Scenario? | Describes Expectation? | Violation Type |
      |-------------|--------------------|-----------------------|---------------|
      |             |                    |                       |               |

    - [ ] 1.3.2 Check naming convention consistency across the test class

      Convention detected: ___
      Inconsistencies: ___

    - [ ] 1.3.3 Count naming violations
      Naming violations: ___

- [ ] **1.4 TEST-4: Detect Test Double Quality Violations**
    - [ ] 1.4.1 Inventory test doubles — list all mocks, stubs, fakes used

      | Test Double | Type (mock/stub/fake/spy) | What It Replaces | Necessary? |
      |-------------|--------------------------|-----------------|------------|
      |             |                          |                 |            |

    - [ ] 1.4.2 Detect over-mocking — mocked value types, partial mocks (SUT subclass), mocked pure logic types

      | Test Method | Mock | Issue | Violation? |
      |-------------|------|-------|------------|
      |             |      |       |            |

    - [ ] 1.4.3 Detect brittle verification — verifying internal method calls instead of observable outcomes

      | Test Method | Verification | Issue | Violation? |
      |-------------|-------------|-------|------------|
      |             |             |       |            |

    - [ ] 1.4.4 Detect testing mock logic — circular mock assertions (set then assert same mock), facades with mocked direct deps instead of mocked boundaries

      | Test Method | Issue | Detail | Violation? |
      |-------------|-------|--------|------------|
      |             |       |        |            |

    - [ ] 1.4.5 Count test double violations
      Test double violations: ___

- [ ] **1.5 TEST-5: Detect Setup Complexity Violations**
    - [ ] 1.5.1 Identify how SUT is constructed — inline in each test or centralized

      | Test Method | SUT Type | Construction Location | Dependency Count |
      |-------------|----------|----------------------|-----------------|
      |             |          |                      |                 |

    - [ ] 1.5.2 Count test methods with inline SUT construction (same pattern repeated)
      Inline constructions: ___

    - [ ] 1.5.3 Record max dependency count (informs fix strategy)
      Dependency count: ___

    - [ ] 1.5.4 Count setup complexity violations
      Setup violations: ___

#### Phase 2: Filter Out Exceptions

- [ ] **2.1 Cross-check exceptions** — mark exceptions

  | Test/Class | Exception Reason |
  |------------|-----------------|
  |            |                 |

- [ ] **2.2 Exclude exceptions** — exclude integration tests, snapshot tests, performance tests, parameterized loops, shared immutable fixtures

#### Phase 3: Scoring

- [ ] **3.1 Determine severity**
    - [ ] 3.1.1 Isolation violations: ___, severity: ___
    - [ ] 3.1.2 Structure violations: ___, severity: ___
    - [ ] 3.1.3 Naming violations: ___, severity: ___
    - [ ] 3.1.4 Test double violations: ___, severity: ___
    - [ ] 3.1.5 Setup complexity violations: ___, severity: ___
    - [ ] 3.1.6 Adjust severity considering exceptions.
    - [ ] 3.1.7 Final severity: ___

#### Phase 4: Output

- [ ] **4.1 Report Violations**
    - [ ] 4.1.1 Show isolation analysis with shared state and external call tables
    - [ ] 4.1.2 Show structure analysis with logic, phase, and sleep-waiting tables
    - [ ] 4.1.3 Show naming analysis with descriptiveness assessment
    - [ ] 4.1.4 Show test double analysis with mock inventory, over-mocking, brittle verification, and mock logic tables
    - [ ] 4.1.5 Show setup complexity analysis with inline construction and dependency count
    - [ ] 4.1.6 Show cross-reference table with found exceptions
