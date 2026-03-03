---
name: lsp-review
type: review
rules: PRINCIPLE_FOLDER_ABSOLUTE_PATH/rule.md
output_schema: output.schema.json
---

### Phase 0: Load Examples for context.
- [ ] **0.1 Read all references/examples**
  - [] [FOR EVERY FILE IN PRINCIPLE_FOLDER_ABSOLUTE_PATH/Examples CREATE TODO]

#### Phase 1: Detection (LSP-1, LSP-2, and LSP-3 run independently and in parallel if possible)

- [ ] **1.1 LSP-1: Count Type Checks**
    - [ ] 1.1.1 Scan for `is`, `as?`, `as!`, `type(of:)` patterns used with concrete types, protocols, interfaces

      | Pattern | Concrete Type | Base Type/Protocol  | 
      |---------|--------------|---------------------|
      |         |              |                     |
    - [ ]  1.1.2 Count out exceptions — for each typecast, identify the source type and search the project/local package files for its definition. If found → developer-owned (not exception). If not found → external (exception). See typecast-lsp-exception.swift in Examples
    - [ ] 1.1.3 Count net type checks (total - exceptions)

      Net type check count: ___

- [ ] **1.2 LSP-2: Contract Compliance (Inheritance Only)**
    - [ ] 1.2.1 Detect class inheritance — does the class inherit from a concrete base class?
      - If NO → LSP-2 not applicable, skip to 1.3
      - If YES → continue
    - [ ] 1.2.2 Read the base class source code
    - [ ] 1.2.3 For each `override` method, compare base vs subtype:
      - [ ] 1.2.3.1 Precondition changes — list guard clauses in base and subtype

        | Method | Base Guards | Subtype Guards | New Guards |
        |--------|------------|----------------|------------|
        |        |            |                |            |
      - [ ] 1.2.3.2 Postcondition weakening — list assertions/guarantees in base and subtype

        | Method | Base Assertions | Subtype Assertions | Weakened |
        |--------|----------------|-------------------|----------|
        |        |                |                   |          |
      - [ ] 1.2.3.3 Invariant violations — check for exposed mutable state

        | Property | Base Access | Subtype Access | Violation |
        |----------|------------|----------------|-----------|
        |          |            |                |           |
    - [ ] 1.2.4 Count total contract violations

      Contract violation count: ___

- [ ] **1.3 LSP-3: Empty/Non-Implemented Methods**
    - [ ] 1.3.1 Identify the protocol/interface the class conforms to
    - [ ] 1.3.2 Count total methods/vars in the interface

      Total methods/vars in interface: ___
    - [ ] 1.3.3 Count empty methods/vars (body contains no statements, or only a comment)

      Empty methods/vars: ___
    - [ ] 1.3.4 Count methods whose entire body is a crash assertion (fatalError, preconditionFailure, assertionFailure — the method exists only to satisfy protocol conformance)

      Fatal error methods: ___
    - [ ] 1.3.5 Apply NoOp exception — if the name states it is a NoOp AND 100% of methods/vars from the contract are empty or resolved to default values → exception, not a violation
    - [ ] 1.3.6 Calculate empty percentage: empty (non-fatal) methods/vars / total methods/vars

      Empty methods/vars percentage: ___

#### Phase 2: Scoring

- [ ] **2.1 Determine severity**
    - [ ] 2.1.1 Net type checks: ___, severity: ___
    - [ ] 2.1.2 Has inheritance: yes/no
    - [ ] 2.1.3 Contract violations: ___, severity: ___
    - [ ] 2.1.4 Empty methods percentage: ___, severity: ___
    - [ ] 2.1.5 Fatal error methods: ___, severity: ___
    - [ ] 2.1.6 NoOp exception applied: yes/no
    - [ ] 2.1.7 Final severity: ___

#### Phase 3: Output

- [ ] **3.1 Report Violations**
    - [ ] 3.1.1 Show type check table with framework-API exception analysis
    - [ ] 3.1.2 Show contract compliance comparison tables (if inheritance detected)
    - [ ] 3.1.3 Show empty methods/fatal error methods table (if LSP-3 violations found)
