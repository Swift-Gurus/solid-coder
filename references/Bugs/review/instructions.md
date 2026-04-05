---
name: bugs-review
type: review
rules: PRINCIPLE_FOLDER_ABSOLUTE_PATH/rule.md
output_schema: output.schema.json
---

### Phase 0: Load Examples for context.
- [ ] **0.1 Read all examples** — Glob `PRINCIPLE_FOLDER_ABSOLUTE_PATH/Examples/*` and read every file found

#### Phase 1: Detection (BUG-1 through BUG-4 run independently and in parallel if possible)

- [ ] **1.1 BUG-1: Detect Unsafe Unwrap and Access**
    - [ ] 1.1.1 Scan for force unwraps — `value!`, `as!`, `try!`, implicitly unwrapped optionals beyond IBOutlet

      | Location | Pattern | Code | Exception? |
      |----------|---------|------|------------|
      |          |         |      |            |

    - [ ] 1.1.2 Scan for unhandled optionals — `_ = optionalFunc()`, unused optional chain result, `try?` discarding error+value

      | Location | Pattern | Code | Exception? |
      |----------|---------|------|------------|
      |          |         |      |            |

    - [ ] 1.1.3 Scan for unguarded collection access — direct subscript without bounds check, `.first!`, `.last!`, `dictionary[key]!`

      | Location | Pattern | Code | Exception? |
      |----------|---------|------|------------|
      |          |         |      |            |

    - [ ] 1.1.4 Count unsafe unwrap/access violations
      Violations: ___

- [ ] **1.2 BUG-2: Detect Logic and Semantic Bugs**
    - [ ] 1.2.1 Scan for unreachable code — statements after unconditional return/throw/fatalError/break/continue

      | Location | Unreachable Statement | After | Exception? |
      |----------|-----------------------|-------|------------|
      |          |                       |       |            |

    - [ ] 1.2.2 Scan for dead branches — always-true/always-false conditions, redundant guards, impossible switch cases

      | Location | Condition | Why Dead | Exception? |
      |----------|-----------|----------|------------|
      |          |           |          |            |

    - [ ] 1.2.3 Scan for contradictory conditions — impossible conjunctions, sequential contradictions

      | Location | Conditions | Contradiction | Exception? |
      |----------|------------|---------------|------------|
      |          |            |               |            |

    - [ ] 1.2.4 Scan for missing edge cases — empty `default: break` on enum switch, uncovered comparison ranges, `if/else if` gaps

      | Location | Pattern | Missing Case | Exception? |
      |----------|---------|-------------|------------|
      |          |         |             |            |

    - [ ] 1.2.5 Count logic/semantic violations
      Violations: ___

- [ ] **1.3 BUG-3: Detect Concurrency Bugs**
    - [ ] 1.3.1 Scan for data races — shared mutable `var` across boundaries without synchronization, `nonisolated` access to actor state

      | Location | Shared State | Access Contexts | Protection | Violation? |
      |----------|-------------|-----------------|------------|------------|
      |          |             |                 |            |            |

    - [ ] 1.3.2 Scan for deadlock risk — `DispatchQueue.main.sync` from main, `semaphore.wait()` on main, nested locks

      | Location | Pattern | Context | Violation? |
      |----------|---------|---------|------------|
      |          |         |         |            |

    - [ ] 1.3.3 Scan for main-thread blocking — sync I/O, `Thread.sleep`/`usleep` on main, long-running loops on main

      | Location | Blocking Call | Queue/Context | Violation? |
      |----------|--------------|---------------|------------|
      |          |              |               |            |

    - [ ] 1.3.4 Scan for unsafe shared mutable state — `static var` on non-actor types, global mutable variables, `var` properties without `@MainActor` or synchronization

      | Location | Declaration | Why Unsafe | Violation? |
      |----------|-------------|-----------|------------|
      |          |             |           |            |

    - [ ] 1.3.5 Count concurrency violations
      Violations: ___

