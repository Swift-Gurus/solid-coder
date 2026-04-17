---
name: structured-concurrency-fix
type: fix
input_schema: PRINCIPLE_FOLDER_ABSOLUTE_PATH/review/output.schema.json
output_schema: output.schema.json
---

### Phase 0: Load Context

- [ ] **0.1 Read the review findings JSON** (provided as structured input_schema)
- [ ] **0.2 Read the source file** (provided as input)

#### Phase 1: Determine Fix Strategy

- [ ] **1.1 Read `scoring.final_severity` from findings**
    - MINOR → narrow @MainActor scope only
    - SEVERE → full restructuring based on which metrics triggered

- [ ] **1.2 Identify which metrics triggered the severity**
    - SC-1 (model mixing) → Migrate GCD/completion to async/await
    - SC-2 (task lifecycle) → Store Handle + Cancel
    - SC-3 (safety bypasses) → Remove @unchecked / nonisolated(unsafe), fix underlying issue
    - SC-4 (sequential await) → Parallelize with async let or TaskGroup
    - SC-5 (sync-async bridge) → Remove blocking, make caller async
    - Multiple → combine patterns as needed

#### Phase 2: Identify Suggestions

- [ ] **2.1 Analyze findings** — read metrics tables
- [ ] **2.2 Propose suggestion** — which patterns to migrate, which tasks to manage
- [ ] **2.3 Create todo items** — concrete actionable steps:
    - [ ] For SC-1 (model mixing):
        - Replace `DispatchQueue.main.async { }` with `await MainActor.run { }` or mark the method `@MainActor`
        - Replace `DispatchQueue.global().async { }` — question why background dispatch is needed. Usually the function should be `async` and the caller should `await` it. Only use `Task { }` when fire-and-forget is the actual intent.
        - Replace completion handler patterns with async/await return values
        - Remove all GCD imports if no GCD usage remains
    - [ ] For SC-2 (task lifecycle):
        - Store Task handle — if the project has a task management library or utility in context knowledge, use it. Otherwise store in a property: `private var loadTask: Task<Void, Never>?`
        - Add cancellation in deinit or cleanup: `loadTask?.cancel()`
        - Replace `Task.detached { }` with `Task { }` when actor context inheritance is correct
        - Add `try Task.checkCancellation()` inside long loops
    - [ ] For SC-3 (safety bypasses):
        - `@unchecked Sendable` on type with var → make properties `let`, convert to actor, or use proper synchronization
        - `nonisolated(unsafe)` → restructure to avoid the boundary crossing, or use actor isolation
    - [ ] For SC-4 (sequential await):
        - 2-3 independent calls → replace with `async let a = ...; async let b = ...`
        - Dynamic number → replace with `withTaskGroup` or `withThrowingTaskGroup`
    - [ ] For SC-5 (sync-async bridge):
        - Remove `DispatchSemaphore`/`DispatchGroup` blocking → make the caller async
        - Replace `withCheckedContinuation` with native async API if one exists
        - If no async API exists → keep continuation but document why (legacy bridge exception)
    - Each todo item should be a single, implementable action

#### Phase 3: Write suggested_fix

- [ ] **3.1 Write full code snippets** showing before/after
- [ ] **3.2 Predict post-fix metrics** per type

#### Phase 4: Generate Output

- [ ] **4.1 Produce JSON matching output schema**
    - [ ] 4.1.1 Fill `suggested_fix` with full text + code snippets from Phase 3
    - [ ] 4.1.2 Fill `todo_items` with actionable steps from Phase 2.3
    - [ ] 4.1.3 Fill `verification` with predicted metrics from Phase 3.2
    - [ ] 4.1.4 Fill `addresses` with finding IDs this suggestion resolves

    - [ ] For Duration API:
        - Replace `Task.sleep(nanoseconds:)` with `Task.sleep(for: .seconds(N))` or appropriate unit
        - Replace any raw nanosecond/millisecond integer literals for time with `.seconds()`, `.milliseconds()`, `.minutes()`
        - Applies to timeouts, delays, intervals — anywhere a time duration is expressed

#### Constraints
- Include full code snippets in suggested_fix
- Todo items must be concrete and implementable
- Preserve existing public API
- When migrating GCD → async/await, ensure callers are updated too
- When removing safety bypasses, fix the root cause — don't just move the bypass elsewhere
