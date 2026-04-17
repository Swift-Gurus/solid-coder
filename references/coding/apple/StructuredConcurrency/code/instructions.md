---
name: structured-concurrency-code
type: code
---

# Structured Concurrency Coding Instructions

Every async operation, task creation, or concurrency boundary crossing is a potential violation. Run this checklist twice — once before writing (plan your approach) and once after writing (verify what you wrote).

---

## Before Writing Any Concurrent Code

```
You are about to write async code, create a Task, or bridge between sync and async.
         │
         ▼
SC-1: Are you mixing concurrency models in this type?
    Does this type already have async/await methods?
    YES → Do NOT add DispatchQueue.async, .sync, or completion handlers.
          Migrate the new code to async/await.
    Does this type already have GCD or completion handlers?
    YES → Do NOT add async/await. Either migrate the entire type
          or keep the existing model.
    One model per type. No mixing.
         │
         ▼
SC-2: Are you creating a Task?
    Inside SwiftUI .task modifier → framework handles cancellation. Proceed.
    Otherwise:
       → Store the Task handle. If the project has a task management library or utility in context knowledge, use it. Otherwise store in a property.
       → Cancel it in deinit or cleanup.
       → If the task has a long loop → add Task.checkCancellation() inside.
    Using Task.detached? → Do you need to escape actor context?
       Usually no → use regular Task { } instead.
         │
         ▼
SC-3: Are you about to use @unchecked Sendable or nonisolated(unsafe)?
    These bypass the compiler's safety checks. Do NOT use them.
    Instead:
       → Make properties `let` so the type is naturally Sendable
       → Convert to an actor if mutable state is needed
       → Restructure to avoid the boundary crossing
         │
         ▼
SC-4: Are you calling multiple independent async operations?
    YES and they don't depend on each other
       → Use async let for 2-3 calls
       → Use TaskGroup for dynamic count
       → Do NOT await them sequentially
    NO (each depends on the previous result)
       → Sequential await is correct. Proceed.
         │
         ▼
SC-5: Are you bridging sync → async?
    Do NOT use DispatchSemaphore or DispatchGroup to block.
    Instead:
       → Make the caller async
       → Or use Task { } at the call boundary
    Using withCheckedContinuation?
       → Does a native async API exist? Use that instead.
       → No async API exists? → Legacy bridge exception, acceptable.
         │
         ▼
Validate against severity bands in rule.md:
    COMPLIANT or MINOR → Proceed.
    SEVERE             → Do not write it this way. Use loaded fix instructions to restructure.
```

## Duration API

Always use `Duration` API for time values — never raw nanoseconds:
- `Task.sleep(for: .seconds(2))` not `Task.sleep(nanoseconds: 2_000_000_000)`
- `.seconds(5)`, `.milliseconds(500)`, `.minutes(1)` — use the appropriate unit
- This applies to timeouts, delays, intervals — anywhere a time duration is expressed

## Exceptions — Not Violations

These are defined in rule.md. Do not expand this list.
