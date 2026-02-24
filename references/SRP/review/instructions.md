---
name: srp-review
type: review
rules: PRINCIPLE_FOLDER_ABSOLUTE_PATH/rule.md
output_schema: output.schema.json
---

### Phase 0: Load Examples for context.
- [ ] **0.1 Read all references/examples**
  - [] [FOR EVERY FILE IN PRINCIPLE_FOLDER_ABSOLUTE_PATH/Examples CREATE TODO]

#### Phase 1: Detection (SRP-1 and SRP-2 run independently and in parallel if possible)

- [ ] **1.1 SRP-1: Count Verbs**
    - [ ] 1.1.1 For each method, extract the verb (what it does)

      | Method | Verb |
      |--------|------|
      |        |      |
    - [ ] 1.1.2 Count distinct verbs (no merging, no deduplication)

      Verb count: ___

- [ ] **1.2 SRP-2: Count Cohesion Groups**
    - [ ] 1.2.1 List which methods use which instance variables

      | Method | Variables Used |
      |--------|---------------|
      |        |               |
    - [ ] 1.2.2 Identify disjoint variable sets 
      - exclude shared-by-all variables
      - consider special case bridge-method
      Groups: ___
    - [ ] 1.2.3 Count groups
      Cohesion group count: ___
  
- [ ] **1.3 SRP-3: Count Stakeholders Groups**
    - [ ] 1.3.1 List which verbs attributed to a stakeholder

      | Verb | Stakeholder |
      |------|-------------|
      |      |             |
    - [ ] 1.3.2 Count stakeholders
      stakeholders count: ___

#### Phase 2: Cross-Reference

- [ ] **2.1 Map verbs onto cohesion groups**

  | Cohesion Group | Variables | Verbs | Stakeholder Label |
  |----------------|-----------|-------|-------------------|
  |                |           |       |                   |

#### Phase 3: Scoring

- [ ] **3.1 Determine severity**
    - [ ] 3.1.1 Cohesion groups: ___, severity: __
    - [ ] 3.1.2 Verb count: ___ , severity: ___
    - [ ] 3.1.3 Stakeholders count: ___
    - [ ] 3.1.4 Final severity: ___

#### Phase 4: Output

- [ ] **4.1 Report Violations**
    - [ ] 4.1.1 Show verb list and cohesion group analysis
    - [ ] 4.1.2 Show cross-reference table with stakeholder labels