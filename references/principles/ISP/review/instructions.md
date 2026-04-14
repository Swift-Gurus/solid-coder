---
name: isp-review
type: review
rules: PRINCIPLE_FOLDER_ABSOLUTE_PATH/rule.md
output_schema: output.schema.json
---

### Phase 0: Load Examples for context.
- [ ] **0.1 Read all examples** — Glob `PRINCIPLE_FOLDER_ABSOLUTE_PATH/Examples/*` and read every file found

#### Phase 1: Detection (ISP-1, ISP-2, ISP-3 run per protocol)

- [ ] **1.0 Scope check** — ISP applies ONLY to protocol/interface declarations (see rule.md Exception 1). For each unit:
  - `protocol` → proceed to 1.1
  - `class`, `struct`, `enum`, `extension` (no protocol declaration) → mark COMPLIANT, skip all ISP metrics

- [ ] **1.1 ISP-1: Measure Protocol Width**
    - [ ] 1.1.1 List every method, property, and associated type declared in the protocol

      | Requirement | Kind (method/property/associatedtype) |
      |-------------|---------------------------------------|
      |             |                                       |
    - [ ] 1.1.2 Exclude inherited requirements (from parent protocols)
    - [ ] 1.1.3 Count total requirements

      Protocol width: ___

- [ ] **1.2 ISP-2: Measure Conformer Coverage**
    - [ ] 1.2.1 Find all conformers of this protocol in the project
    - [ ] 1.2.2 For each conformer, classify each required method/property:

      | Conformer | Method | Classification (MEANINGFUL/EMPTY/STUB/DELEGATED) |
      |-----------|--------|--------------------------------------------------|
      |           |        |                                                  |
    - [ ] 1.2.3 Calculate coverage per conformer = meaningful / total

      | Conformer | Meaningful | Empty | Stub | Total | Coverage % |
      |-----------|------------|-------|------|-------|------------|
      |           |            |       |      |       |            |
    - [ ] 1.2.4 Find minimum coverage across all conformers

      Minimum conformer coverage: ___

- [ ] **1.3 ISP-3: Protocol Cohesion Groups**
    - [ ] 1.3.1 Build usage matrix: which methods are MEANINGFUL per conformer

      | Method | Conformer A | Conformer B | Conformer C |
      |--------|-------------|-------------|-------------|
      |        |             |             |             |
    - [ ] 1.3.2 Identify disjoint usage groups (methods that cluster together)

      | Group | Methods | Conformers That Use All |
      |-------|---------|------------------------|
      |       |         |                        |
    - [ ] 1.3.3 Count groups

      Protocol cohesion groups: ___

#### Phase 2: Filter Out Exceptions

- [ ] **2.1 Cross-check exceptions** — mark exceptions

  | Protocol | Exception Reason |
  |----------|-----------------|
  |          |                 |
- [ ] **2.2 Exclude exceptions** — exclude from analysis
- [ ] **2.3 Check default implementations** — if non-meaningful methods have protocol extension defaults, conformers are not forced to implement them. Reduce empty/stub counts accordingly.
- [ ] **2.4 Flag typealias compositions** — if the project uses `typealias P = A & B` instead of `protocol P: A, B {}`, flag as a code smell. Typealiases cannot be conformed to (`class Decorator: P` won't compile), which breaks decorator and wrapper patterns.

#### Phase 3: Scoring

- [ ] **3.1 Determine severity**
    - [ ] 3.1.1 Protocol width: ___, severity: ___
    - [ ] 3.1.2 Minimum conformer coverage: ___%, severity: ___
    - [ ] 3.1.3 Protocol cohesion groups: ___, severity: ___
    - [ ] 3.1.4 Empty/stub methods in worst conformer: ___
    - [ ] 3.1.5 Adjust severity considering exceptions
    - [ ] 3.1.6 Final severity: ___

#### Phase 4: Output

- [ ] **4.1 Report Violations**
    - [ ] 4.1.1 Show protocol requirements table and width count
    - [ ] 4.1.2 Show conformer coverage matrix
    - [ ] 4.1.3 Show cohesion groups (if 2+)
    - [ ] 4.1.4 Show exceptions found
