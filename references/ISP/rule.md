---
name: isp
displayName: Interface Segregation Principle
category: solid
description: Protocol width analysis and conformer coverage scoring with direct severity scoring
---

# Interface Segregation Principle (ISP)

> No client should be forced to depend on methods it does not use. — Robert C. Martin
---

## The ISP Metrics Framework

This framework provides objective scoring for ISP compliance. The primary
metrics are protocol method count and conformer coverage — both directly
observable from code.

## Metrics:

### ISP-1: Protocol Width (Method Count)

Count the number of methods/properties declared in a protocol.

**Definition:** A "wide" protocol forces conformers to implement methods they do not need. Each unnecessary method is a coupling point that creates implementation burden and fragility.

**Detection:**

1. **List every method and property** declared in the protocol (including associated types)
2. **Count total requirements** (methods + properties + associated types)
3. **Exclude inherited requirements** — only count what THIS protocol declares, not parent protocols

**Result:**

| Category              | Count |
|-----------------------|-------|
| Methods               | ___   |
| Properties            | ___   |
| Associated types      | ___   |
| Total requirements    | ___   |

**Example: SEVERE Wide Protocol:**
```swift
// SEVERE Violation: 8 requirements, 3 cohesion groups
protocol DataManaging {
    // Group 1: Read
    func fetch(id: String) -> Data
    func fetchAll() -> [Data]
    func search(query: String) -> [Data]
    // Group 2: Write
    func save(_ data: Data)
    func delete(id: String)
    func update(id: String, data: Data)
    // Group 3: Export
    func export(_ data: Data, format: ExportFormat) -> String
    func exportAll(format: ExportFormat) -> String
}

// Conformer only needs read operations but must implement everything
final class ReadOnlyCache: DataManaging {
    func fetch(id: String) -> Data { /* real */ }
    func fetchAll() -> [Data] { /* real */ }
    func search(query: String) -> [Data] { /* real */ }
    func save(_ data: Data) { }              // empty — doesn't write
    func delete(id: String) { }              // empty — doesn't write
    func update(id: String, data: Data) { }  // empty — doesn't write
    func export(_ data: Data, format: ExportFormat) -> String { "" }  // stub
    func exportAll(format: ExportFormat) -> String { "" }             // stub
}
```
**Analysis:**
- Protocol has 8 requirements, 3 cohesion groups (read, write, export)
- ReadOnlyCache only meaningfully implements 3 of 8 (37.5% coverage)
- 5 empty/stub methods → forced implementations

### ISP-2: Conformer Coverage (Implementation Ratio)

For each conformer of a protocol, measure what percentage of protocol methods have meaningful (non-empty, non-stub) implementations.

**Definition:** A conformer with low coverage is being forced to depend on methods it does not use. This is the direct ISP violation signal.

**Detection:**

1. **Find all conformers** of the protocol in the project
2. **For each conformer, classify each required method/property as:**
   - MEANINGFUL — contains real logic (more than a single return statement with a default value)
   - EMPTY — empty body `{}`
   - STUB — returns a hardcoded default, throws `fatalError`, or has a trivial passthrough that ignores the intent
   - DELEGATED — forwards to another object (still counts as meaningful)
3. **Calculate coverage** = meaningful / total requirements

**Result (per conformer):**

| Conformer        | Total Req | Meaningful | Empty | Stub | Coverage |
|------------------|-----------|------------|-------|------|----------|
|                  |           |            |       |      |          |

**Example: Mixed Coverage Across Conformers:**
```swift
protocol Worker {
    func prepare()
    func execute()
    func cleanup()
    func report() -> String
}

// Full coverage — all methods meaningful
final class DatabaseWorker: Worker {
    func prepare() { openConnection() }
    func execute() { runQueries() }
    func cleanup() { closeConnection() }
    func report() -> String { return queryLog }
}

// Low coverage — forced to implement unused methods
final class FireAndForgetWorker: Worker {
    func prepare() { /* nothing needed */ }
    func execute() { sendRequest() }
    func cleanup() { /* nothing needed */ }
    func report() -> String { return "" /* never reports */ }
}
```
**Analysis:**
- DatabaseWorker: 4/4 meaningful = 100% coverage
- FireAndForgetWorker: 1/4 meaningful = 25% coverage
- Protocol is too wide for FireAndForgetWorker

