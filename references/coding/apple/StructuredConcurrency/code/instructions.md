---
name: structured-concurrency-code
type: code
---

# Structured Concurrency Coding Instructions

<rule id="SC-1" name="One Concurrency Model Per Type">
Before adding any async, GCD, or completion-handler code to an existing type:
- Type already has `async/await` methods → do NOT add `DispatchQueue.async`, `.sync`, or completion handlers. Write the new code as `async` instead.
- Type already has GCD or completion handlers → do NOT add `async/await`. Either migrate the whole type or stay consistent with the existing model.
- One model per type. No mixing.
</rule>

<rule id="SC-2" name="Task Lifecycle">
Before creating any `Task { }` or `Task.detached { }`:
- Always store the handle in a property — never fire-and-forget.
- Always cancel it in `deinit` or a dedicated cleanup method.
- If the task contains a long-running loop → add `Task.checkCancellation()` inside the loop.
- `Task.detached` is only justified when you need to escape actor context — default to `Task { }`.
- Exception: tasks created inside a SwiftUI `.task` modifier — the framework manages cancellation automatically.
</rule>

<rule id="SC-3" name="No Concurrency Safety Bypasses">
Do NOT use `@unchecked Sendable` or `nonisolated(unsafe)` — they silence the compiler without fixing the problem.

Instead:
- No reference/identity requirement → convert to `struct` (synthesised `Sendable` when all stored properties are `Sendable`).
- Mutable state with concurrent access → use `actor` — isolation is compiler-verified.
- Third-party non-`Sendable` type you don't own:
  - iOS 16+ / macOS 13+ → wrap in `OSAllocatedUnfairLock<T>`.
  - Older deployment → use an existing project lock abstraction, or create `Lock<T>` backed by `os_unfair_lock`.
- `@unchecked Sendable` is only acceptable on a type that IS itself a synchronisation primitive using OS-level constructs (e.g. your own `Lock<T>`). It is a one-time project-level utility, not a per-use-case escape hatch.
</rule>

<rule id="SC-4" name="Concurrent Awaits for Independent Calls">
Before writing two or more sequential `await` calls in the same scope:
- Ask: does the second call depend on the result of the first?
- YES → sequential `await` is correct. Proceed.
- NO (they are independent) → do NOT await sequentially.
  - 2–3 independent calls → use `async let`.
  - Dynamic count → use `TaskGroup`.
</rule>

<rule id="SC-5" name="No Sync-to-Async Blocking">
Before bridging synchronous code to async results:
- Do NOT use `DispatchSemaphore`, `DispatchGroup.wait()`, or `RunLoop.current.run` to block and wait for async results.
- Make the caller `async` instead, or use `Task { }` at the boundary.
- Before using `withCheckedContinuation`: check if a native `async` API exists — if it does, use that instead. `withCheckedContinuation` is only acceptable as a legacy bridge for APIs that have no `async` alternative.
</rule>

<rule id="SC-6" name="Duration API">
Always use the `Duration` API for time values — never raw integers:
- `Task.sleep(for: .seconds(2))` not `Task.sleep(nanoseconds: 2_000_000_000)`.
- Use `.seconds()`, `.milliseconds()`, `.minutes()` for timeouts, delays, and intervals.
</rule>

<exceptions>
- Legacy bridge — `withCheckedContinuation` wrapping completion-handler APIs (e.g., URLSession delegate methods, CoreLocation callbacks, NotificationCenter observers) where Apple has not yet provided an `async` alternative. If an `async` version exists in the SDK, using continuation instead IS a violation.
- SwiftUI `.task` modifier — framework manages Task cancellation automatically. No need to store the handle.
- Test code — unit tests are exempt from Task lifecycle checks.
</exceptions>
