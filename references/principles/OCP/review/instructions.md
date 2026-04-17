---
name: ocp-review
type: review
rules: PRINCIPLE_FOLDER_ABSOLUTE_PATH/rule.md
output_schema: output.schema.json
---

#### Phase 1: Detection (OCP-1 and OCP-2 run independently and in parallel if possible)

- [ ] **1.1 OCP-1: Count Sealed Variation Points**
    - [ ] 1.1.1 List every dependency the class uses (properties, parameters, method calls)

      | Dependency | Type | Classification | Reason |
      |------------|------|----------------|--------|
      |            |      |                |        |
    - [ ] 1.1.2 Check exceptions (factories, helpers, pure data structures — 0 points)
    - [ ] 1.1.3 Classify DIRECT types for INJECTED, NON-INJECTED

      | DIRECT | INJECTED/NON-INJECTED |
      |--------|-----------------------|
      |        |                       |
    - [ ] 1.1.4 List INDIRECT types
        
    - [ ] 1.1.5 Sum sealed variation points (DIRECT non-injected - exceptions)

      Sealed variation point count: ___

- [ ] **1.2 OCP-2: Testability Score**
    - [ ] 1.2.1 Perform analysis of DIRECT AND INDIRECT Dependencies
    - [ ] 1.2.2 For every DIRECT INJECTED
      -  [ ] 1.2.2.1 List every dependency the class uses (properties, parameters, method calls)

      | Dependency | Type | Classification | Reason |
      |------------|------|----------------|--------|
      |            |      |                |        |
      - [ ] 1.2.2.2 Check exceptions (factories, helpers, pure data structures — 0 points)
      - [ ] 1.2.2.3 List DIRECT types for INJECTED, NON-INJECTED

        | CONCRETE | INJECTED/NON-INJECTED |
        |----------|-----------------------|
        |          |                       |
      - [ ] 1.2.2.4 Sum sealed variation points (DIRECT non-injected - exceptions)
    - [ ] 1.2.3 Count all DIRECT INJECTED UNTESTABLE DEPENDENCIES
    - [ ] 1.2.4 For every INDIRECT dependency
      - [ ] 1.2.4.1 - validate if it can be subclassed, if not -> mark untestable
  - [ ] 1.2.5 Count all INDIRECT UNTESTABLE DEPENDENCIES


#### Phase 2: Scoring

- [ ] **2.1 Determine severity**
    - [ ] 2.1.1 Sealed variation points: ___, severity: ___
    - [ ] 2.1.2 Untestable DIRECT INJECTED dependencies: ___, severity: ___
    - [ ] 2.1.3 Testable DIRECT INJECTED count: ___
    - [ ] 2.1.4 Untestable INDIRECT dependencies: ___, severity: ___
    - [ ] 2.1.5 Testable INDIRECT count: ___  
    - [ ] 2.1.6 Final severity: ___ 

#### Phase 3: Output

- [ ] **3.1 Report Violations**
    - [ ] 3.1.1 Show dependency table and sealed variation point analysis
    - [ ] 3.1.2 Show dependency testability compliance for DIRECT and INDIRECT dependencies

