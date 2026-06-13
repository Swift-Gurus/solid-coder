---
name: structured-concurrency
displayName: Structured Concurrency
category: practice
description: Actor isolation, Task lifecycle, Sendable conformance, and async/await correctness analysis
tags:
  - structured-concurrency
bands:
  SC-1:
    model_mixing:
      severe:
        greater_than_or_equal: 1
  SC-2:
    orphaned_tasks:
      severe:
        greater_than_or_equal: 1
  SC-3:
    safety_bypasses:
      severe:
        greater_than_or_equal: 1
  SC-4:
    independent_sequential_awaits:
      severe:
        greater_than_or_equal: 3
  SC-5:
    blocking_bridges:
      severe:
        greater_than_or_equal: 1
  SC-6:
    raw_duration_count:
      severe:
        greater_than_or_equal: 1
---

# Structured Concurrency

> Concurrency should be structured — every async operation has a clear owner, scope, and cancellation path. Do not mix concurrency models.
---

## The Structured Concurrency Metrics Framework

## Metrics:

### SC-1: Concurrency Model Mixing

<definition id="SC-1" name="Concurrency Model Mixing">
A type MUST use one concurrency model. Mixing `async/await` with GCD (`DispatchQueue.async`, `DispatchQueue.main.async`) or completion handlers in the same type creates unpredictable execution order and makes cancellation impossible.
</definition>

<detection id="SC-1" name="Concurrency Model Mixing">
1. Count `async` functions/methods in the type
2. Count GCD calls in the same type: `DispatchQueue.main.async`, `DispatchQueue.global().async`, `.async {`, `.sync {`
3. Count completion handler patterns in the same type: closures as last parameter with `@escaping` that are called asynchronously

**Scoring:**
- If async count > 0 AND (GCD count > 0 OR completion handler count > 0) → the type mixes models
</detection>

**Result:**

| Concurrency Model | Count |
|-------------------|-------|
| async/await       |       |
| GCD dispatch      |       |
| Completion handler|       |

### SC-2: Unstructured Task Lifecycle

<definition id="SC-2" name="Unstructured Task Lifecycle">
Every `Task { }` or `Task.detached { }` created outside of SwiftUI `.task` modifier must have a stored handle and a cancellation path.
</definition>

<detection id="SC-2" name="Unstructured Task Lifecycle">
1. Count `Task {` and `Task.detached {` occurrences in the type
2. For each, check:
   - Is the return value stored in a property? (e.g., `let task = Task { }`)
   - Is there a `task.cancel()` call in `deinit`, `onDisappear`, or a cleanup method?
3. Count tasks without stored handle = orphaned tasks
4. Count tasks with stored handle but no cancel call = leaked tasks
</detection>

**Result:**

| Task | Stored? | Cancelled? | Status |
|------|---------|-----------|--------|
|      |         |           | orphaned / leaked / managed |

### SC-3: Concurrency Safety Bypasses

<definition id="SC-3" name="Concurrency Safety Bypasses">
Developer escape hatches that silence the compiler without fixing the underlying problem.
</definition>

<detection id="SC-3" name="Concurrency Safety Bypasses">
1. Count `@unchecked Sendable` on any type — bypasses compiler Sendable verification entirely, regardless of whether properties are `let` or `var`
2. Count `nonisolated(unsafe)` usages — bypasses actor isolation checking
</detection>

**Result:**

| Type/Location | Bypass | Violation? |
|--------------|--------|------------|
|              |        |            |

### SC-4: Sequential vs Concurrent Await