### ISP-3: Cohesion Groups Within Protocol

Group protocol methods by which conformers actually use them together. Disjoint groups suggest the protocol should be split.

**Detection:**

1. **Build a usage matrix**: for each conformer, which methods are MEANINGFUL
2. **Identify groups of methods** that are always used together across conformers
3. **Count groups** — if methods cluster into 2+ disjoint usage groups, the protocol mixes responsibilities

**Result:**

| Group | Methods | Used By Conformers |
|-------|---------|-------------------|
|       |         |                   |

### Exceptions (NOT violations):
1. **Non-protocol units** — ISP applies ONLY to protocol/interface declarations. Classes, structs, enums, and extensions that do not declare a protocol are outside ISP scope — mark as COMPLIANT, do not analyze. Conformers are examined only as evidence during ISP-2 (coverage analysis) of the protocol they conform to, not as ISP review targets themselves.
2. **Marker protocols** — protocols with zero requirements used for type discrimination (e.g., `Sendable`, `Identifiable`). Width = 0 is always COMPLIANT.
3. **Single-conformer protocols** — if only one conformer exists in the project, coverage is trivially 100%. Not a violation, but flag as "unable to verify ISP — single conformer." The protocol may still be too wide, but there is no evidence from usage.
4. **Composition protocols** — protocols defined as `protocol P: A, B {}` (or `typealias P = A & B`) where A and B are already narrow. The composition itself is not a violation if each component protocol is compliant. **Prefer `protocol P: A, B {}` over `typealias`** — a typealias cannot be conformed to directly (you cannot write `class Decorator: MyTypealias`), which breaks the decorator pattern and other composition patterns that need a single nominal type to conform to.
5. **@objc protocols** — Objective-C interop protocols may require specific method sets dictated by the framework. Flag as "framework-constrained" rather than violation.
6. **Protocols with default implementations** — if all non-meaningful methods have default implementations via protocol extensions, conformers are not forced to implement them. Check whether the conformer overrides the default — if not, the default satisfies ISP.

### Severity Bands:
- COMPLIANT (protocol width <= 5 AND minimum conformer coverage >= 80%)
- MINOR (any of the following, provided no SEVERE trigger):
    - Protocol width 6-8 AND minimum conformer coverage >= 60%
    - Protocol width <= 5 AND minimum conformer coverage 60-79%
- SEVERE (any of the following):
    - Protocol width > 8
    - Any conformer coverage < 60%
    - 2+ cohesion groups within protocol methods
    - 1+ conformers with 3+ empty/stub methods
---

## Quantitative Metrics Summary
| ID    | Metric              | Threshold                                        | Severity   |
|-------|---------------------|--------------------------------------------------|------------|
| ISP-0 | Exception           | Falls into exception category                    | COMPLIANT  |
| ISP-1 | Protocol width      | <= 5 methods, all conformers >= 80%              | COMPLIANT  |
| ISP-2 | Conformer coverage  | All conformers >= 80%, width <= 5                | COMPLIANT  |
| ISP-1 | Protocol width      | 6-8 methods, all conformers >= 60%               | MINOR      |
| ISP-2 | Conformer coverage  | Width <= 5, any conformer 60-79%                 | MINOR      |
| ISP-1 | Protocol width      | > 8 methods                                      | SEVERE     |
| ISP-2 | Conformer coverage  | Any conformer < 60% meaningful                   | SEVERE     |
| ISP-3 | Protocol cohesion   | 2+ disjoint usage groups                         | SEVERE     |
---
