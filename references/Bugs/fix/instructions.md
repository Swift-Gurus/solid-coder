---
name: bugs-fix
type: fix
input_schema: PRINCIPLE_FOLDER_ABSOLUTE_PATH/review/output.schema.json
output_schema: output.schema.json
---

### Phase 0: Load Context

- [ ] **0.1 Read the review findings JSON** (provided as structured input_schema)
- [ ] **0.2 Read the source file** (provided as input)

#### Phase 1: Determine Fix Strategy

- [ ] **1.1 Read `scoring.final_severity` from findings**
    - MINOR — light touch: add guard clauses or nil coalescing for 1-2 force unwraps
    - SEVERE — full fix based on which metrics triggered

- [ ] **1.2 Identify which metrics triggered the severity**
    - BUG-1 (unsafe unwrap) — `guard_clause`, `optional_binding`, `nil_coalescing`, `safe_subscript`
    - BUG-2 (logic/semantic) — `remove_dead_code`, `add_missing_case`
    - BUG-3 (concurrency) — `actor_isolation`, `dispatch_to_background`, `add_synchronization`
    - BUG-4 (safety/correctness) — `weak_capture`, `add_error_propagation`, `add_resource_cleanup`
    - Multiple — combine patterns as needed

#### Phase 2: Identify Suggestions

- [ ] **2.1 Analyze findings** — read metrics (unsafe unwrap tables, logic analysis, concurrency analysis, safety/correctness analysis)
- [ ] **2.2 Propose suggestion** — which patterns to apply, which code sites to fix
- [ ] **2.3 Create todo items** — concrete actionable steps to implement the fix:
    - [ ] For BUG-1 (unsafe unwrap/access):
        - Replace `value!` with `guard let value = value else { return }` or
          `if let` binding with appropriate handling
        - Replace `as!` with `as?` followed by guard/if-let handling
        - Replace `try!` with `do { try ... } catch { ... }` with appropriate
          error handling
        - Replace `array[index]` with safe subscript: `guard array.indices.contains(index)`
          or use `array[safe: index]` extension
        - Replace `dictionary[key]!` with `dictionary[key] ?? defaultValue` or
          guard let binding
        - Replace `.first!` / `.last!` with `.first` / `.last` + guard/if-let
    - [ ] For BUG-2 (logic/semantic):
        - Delete unreachable code after unconditional return/throw/fatalError
        - Remove dead branches — replace with the live path only
        - Fix contradictory conditions — correct the logic to match intent
        - Add missing switch cases with explicit handling (not empty default)
        - Replace empty `default: break` with exhaustive case handling so the
          compiler catches future enum additions
    - [ ] For BUG-3 (concurrency):
        - Wrap shared mutable state in an `actor`
        - Replace `DispatchQueue.main.sync` with `.async` (or restructure to
          avoid synchronous dispatch entirely)
        - Move blocking I/O to background: `Task { }` or
          `DispatchQueue.global().async`
        - Add `@MainActor` to properties/methods that require main-thread access
        - Replace `static var` on classes with `actor`-based shared state or
          `@MainActor` annotation
        - Replace `semaphore.wait()` on main with async/await pattern
    - [ ] For BUG-4 (safety/correctness):
        - Add `[weak self]` to closure captures where `self` is stored
        - Add `weak var delegate` for delegate properties
        - Add `deinit` cleanup: `timer?.invalidate()`,
          `NotificationCenter.default.removeObserver(self)`
        - Add `defer { resource.close() }` immediately after resource acquisition
        - Replace empty `catch {}` with `throw` or meaningful recovery logic
        - Ensure completion handlers are called on ALL code paths (including
          error branches) — add missing `completion(.failure(error))` calls
        - Replace `==` on floating point with `abs(a - b) < epsilon`
        - Replace `===` with `==` (or vice versa) where intent is equality not identity
        - Replace collection mutation during iteration with a copy or filter pattern
    - Each todo item should be a single, implementable action

#### Phase 3: Write suggested_fix

- [ ] **3.1 Write full code snippets** showing:
    - For BUG-1: guard let / if let replacing force unwraps, safe subscript
      replacing direct access, do-try-catch replacing try!
    - For BUG-2: cleaned code with dead code removed, explicit switch cases,
      corrected conditions
    - For BUG-3: actor wrapping shared state, @MainActor annotations, async
      dispatch replacing sync
    - For BUG-4: [weak self] captures, defer cleanup, proper error propagation,
      completion handlers on all paths
    - Before/after of the affected code
- [ ] **3.2 Predict post-fix metrics** (violation counts per category: unsafe
  unwrap, logic/semantic, concurrency, safety/correctness)

#### Phase 4: Generate Output

- [ ] **4.1 Produce JSON matching output schema**
    - [ ] 4.1.1 Fill `suggested_fix` with the full text + code snippets from Phase 3
    - [ ] 4.1.2 Fill `todo_items` with the actionable steps from Phase 2.3
    - [ ] 4.1.3 Fill `verification` with predicted metrics from Phase 3.2
    - [ ] 4.1.4 Fill `addresses` with finding IDs this suggestion resolves

#### Constraints
- Include full code snippets in suggested_fix (before/after for each fix site)
- Todo items must be concrete and implementable (not vague)
- Preserve existing public API — fixes should not change method signatures
- Match fix depth to severity (MINOR — guard clause only, SEVERE — full fix)
- When fixing retain cycles, verify the `[weak self]` does not break expected
  strong reference semantics (e.g., intentional retain in animation blocks)
- When adding guard clauses, provide meaningful early return or error
  propagation — not silent `return` that hides failures
- When converting to actors, ensure all access points are updated to use
  `await` — do not leave synchronous call sites broken
- When replacing empty `default: break`, only do so if the enum is owned by
  the project (not framework enums that may add cases)
