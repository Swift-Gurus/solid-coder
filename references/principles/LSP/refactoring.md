---
name: lsp
displayName: Liskov Substitution Principle
category: solid
description: Patterns, examples of conforming/refactoring for LSP
---
# Liskov Substitution Principle (LSP)

> If S is a subtype of T, then objects of type T may be replaced with objects of type S, without breaking the program. — Barbara Liskov (1987)
---

## LSP Refactoring Approaches

This framework provides examples of how to refactor LSP violations, matched to the type of violation found.

---

## Refactoring Depth by Severity

### COMPLIANT — No Action Required

0 net type checks, 0 contract violations, 0 empty/fatal error methods. Subtypes are fully substitutable.

### MINOR — Watch Item

<50% empty (non-fatal error) methods. No refactoring needed — consider splitting the interface.

### SEVERE — Full Refactoring

1+ net type checks OR 1+ contract violations OR 1+ fatalError methods OR >=50% empty methods. Protocol extraction, hierarchy redesign, interface splitting, or contract correction required.

---

## Refactoring by Violation Type

### 1. Protocol Extraction + Generic Constraints — Replace Type Checking (LSP-1)

The most common SEVERE refactoring. Each `as?`/`is` type check becomes a protocol method call.

```swift
// BEFORE: Type checking with concrete types (3 type checks)
final class StorageImpl: Storage {
   let database: Database
   func saveItem(_ item: StorageItem) {
      if let user = item as? User {
             let json = // create json from user
             let record == Record(user.id, attributes: json)
             try database.save(record)
         } else if let product = item as? Product {
              let json = // create json from product
              let record == Record(product.id, attributes: json)
             try database.save(record)
         } else if let order = item as? Order {
             let json = // create json from order
             let record == Record(order.id, attributes: json)
             try database.save(record)
         }
   }
}

// AFTER: Protocol + generic constraint (0 type checks)
protocol Identifiable {
   var id: String { }
}

protocol RecordRepresentable: Identifiable, Encodable {

}

protocol Storage {
    func saveItem<T: RecordRepresentable>(_ item: T)
}

final class StorageImpl: Storage {
   let database: Database
   func saveItem<T: RecordRepresentable>(_ item: T) {
      let data = try JSONEncoder().encode(item)
      let json = try JSONSerialization.jsonObject(data) as? [String: Any] ?? [:]
      let record = Record(item.id, attributes: json)
      try database.save(record)
   }
}

```

### 2. Contract Update — Fix Strengthened Preconditions (LSP-2)

When a subtype adds guard clauses the base doesn't have.

**Option A: Update base contract** (if all implementations need the constraint):
```swift
// BEFORE: Base accepts nil, subtype rejects nil
class ShippingStrategy {
    func calculateCost(weight: Float, destination: Region?) throws -> Decimal {
        guard weight > 0 else { throw ShippingError.invalidWeight }
        return baseCost
    }
}

// AFTER: Base requires non-optional destination
class ShippingStrategy {
    func calculateCost(weight: Float, destination: Region) throws -> Decimal {
        guard weight > 0 else { throw ShippingError.invalidWeight }
        return baseCost
    }
}
```

**Option B: Handle in subtype** (honor the base contract):
```swift
// AFTER: Subtype handles nil instead of rejecting it
class WorldWideShipping: ShippingStrategy {
    override func calculateCost(weight: Float, destination: Region?) throws -> Decimal {
        guard weight > 0 else { throw ShippingError.invalidWeight }
        let region = destination ?? .unknown  // Handle nil, don't reject
        return internationalCost(to: region)
    }
}
```

### 3. Postcondition Restoration — Fix Weakened Guarantees (LSP-2)

When a subtype removes assertions or relaxes return value constraints.

**Option A: Honor base guarantee**:
```swift
// BEFORE: Base guarantees cost > 0, subtype returns 0
class FreeShipping: ShippingStrategy {
    override func calculateCost(weight: Float, destination: Region?) throws -> Decimal {
        return 0  // Violates cost > 0 postcondition
    }
}

// AFTER: Return minimum positive value
class FreeShipping: ShippingStrategy {
    override func calculateCost(weight: Float, destination: Region?) throws -> Decimal {
        return 0.01  // Honors postcondition
    }
}
```

