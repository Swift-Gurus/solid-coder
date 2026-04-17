---
name: structured-concurrency
displayName: Structured Concurrency
category: practice
description: Actor isolation, Task lifecycle, Sendable conformance, and async/await correctness analysis
tags:
  - structured-concurrency
---

# Structured Concurrency

> Concurrency should be structured — every async operation has a clear owner, scope, and cancellation path. Do not mix concurrency models.
---

## The Structured Concurrency Metrics Framework

## Metrics:

### SC-1: Concurrency Model Mixing

A type MUST use one concurrency model. Mixing `async/await` with GCD (`DispatchQueue.async`, `DispatchQueue.main.async`) or completion handlers in the same type creates unpredictable execution order and makes cancellation impossible.

**Detection:**

1. Count `async` functions/methods in the type
2. Count GCD calls in the same type: `DispatchQueue.main.async`, `DispatchQueue.global().async`, `.async {`, `.sync {`
3. Count completion handler patterns in the same type: closures as last parameter with `@escaping` that are called asynchronously

**Scoring:**
- If async count > 0 AND (GCD count > 0 OR completion handler count > 0) → the type mixes models

**Result:**

| Concurrency Model | Count |
|-------------------|-------|
| async/await       |       |
| GCD dispatch      |       |
| Completion handler|       |

### SC-2: Unstructured Task Lifecycle

Every `Task { }` or `Task.detached { }` created outside of SwiftUI `.task` modifier must have a stored handle and a cancellation path.

**Detection:**

1. Count `Task {` and `Task.detached {` occurrences in the type
2. For each, check:
   - Is the return value stored in a property? (e.g., `let task = Task { }`)
   - Is there a `task.cancel()` call in `deinit`, `onDisappear`, or a cleanup method?
3. Count tasks without stored handle = orphaned tasks
4. Count tasks with stored handle but no cancel call = leaked tasks

**Result:**

| Task | Stored? | Cancelled? | Status |
|------|---------|-----------|--------|
|      |         |           | orphaned / leaked / managed |

### SC-3: Concurrency Safety Bypasses

Developer escape hatches that silence the compiler without fixing the underlying problem.

**Detection:**

1. Count `@unchecked Sendable` on types with `var` properties — bypasses Sendable checking on mutable types
2. Count `nonisolated(unsafe)` usages — bypasses actor isolation checking

**Result:**

| Type/Location | Bypass | Has mutable state? | Violation? |
|--------------|--------|-------------------|------------|
|              |        |                   |            |

### SC-4: Sequential vs Concurrent Await

**Detection:**

1. Find sequences of `await` calls within the same scope (function body, closure)
2. For each pair of sequential awaits: are they independent? (second doesn't use result of first)
3. Count independent sequential awaits that could be `async let` or `TaskGroup`

**Result:**

| Location | Await A | Await B | B depends on A? | Should be concurrent? |
|----------|---------|---------|----------------|----------------------|
|          |         |         |                |                      |

### SC-5: Sync-to-Async Bridging

**Detection:**

1. Count synchronous functions that use blocking mechanisms to wait for async results:
   - `DispatchSemaphore` + `.wait()` around async code
   - `DispatchGroup` + `.wait()` around async code  
   - `RunLoop.current.run` to wait for completion
2. Count `withCheckedContinuation` / `withUnsafeContinuation` usages:
   - Is there a native async API available for what's being wrapped?
   - Does every code path resume exactly once?

**Result:**

| Location | Blocking mechanism | Native async available? | Violation? |
|----------|--------------------|------------------------|------------|
|          |                    |                        |            |

### SC-6: Duration API

Use Swift `Duration` API for all time values. Raw nanosecond/millisecond integers are error-prone and unreadable.

**Detection:**

1. Count usages of `Task.sleep(nanoseconds:)` — should be `Task.sleep(for: .seconds(N))`
2. Count raw integer literals used as time durations (nanoseconds, milliseconds) where `.seconds()`, `.milliseconds()`, `.minutes()` should be used
3. Applies to: timeouts, delays, intervals, any time duration parameter

**Result:**

| Location | Raw API / literal | Should be | Violation? |
|----------|------------------|-----------|------------|
|          |                  |           |            |

### Exceptions (NOT violations):
1. **Legacy bridge code** — `withCheckedContinuation` wrapping completion-handler APIs (e.g., `URLSession` delegate methods, CoreLocation callbacks, `NotificationCenter` observers) that Apple has not yet provided an `async` alternative for. If an `async` version of the API exists in the SDK, using continuation instead of the async version IS a violation.
2. **`@unchecked Sendable` on immutable reference types** — classes with only `let` properties that the compiler can't verify
3. **SwiftUI `.task` modifier** — framework manages Task cancellation automatically, no need to store handle
4. **Test code** — unit tests are exempt from lifecycle checks (Task { } in tests is acceptable)

### Severity Bands:
- COMPLIANT (0 violations across all metrics)
- MINOR (any of the following):
    - @MainActor slightly too broad but no data race risk
- SEVERE (any of the following):
    - 1+ concurrency model mixing in a type (SC-1)
    - 1+ orphaned or leaked Task (SC-2)
    - 1+ @unchecked Sendable on type with var properties (SC-3)
    - 1+ nonisolated(unsafe) usage (SC-3)
    - 3+ independent sequential awaits that should be concurrent (SC-4)
    - 1+ sync-to-async blocking bridge (SC-5)
    - 1+ raw nanosecond API or integer literal for duration (SC-6)
---

## Quantitative Metrics Summary
| ID   | Metric              | Threshold                                           | Severity  |
|------|---------------------|-----------------------------------------------------|-----------|
| SC-0 | Exception           | Falls into exception category                       | COMPLIANT |
| SC-1 | Model mixing        | 0 types mixing async/await with GCD/completion      | COMPLIANT |
| SC-2 | Task lifecycle      | 0 orphaned or leaked tasks                          | COMPLIANT |
| SC-3 | Safety bypasses     | 0 @unchecked Sendable on var types, 0 nonisolated(unsafe) | COMPLIANT |
| SC-4 | Sequential await    | 0-2 independent sequential awaits                   | COMPLIANT |
| SC-5 | Sync-async bridge   | 0 blocking bridges                                  | COMPLIANT |
| SC-6 | Duration API        | 0 raw nanosecond/integer durations                  | COMPLIANT |
| SC-1 | Model mixing        | 1+ type mixing async/await with GCD/completion      | SEVERE    |
| SC-2 | Task lifecycle      | 1+ orphaned or leaked task                          | SEVERE    |
| SC-3 | Safety bypasses     | 1+ @unchecked on mutable type or nonisolated(unsafe)| SEVERE    |
| SC-4 | Sequential await    | 3+ independent sequential awaits                    | SEVERE    |
| SC-5 | Sync-async bridge   | 1+ blocking bridge                                  | SEVERE    |
| SC-6 | Duration API        | 1+ raw nanosecond API or integer duration literal    | SEVERE    |
---