- [ ] **1.4 BUG-4: Detect Safety and Correctness Issues**
    - [ ] 1.4.1 Scan for resource leaks — retain cycles (`self` in stored closures, non-weak delegates), unclosed file handles, unremoved observers, non-invalidated timers

      | Location | Resource | Acquisition | Release? | Violation? |
      |----------|----------|-------------|----------|------------|
      |          |          |             |          |            |

    - [ ] 1.4.2 Scan for error handling gaps — empty `catch {}`, `catch { print(error) }` without propagation, incomplete catch, completion handlers not called on all paths

      | Location | Pattern | Missing Handling | Violation? |
      |----------|---------|-----------------|------------|
      |          |         |                 |            |

    - [ ] 1.4.3 Scan for correctness violations — float `==`, `===` vs `==` confusion, mutation during iteration, `Date()`/`UUID()` in deterministic contexts

      | Location | Pattern | Code | Violation? |
      |----------|---------|------|------------|
      |          |         |      |            |

    - [ ] 1.4.4 Count safety/correctness violations
      Violations: ___

#### Phase 1.5: Reconstruction Verification (hallucination guard)

For EACH finding from Phase 1, verify it is grounded in actual code — not hallucinated.

- [ ] **1.5.1 For each finding, run the reconstruction test:**

  1. **Take** the finding description (the `issue` field)
  2. **Ask yourself**: "What code pattern would produce this finding?"
  3. **Generate** a reconstructed description of the code you expect to see
  4. **Compare** the original finding against the reconstructed description
  5. **Score** similarity 0–1:
     - **1.0** — reconstruction matches the actual code exactly
     - **0.7–0.9** — reconstruction describes the same pattern with minor wording differences
     - **0.4–0.6** — reconstruction is vaguely related but misses key details
     - **0.0–0.3** — reconstruction does not match the actual code at all

  | Finding ID | Issue (original) | Reconstructed Pattern | Actual Code (quote) | Similarity | Keep? |
  |------------|-----------------|----------------------|--------------------|-----------:|-------|
  |            |                 |                      |                    |            |       |

- [ ] **1.5.2 Drop findings with similarity < 0.7**
  These findings are likely hallucinated — the model described a bug that
  doesn't match the actual code. Remove them from the findings list before
  proceeding.

- [ ] **1.5.3 Flag findings with similarity 0.7–0.8 as LOW_CONFIDENCE**
  These findings may be real but the description is imprecise. Keep them but
  mark them so downstream consumers (synthesize, report) can weigh them
  accordingly.

- [ ] **1.5.4 Update violation counts** — recount after dropping failed reconstructions

#### Phase 2: Filter Out Exceptions

- [ ] **2.1 Cross-check exceptions** — mark exceptions

  | Location | Exception Reason |
  |----------|-----------------|
  |          |                 |

- [ ] **2.2 Exclude exceptions** — exclude:
  - Test files (`*Tests.swift`, `*Test.swift`, test targets) — force unwraps and `try!` acceptable
  - Controlled force unwraps on compile-time-known values (`URL(string: "literal")!`, etc.)
  - `@IBOutlet` implicitly unwrapped optionals
  - `precondition`, `assert`, `fatalError` as intentional contract enforcement
  - Documented `default: break` in switches with explicit developer comment

#### Phase 3: Scoring

- [ ] **3.1 Determine severity**
    - [ ] 3.1.1 Unsafe unwrap/access violations: ___, severity: ___
    - [ ] 3.1.2 Logic/semantic violations: ___, severity: ___
    - [ ] 3.1.3 Concurrency violations: ___, severity: ___
    - [ ] 3.1.4 Safety/correctness violations: ___, severity: ___
    - [ ] 3.1.5 Adjust severity considering exceptions.
    - [ ] 3.1.6 Final severity: ___

#### Phase 4: Output

- [ ] **4.1 Report Violations**
    - [ ] 4.1.1 Show unsafe unwrap/access analysis with force unwrap, unhandled optional, and unguarded access tables
    - [ ] 4.1.2 Show logic/semantic analysis with unreachable code, dead branches, contradictions, and missing edge case tables
    - [ ] 4.1.3 Show concurrency analysis with data race, deadlock, blocking, and shared state tables
    - [ ] 4.1.4 Show safety/correctness analysis with resource leak, error handling, and correctness tables
    - [ ] 4.1.5 Show cross-reference table with found exceptions
