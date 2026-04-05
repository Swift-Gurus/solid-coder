---
name: bugs
displayName: Bug Patterns
category: practice
description: Common bug pattern detection, logic/semantic analysis, concurrency safety, and correctness verification with direct severity scoring
---

# Bug Patterns

> Bugs hide in patterns. Detect the pattern, prevent the crash. — Defensive Programming
---

## The Bug Patterns Metrics Framework

This framework provides objective scoring for common bug patterns in Swift code.
The primary metrics are unsafe unwrap/access, logic/semantic bugs, concurrency
bugs, and safety/correctness — all directly observable from source code.

## Metrics:

### BUG-1: Unsafe Unwrap and Access

Detect force unwraps, unhandled optionals, and unguarded collection access —
patterns that crash at runtime.

**Definition:** Safe code never assumes an optional has a value or a collection
has an element at an index without checking first. Force unwraps, force casts,
and unguarded subscripts are ticking time bombs — they work until they don't.

**Detection:**

1. **Force unwraps** — scan for `!` on optional values:
   - `value!` (force unwrap of optional)
   - `as!` (force cast)
   - `try!` (force try)
   - Implicitly unwrapped optionals (`var x: Type!`) used beyond IBOutlet/Interface Builder context
2. **Unhandled optionals** — detect optionals silently discarded:
   - `_ = optionalReturningFunction()` where the optional is never checked
   - Optional chaining result unused: `object?.method()` where method returns
     a value that is silently dropped
   - `try?` that silently discards the error AND the return value in production
     code (losing error information)
3. **Unguarded collection access** — detect direct subscript without bounds check:
   - `array[index]` without prior `guard index < array.count` or `indices.contains(index)`
   - `dictionary[key]!` (force unwrap of dictionary lookup)
   - `array.first!`, `array.last!`

**Count:** Number of unsafe unwrap/access instances found.

### BUG-2: Logic and Semantic Bugs

Detect unreachable code, dead branches, contradictory conditions, and missing
edge cases.

**Definition:** Logic bugs are code that compiles and runs but does not do what
the developer intended. They are silent — no crash, no warning, just wrong
behavior.

**Detection:**

1. **Unreachable code** — statements after unconditional `return`, `throw`,
   `fatalError()`, `break`, `continue`
2. **Dead branches** — conditions that are always true or always false within
   the local scope:
   - `if let x = x` immediately after a non-optional assignment
   - Guard conditions that duplicate prior guards
   - Switch cases that can never match given the type
3. **Contradictory conditions** — mutually exclusive checks in the same scope:
   - `if x > 5 && x < 3` (impossible)
   - Sequential guards that contradict: `guard x != nil` followed by code
     that assumes `x` is nil
4. **Missing edge cases** — detectable gaps in exhaustive handling:
   - Switch on enum with empty `default:` / `default: break` that silently
     hides future cases
   - `if/else if` chains on enums without covering all cases
   - Comparison chains with gaps (e.g., handles `> 0` and `< 0` but not `== 0`)

**Count:** Number of logic/semantic bug instances found.

### BUG-3: Concurrency Bugs

Detect data races, deadlocks, main-thread blocking, and unsafe shared mutable
state.

**Definition:** Concurrency bugs are the hardest to reproduce and diagnose. A
data race may crash once in a thousand runs. A deadlock may only manifest under
load. These patterns must be caught statically.

**Detection:**

1. **Data races** — shared mutable state accessed from multiple contexts without
   synchronization:
   - `var` properties on non-`Sendable` types passed across actor/thread boundaries
   - Properties mutated in closures dispatched to different queues without
     lock/actor protection
   - `nonisolated` access to actor-isolated state
2. **Deadlock risk** — synchronous waits on main thread or nested lock
   acquisitions:
   - `DispatchQueue.main.sync` called from main thread
   - `semaphore.wait()` on main thread
   - Nested `lock.lock()` calls on non-recursive locks
   - `Task { await ... }` blocking patterns
3. **Main-thread blocking** — heavy work on main queue:
   - Synchronous network/file I/O calls not dispatched to background
   - `Thread.sleep` / `usleep` on main thread
   - Long-running loops without yielding
4. **Unsafe shared mutable state** — architectural patterns that invite races:
   - `static var` on non-actor types (singleton mutable state)
   - Global mutable variables
   - Classes with `var` properties accessed from closures without `@MainActor`
     or explicit synchronization

**Count:** Number of concurrency bug instances found.

### BUG-4: Safety and Correctness

