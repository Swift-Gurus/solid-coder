---
name: structured-concurrency-review
type: review
rules: PRINCIPLE_FOLDER_ABSOLUTE_PATH/rule.md
output_schema: output.schema.json
---

#### Phase 1: Detection (SC-1 through SC-5)

- [ ] **1.1 SC-1: Detect Concurrency Model Mixing**
    - [ ] 1.1.1 Count `async` functions/methods in the type
    - [ ] 1.1.2 Count GCD calls in the same type: `DispatchQueue.main.async`, `DispatchQueue.global().async`, `.async {`, `.sync {`
    - [ ] 1.1.3 Count completion handler patterns in the same type: `@escaping` closures called asynchronously

      | Type | async count | GCD count | Completion handler count | Mixed? |
      |------|------------|-----------|------------------------|--------|
      |      |            |           |                        |        |

    - [ ] 1.1.4 Count types that mix models
      Model mixing violations: ___

- [ ] **1.2 SC-2: Detect Task Lifecycle Violations**
    - [ ] 1.2.1 Find all `Task {` and `Task.detached {` occurrences
    - [ ] 1.2.2 For each, check: is the return value stored in a property?
    - [ ] 1.2.3 For each stored handle, check: is there a `.cancel()` call in `deinit`, `onDisappear`, or cleanup method?
    - [ ] 1.2.4 Exclude tasks inside SwiftUI `.task` modifier (framework manages cancellation)

      | Location | Task type | Stored? | Cancelled? | Status |
      |----------|-----------|---------|-----------|--------|
      |          |           |         |           | orphaned / leaked / managed |

    - [ ] 1.2.5 Count orphaned + leaked tasks
      Lifecycle violations: ___

- [ ] **1.3 SC-3: Detect Concurrency Safety Bypasses**
    - [ ] 1.3.1 Count `@unchecked Sendable` on types with `var` properties

      | Type | Has var properties? | @unchecked Sendable? | Violation? |
      |------|-------------------|---------------------|------------|
      |      |                   |                     |            |

    - [ ] 1.3.2 Count `nonisolated(unsafe)` usages

      | Location | Why used? | Violation? |
      |----------|-----------|------------|
      |          |           |            |

    - [ ] 1.3.3 Count safety bypass violations
      Safety bypass violations: ___

- [ ] **1.4 SC-4: Detect Sequential vs Concurrent Await**
    - [ ] 1.4.1 Find sequences of `await` calls within the same scope
    - [ ] 1.4.2 For each pair: does the second use the result of the first?

      | Location | Await A | Await B | B depends on A? | Should be concurrent? |
      |----------|---------|---------|----------------|----------------------|
      |          |         |         |                |                      |

    - [ ] 1.4.3 Count independent sequential awaits
      Sequential await violations: ___

- [ ] **1.5 SC-5: Detect Sync-to-Async Bridging**
    - [ ] 1.5.1 Count blocking mechanisms used to wait for async results: `DispatchSemaphore` + `.wait()`, `DispatchGroup` + `.wait()`, `RunLoop.current.run`

      | Location | Blocking mechanism | Violation? |
      |----------|--------------------|------------|
      |          |                    |            |

    - [ ] 1.5.2 Count `withCheckedContinuation` / `withUnsafeContinuation` usages. For each: does a native async API exist for what's being wrapped?

      | Location | Wraps what API? | Native async exists? | Violation? |
      |----------|----------------|---------------------|------------|
      |          |                |                     |            |

    - [ ] 1.5.3 Count bridging violations
      Bridging violations: ___

#### Phase 2: Filter Out Exceptions

- [ ] **2.1 Cross-check exceptions** — mark exceptions

  | Type/Location | Exception Reason |
  |--------------|-----------------|
  |              |                 |

- [ ] **2.2 Exclude exceptions** — legacy bridge code (no async API available), @unchecked Sendable on immutable refs, SwiftUI .task modifier, test code

#### Phase 3: Scoring

- [ ] **3.1 Determine severity**
    - [ ] 3.1.1 Model mixing violations: ___, severity: ___
    - [ ] 3.1.2 Task lifecycle violations: ___, severity: ___
    - [ ] 3.1.3 Safety bypass violations: ___, severity: ___
    - [ ] 3.1.4 Sequential await violations: ___, severity: ___
    - [ ] 3.1.5 Bridging violations: ___, severity: ___
    - [ ] 3.1.6 Adjust severity considering exceptions.
    - [ ] 3.1.7 Final severity: ___

#### Phase 4: Output

- [ ] **4.1 Report Violations**
    - [ ] 4.1.1 Show model mixing analysis with async/GCD/completion counts per type
    - [ ] 4.1.2 Show task lifecycle analysis with orphaned/leaked/managed status per task
    - [ ] 4.1.3 Show safety bypass analysis with @unchecked and nonisolated(unsafe) tables
    - [ ] 4.1.4 Show sequential await analysis with dependency assessment per pair
    - [ ] 4.1.5 Show bridging analysis with blocking mechanism and native API availability
    - [ ] 4.1.6 Show cross-reference table with found exceptions