**Option B: Update base contract** (if zero is valid):
```swift
// AFTER: Base allows cost >= 0
class ShippingStrategy {
    func calculateCost(weight: Float, destination: Region?) throws -> Decimal {
        let cost = performCalculation(weight, destination)
        guard cost >= 0 else {  // Updated: allows zero
            throw ShippingError.invalidResult("Cost cannot be negative")
        }
        return cost
    }
}
```

### 4. Validated Setters — Fix Broken Invariants (LSP-2)

When a subtype exposes protected state without validation.

```swift
// BEFORE: Subtype bypasses invariant validation
class ExpressShipping: ShippingStrategy {
    override var flatRate: Decimal {
        get { super.flatRate }
        set { _flatRate = newValue }  // No validation — can set negative!
    }
}

// AFTER: Route through validated setter
class ExpressShipping: ShippingStrategy {
    func updateFlatRate(_ newRate: Decimal) throws {
        try setFlatRate(newRate)  // Uses base validation
    }
}
```

### 5. Interface Redesign — Fix Empty Methods / Refused Bequest (LSP-3)

When a conformer has empty method stubs or throws `fatalError("NotImplemented")`. The interface is too broad — split it so conformers only implement what they support.

```swift
// BEFORE: Conformer has empty methods (2/3 empty = 66% → SEVERE)
protocol Logger {
    func sendAnalytics(_ name: String)
    func log(_ name: String)
    func sendCrash(_ name: String)
}

final class MyLogger: Logger {
    func sendAnalytics(_ name: String) { /* real logic */ }
    func log(_ name: String) {}          // empty — doesn't log
    func sendCrash(_ name: String) {}    // empty — doesn't send crashes
}

// AFTER: Split interface via protocol composition
protocol AnalyticsSending {
    func sendAnalytics(_ name: String)
}

protocol Logging {
    func log(_ name: String)
}

protocol CrashReporting {
    func sendCrash(_ name: String)
}

// MyLogger only conforms to what it actually implements
final class MyLogger: AnalyticsSending {
    func sendAnalytics(_ name: String) { /* real logic */ }
}
```

```swift
// BEFORE: Conformer throws fatalError (refused bequest → SEVERE)
protocol Stack {
    func push(_ item: Int)
    func pop() -> Int
    var isEmpty: Bool { get }
}

class ReadOnlyStack: Stack {
    func push(_ item: Int) {
        fatalError("Not supported")  // Refused bequest
    }
    func pop() -> Int { items.removeLast() }
    var isEmpty: Bool { items.isEmpty }
}

// AFTER: Split interface via protocol composition
protocol Poppable {
    func pop() -> Int
    var isEmpty: Bool { get }
}

protocol Pushable {
    func push(_ item: Int)
}

typealias Stack = Poppable & Pushable

// ReadOnlyStack only conforms to what it supports
class ReadOnlyStack: Poppable {
    func pop() -> Int { items.removeLast() }
    var isEmpty: Bool { items.isEmpty }
}
```

### 6. Error Hierarchy Unification — Fix Orphan Exceptions

When a subtype throws errors outside the base error hierarchy.

```swift
// BEFORE: CachedRepository throws CacheError (orphan)
enum CacheError: Error {
    case expired
}

class CachedRepository: Repository {
    func findById(_ id: UUID) throws -> Entity {
        if cacheExpired { throw CacheError.expired }  // Not in RepositoryError
        return cached
    }
}

// AFTER: Add to base error hierarchy
enum RepositoryError: Error {
    case notFound(id: UUID)
    case saveFailed
    case cacheExpired  // Part of hierarchy now
}

class CachedRepository: Repository {
    func findById(_ id: UUID) throws -> Entity {
        if cacheExpired { throw RepositoryError.cacheExpired }  // Same hierarchy
        return cached
    }
}
```