Detect resource leaks, error handling gaps, and correctness violations.

**Definition:** Safety bugs are code that works most of the time but leaks
resources, swallows errors, or produces subtly wrong results. They accumulate
over time — a retain cycle that causes a slow memory leak, an empty catch that
hides a failure mode.

**Detection:**

1. **Resource leaks** — resources acquired but not released:
   - Retain cycles: closures capturing `self` strongly in stored closure
     properties, delegates not declared `weak`, `NotificationCenter` observers
     not removed, `Timer` not invalidated
   - File handles / streams opened but not closed in all paths (including
     error paths)
   - `URLSession` tasks created without cancellation path
2. **Error handling gaps** — errors swallowed or incompletely handled:
   - Empty `catch {}` blocks
   - `catch { print(error) }` without propagation or recovery (logging is
     not handling)
   - `catch` that catches all errors but only handles specific ones, silently
     dropping others
   - Completion handlers that are not called on all paths (missing call in
     error branch)
3. **Correctness violations** — semantically wrong patterns:
   - Comparing floating point with `==` instead of epsilon comparison
   - Using `===` (identity) where `==` (equality) was intended, or vice versa
   - Mutating a collection while iterating it
   - `Date()` / `UUID()` in deterministic contexts (breaks testability and
     reproducibility)

**Count:** Number of safety/correctness instances found.

### Exceptions (NOT violations):
1. **Test files** — files whose name ends in `Tests.swift`, `Test.swift`, or
   reside in a test target directory:
   - Force unwraps (`!`) are acceptable in tests (test failures are the mechanism)
   - `try!` is acceptable in test setup where failure means broken test, not
     broken production code
   - `XCTUnwrap` is the preferred pattern but `!` is not a violation
2. **Controlled force unwraps** — force unwraps on compile-time-known values:
   - `URL(string: "https://example.com")!` (literal string, known to succeed)
   - `UIImage(named: "icon")!` in asset-catalog-backed code
   - `NumberFormatter().number(from: literalString)!`
3. **IBOutlet/Storyboard** — `@IBOutlet var label: UILabel!` is the standard
   UIKit pattern
4. **Precondition/assertion** — `precondition`, `assert`, `fatalError` used as
   intentional contract enforcement (not a bug, a design choice)
5. **Documented protocol witness** — empty `default: break` in switches that
   genuinely have no action for unknown future cases AND the developer has
   documented the reason

### Severity Bands:
- COMPLIANT (0 violations across all metrics)
- MINOR (any of the following):
    - 1-2 BUG-1 violations only (force unwraps / unguarded access), all else clean
    - 1 minor BUG-4 correctness issue only (floating point comparison, Date() in non-critical path)
- SEVERE (any of the following):
    - 3+ BUG-1 violations (systemic unsafe unwrap pattern)
    - 1+ BUG-2 violations (logic bugs are always severe — unreachable code / dead branches indicate misunderstanding)
    - 1+ BUG-3 violations (concurrency bugs are always severe — data races are undefined behavior)
    - 1+ BUG-4 retain cycle or resource leak (memory leaks are always severe)
    - 2+ BUG-4 error handling gaps (systemic error swallowing)
---

## Quantitative Metrics Summary
| ID    | Metric                  | Threshold                                    | Severity  |
|-------|-------------------------|----------------------------------------------|-----------|
| BUG-0 | Exception               | Falls into exception category                | COMPLIANT |
| BUG-1 | Unsafe unwrap/access    | 0 violations                                 | COMPLIANT |
| BUG-2 | Logic/semantic          | 0 violations                                 | COMPLIANT |
| BUG-3 | Concurrency             | 0 violations                                 | COMPLIANT |
| BUG-4 | Safety/correctness      | 0 violations                                 | COMPLIANT |
| BUG-1 | Unsafe unwrap/access    | 1-2 force unwraps only, all else clean       | MINOR     |
| BUG-4 | Safety/correctness      | 1 minor correctness issue only               | MINOR     |
| BUG-1 | Unsafe unwrap/access    | 3+ violations                                | SEVERE    |
| BUG-2 | Logic/semantic          | 1+ unreachable/dead/contradictory            | SEVERE    |
| BUG-3 | Concurrency             | 1+ data race/deadlock/main-thread block      | SEVERE    |
| BUG-4 | Safety/correctness      | 1+ retain cycle/resource leak                | SEVERE    |
| BUG-4 | Safety/correctness      | 2+ error handling gaps                       | SEVERE    |
---
