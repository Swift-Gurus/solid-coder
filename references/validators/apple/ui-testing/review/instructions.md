---
name: uitesting-review
type: review
rules: PRINCIPLE_FOLDER_ABSOLUTE_PATH/rule.md
output_schema: output.schema.json
---

### Phase 0: Load Examples for context.
- [ ] **0.1 Read all examples** — Glob `PRINCIPLE_FOLDER_ABSOLUTE_PATH/Examples/*` and read every file found

#### Phase 1: Detection (UITEST-1 through UITEST-5 run independently and in parallel if possible)

- [ ] **1.1 UITEST-1: Detect Flow Encapsulation Violations**
    - [ ] 1.1.1 For each test method, identify whether it contains inline multi-step UI interaction sequences

      | Test Method | Inline Steps | Delegates to Coordinator? | Violation? |
      |-------------|-------------|--------------------------|------------|
      |             |             |                          |            |

    - [ ] 1.1.2 Across all test methods, identify duplicated navigation sequences

      | Flow Summary | Appears In (methods) | Coordinator Exists? | Violation? |
      |--------------|---------------------|---------------------|------------|
      |              |                     |                     |            |

    - [ ] 1.1.3 For each coordinator type, check if it re-implements steps already covered by a prior-screen coordinator

      | Coordinator | Duplicates Steps From | Should Compose? | Violation? |
      |-------------|-----------------------|-----------------|------------|
      |             |                       |                 |            |

    - [ ] 1.1.4 Count flow encapsulation violations
      Flow encapsulation violations: ___

- [ ] **1.2 UITEST-2: Detect Base Class Structure Violations**
    - [ ] 1.2.1 Identify the base class hierarchy

      Base class detected: ___
      Inherits from XCTestCase directly: ___

    - [ ] 1.2.2 Check for lifecycle logic in individual suites

      | Test Class | Overrides setUp? | Overrides tearDown? | Manages App Directly? | Violation? |
      |------------|-----------------|--------------------|-----------------------|------------|
      |            |                 |                    |                       |            |

    - [ ] 1.2.3 Check for conditional setup configured in test methods instead of via base class methods

      | Test Method | Config Applied | Should Be Base Class Method? | Violation? |
      |-------------|---------------|------------------------------|------------|
      |             |               |                              |            |

    - [ ] 1.2.4 Count base class structure violations
      Base class violations: ___

- [ ] **1.3 UITEST-3: Detect Assertion Grouping Violations**
    - [ ] 1.3.1 Group test methods by their setup preamble (coordinator call or navigation path)

      | Setup Preamble | Test Methods That Share It | Assertions Per Method |
      |----------------|---------------------------|-----------------------|
      |                |                           |                       |

    - [ ] 1.3.2 For each group, assess whether the assertions are independent and could be merged

      | Group | Tests In Group | Independent Assertions? | Could Be One Test? | Violation? |
      |-------|---------------|------------------------|---------------------|------------|
      |       |               |                        |                     |            |

    - [ ] 1.3.3 Count fragmented assertion groups
      Assertion grouping violations: ___

- [ ] **1.4 UITEST-4: Detect Synchronization Violations**
    - [ ] 1.4.1 Scan all test methods for time-based waits

      | Test Method | Wait Call | Type (sleep/asyncAfter/etc) | Violation? |
      |-------------|----------|-----------------------------|------------|
      |             |          |                             |            |

    - [ ] 1.4.2 For every element interaction (tap, click, type) and assertion on an element property, trace the full call chain to determine if a condition-based existence check occurs before the access:
        - If the access goes through a helper method, read that method's implementation
        - If that helper calls further methods, keep tracing until you reach the assertion point
        - Only mark compliant if condition-based waiting is found somewhere in the chain

      | Test Method | Element Access | Traced Through | Condition-Based Wait Found? | Violation? |
      |-------------|---------------|---------------|----------------------------|------------|
      |             |               |               |                            |            |

    - [ ] 1.4.3 Count synchronization violations
      Synchronization violations: ___

- [ ] **1.5 UITEST-5: Detect Typed Identifier Violations**
    - [ ] 1.5.1 Scan all test methods for raw string literals in element queries

      | Test Method | Query | Raw String | App or System Element? | Violation? |
      |-------------|-------|-----------|------------------------|------------|
      |             |       |           |                        |            |

    - [ ] 1.5.2 Note whether a typed identifier system exists at all

      Typed identifier system detected: ___
      If none detected: note in findings — fix instructions cover how to create one

    - [ ] 1.5.3 Count typed identifier violations
      Identifier violations: ___

#### Phase 2: Filter Out Exceptions

- [ ] **2.1 Cross-check exceptions** — mark exceptions

  | Test/Class | Exception Reason |
  |------------|-----------------|
  |            |                 |

- [ ] **2.2 Exclude exceptions** — per-test launch argument tests, performance measure blocks, terminate-and-relaunch boundary tests, single-method classes (UITEST-3 exempt)

#### Phase 3: Scoring

- [ ] **3.1 Determine severity**
    - [ ] 3.1.1 Flow encapsulation violations: ___, severity: ___
    - [ ] 3.1.2 Base class structure violations: ___, severity: ___
    - [ ] 3.1.3 Assertion grouping violations: ___, severity: ___
    - [ ] 3.1.4 Synchronization violations: ___, severity: ___
    - [ ] 3.1.5 Typed identifier violations: ___, severity: ___
    - [ ] 3.1.6 Adjust severity considering exceptions
    - [ ] 3.1.7 Final severity: ___

#### Phase 4: Output

- [ ] **4.1 Report Violations**
    - [ ] 4.1.1 Show flow encapsulation analysis with inline flow and duplication tables
    - [ ] 4.1.2 Show base class structure analysis with lifecycle and conditional setup tables
    - [ ] 4.1.3 Show assertion grouping analysis with preamble groups table
    - [ ] 4.1.4 Show synchronization analysis with time-based wait and call chain tables
    - [ ] 4.1.5 Show typed identifier analysis with raw string query table and identifier system status
    - [ ] 4.1.6 Show exceptions table