<detection id="SC-4" name="Sequential vs Concurrent Await">
1. Find sequences of `await` calls within the same scope (function body, closure)
2. For each pair of sequential awaits: are they independent? (second doesn't use result of first)
3. Count independent sequential awaits that could be `async let` or `TaskGroup`
</detection>

**Result:**

| Location | Await A | Await B | B depends on A? | Should be concurrent? |
|----------|---------|---------|----------------|----------------------|
|          |         |         |                |                      |

### SC-5: Sync-to-Async Bridging

<detection id="SC-5" name="Sync-to-Async Bridging">
1. Count synchronous functions that use blocking mechanisms to wait for async results:
   - `DispatchSemaphore` + `.wait()` around async code
   - `DispatchGroup` + `.wait()` around async code  
   - `RunLoop.current.run` to wait for completion
2. Count `withCheckedContinuation` / `withUnsafeContinuation` usages:
   - Is there a native async API available for what's being wrapped?
   - Does every code path resume exactly once?
</detection>

**Result:**

| Location | Blocking mechanism | Native async available? | Violation? |
|----------|--------------------|------------------------|------------|
|          |                    |                        |            |

### SC-6: Duration API

<definition id="SC-6" name="Duration API">
Use Swift `Duration` API for all time values. Raw nanosecond/millisecond integers are error-prone and unreadable.
</definition>

<detection id="SC-6" name="Duration API">
1. Count usages of `Task.sleep(nanoseconds:)` — should be `Task.sleep(for: .seconds(N))`
2. Count raw integer literals used as time durations (nanoseconds, milliseconds) where `.seconds()`, `.milliseconds()`, `.minutes()` should be used
3. Applies to: timeouts, delays, intervals, any time duration parameter
</detection>

**Result:**

| Location | Raw API / literal | Should be | Violation? |
|----------|------------------|-----------|------------|
|          |                  |           |            |

<exceptions>
1. **Legacy bridge code** — `withCheckedContinuation` wrapping completion-handler APIs (e.g., `URLSession` delegate methods, CoreLocation callbacks, `NotificationCenter` observers) that Apple has not yet provided an `async` alternative for. If an `async` version of the API exists in the SDK, using continuation instead of the async version IS a violation.
2. **SwiftUI `.task` modifier** — framework manages Task cancellation automatically, no need to store handle
3. **Test code** — unit tests are exempt from lifecycle checks (Task { } in tests is acceptable)
</exceptions>

<severity-bands id="SC-1">
<band severity="SEVERE"><condition>model_mixing >= 1</condition></band>
<band severity="COMPLIANT"><condition>model_mixing == 0</condition></band>
</severity-bands>

<severity-bands id="SC-2">
<band severity="SEVERE"><condition>orphaned_tasks >= 1</condition></band>
<band severity="COMPLIANT"><condition>orphaned_tasks == 0</condition></band>
</severity-bands>

<severity-bands id="SC-3">
<band severity="SEVERE"><condition>safety_bypasses >= 1</condition></band>
<band severity="COMPLIANT"><condition>safety_bypasses == 0</condition></band>
</severity-bands>

<severity-bands id="SC-4">
<band severity="SEVERE"><condition>independent_sequential_awaits >= 3</condition></band>
<band severity="COMPLIANT"><condition>independent_sequential_awaits < 3</condition></band>
</severity-bands>

<severity-bands id="SC-5">
<band severity="SEVERE"><condition>blocking_bridges >= 1</condition></band>
<band severity="COMPLIANT"><condition>blocking_bridges == 0</condition></band>
</severity-bands>

<severity-bands id="SC-6">
<band severity="SEVERE"><condition>raw_duration_count >= 1</condition></band>
<band severity="COMPLIANT"><condition>raw_duration_count == 0</condition></band>
</severity-bands>

---

## Quantitative Metrics Summary
| ID   | Metric              | Threshold                                           | Severity  |
|------|---------------------|-----------------------------------------------------|-----------|
| SC-0 | Exception           | Falls into exception category                       | COMPLIANT |
| SC-1 | Model mixing        | 0 types mixing async/await with GCD/completion      | COMPLIANT |
| SC-2 | Task lifecycle      | 0 orphaned or leaked tasks                          | COMPLIANT |
| SC-3 | Safety bypasses     | 0 @unchecked Sendable on owned types, 0 nonisolated(unsafe) | COMPLIANT |
| SC-4 | Sequential await    | 0-2 independent sequential awaits                   | COMPLIANT |
| SC-5 | Sync-async bridge   | 0 blocking bridges                                  | COMPLIANT |
| SC-6 | Duration API        | 0 raw nanosecond/integer durations                  | COMPLIANT |
| SC-1 | Model mixing        | 1+ type mixing async/await with GCD/completion      | SEVERE    |
| SC-2 | Task lifecycle      | 1+ orphaned or leaked task                          | SEVERE    |
| SC-3 | Safety bypasses     | 1+ @unchecked Sendable on owned type or nonisolated(unsafe) | SEVERE    |
| SC-4 | Sequential await    | 3+ independent sequential awaits                    | SEVERE    |
| SC-5 | Sync-async bridge   | 1+ blocking bridge                                  | SEVERE    |
| SC-6 | Duration API        | 1+ raw nanosecond API or integer duration literal    | SEVERE    |
---
