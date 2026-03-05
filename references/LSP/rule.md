---
name: lsp
displayName: Liskov Substitution Principle
category: solid
description: Type check counting and contract compliance analysis with direct severity scoring
---

# Liskov Substitution Principle (LSP)

> If S is a subtype of T, then objects of type T may be replaced with objects of type S, without breaking the program. — Barbara Liskov (1987)
---

## The LSP Metrics Framework

This framework provides objective scoring for LSP compliance. The primary
metrics are type check count and contract compliance — both directly
observable from code.

## Metrics:

### LSP-1: Type Check/Typecast Count

Count runtime type checks (`is`, `as?`, `as!`, `type(of:)`) against concrete types in client code that uses a base type or protocol.

**Definition:** 
- A "type check" is a place where client code inspects the concrete type/interfaces/protocols behind an abstraction. Each type check means the client knows about subtypes — the wrong abstraction was picked.
    
**Detection:**

1. **Count typechecks** — `is`, `as?`, `as!`, `type(of:)` used with concrete types, protocols, interfaces
2. **Count out exceptions**
   - see typecast-lsp-exception.swift in Examples
   - identify the source of typecasted object
   - search in project/local packages/local framework files
   - if not found -> external -> exception
   - if found -> developer-owned -> violation
3. **Total Count** = total type checks minus exceptions

**Result:**

| Category              | Count | Class/Interface                               |
|-----------------------|-------|-----------------------------------------------|
| Type checks  | ___ | `to class User`, to protocol Encodable        |
| Type checks exceptions | ___ | to [String: Any], forced by JSONSerialization |
| Net type checks       | ___ | (total - exceptions)                          |

**Example: SEVERE Type Checking (Wrong Abstraction):**
```swift
// SEVERE Violation: 3 type checks → client knows about subtypes
final class StorageImpl: Storage {
   let database: Database
   func saveItem(_ item: StorageItem) {
      if let user = item as? User {
             let json = // create json from user
             let record = Record(user.id, attributes: json)
             try database.save(record)
         } else if let product = item as? Product {
              let json = // create json from product
              let record = Record(product.id, attributes: json)
             try database.save(record)
         } else if let order = item as? Order {
             let json = // create json from order
             let record = Record(order.id, attributes: json)
             try database.save(record)
         }
   }
}
```
**Analysis:**
- `item as? User` → concrete type check → 1 type check
- `item as? Product` → concrete type check → 1 type check
- `item as? Order` → concrete type check → 1 type check
- **Net type checks: 3** → SEVERE


### LSP-2: Contract Compliance (Inheritance Only)

**Definition:** When a class inherits from another class and overrides methods, the subtype must honor the base contract: same or weaker preconditions, same or stronger postconditions, preserved invariants.

**Trigger:** This metric only applies when `override` methods are detected in class inheritance. For protocol conformance without class inheritance, LSP-2 does not apply.

**Detection:**

1. **Detect inheritance** — does the class inherit from a concrete base class (not just protocol conformance)?
2. **If yes** — read the base class source code
3. **For each `override` method, compare base vs subtype:**

   **a. Precondition Changes** — new guard clauses in subtype not present in base

   | Method | Base Guards | Subtype Guards | New Guards |
   |--------|------------|----------------|------------|
   |        |            |                |            |

   **b. Postcondition Weakening** — assertions/guarantees removed or relaxed in subtype

   | Method | Base Assertions | Subtype Assertions | Weakened |
   |--------|----------------|-------------------|----------|
   |        |                |                   |          |

   **c. Invariant Violations** — protected/private state exposed with public setters, or validated state bypass

   | Property | Base Access | Subtype Access | Violation |
   |----------|------------|----------------|-----------|
   |          |            |                |           |

4. **Count** = total contract violations (new guards + weakened postconditions + invariant violations)

*Note*: If the base class source is not available for reading, flag as "unable to verify" rather than assuming compliant.

**Result:**

| Violation Type | Count | Example |
|---------------|-------|---------|
| Strengthened preconditions | ___ | New guard clause in override |
| Weakened postconditions | ___ | Removed assertion in override |
| Broken invariants | ___ | Exposed private(set) property |
| Total contract violations | ___ | |

**Example: SEVERE Contract Violation (Strengthened Precondition):**
```swift
// Base accepts destination as optional
class ShippingStrategy {
    func calculateCost(weight: Float, destination: Region?) throws -> Decimal {
        guard weight > 0 else { throw ShippingError.invalidWeight }
        return baseCost  // destination can be nil
    }
}

// SEVERE Violation: subtype adds NEW guard (strengthens precondition)
class WorldWideShipping: ShippingStrategy {
    override func calculateCost(weight: Float, destination: Region?) throws -> Decimal {
        guard weight > 0 else { throw ShippingError.invalidWeight }     // Same guard
        guard let destination = destination else {                       // NEW guard — violation!
            throw ShippingError.destinationRequired
        }
        }
        return internationalCost(to: destination)
    }
}
```
**Analysis:**
- Base has 1 guard (`weight > 0`), subtype has 2 guards
- New guard: `destination != nil` — strengthened precondition
- **Contract violations: 1** → SEVERE


### LSP-3: Empty/non-implemented methods

**Definition:** 
- When an object conforms to an interface/protocol and have methods non-implemented or crashing, this breaks the contract
- Empty methods or vars. Meaning non implemented methods or var from the contract
- Methods/vars whose entire body is a crash assertion — the method exists only to satisfy protocol conformance, not to provide real behavior.
  - fatalError, preconditionFailure, assertionFailure, fatalError("not implemented"), fatalError("abstract method"), fatalError("invalid state")

**Detection:**
1. **Count total methods/vars in the interface**
2. **Count empty methods/vars** 
3. **Count methods with fatal-error(or any conditions that cause crash)**
4. **Calculate percentage of empty** - empty(non-fatal methods) methods/vars / total methods/vars

| Category                        | Value |
|---------------------------------|-------|
| Empty methods/vars              | ___   |
| Fatal error methods             | ___   |
| Total methods/vars in interface | ___   |
| Empty methods/vars percentage   | ___   |


```swift
// SEVERE Violation: >50% empty(non fatal-error) methods

protocol Logger {
   func sendAnalytics(_ name: String)
   func log(_ name: String)
   func sendCrash(_ name: String)
}

final class MyLogger: Logger {
   func sendAnalytics(_ name: String) { 
    //logic for sending analytics 
   }
   func log(_ name: String) {}
   func sendCrash(_ name: String) {}
}

```

```swift
// Compliant

protocol Logger {
   func sendAnalytics(_ name: String)
   func log(_ name: String)
   func sendCrash(_ name: String)
}

final class NoOp: Logger {
   func sendAnalytics(_ name: String) {}
   func log(_ name: String) {}
   func sendCrash(_ name: String) {}
}

```

### Exceptions (NOT violations):
1. **NoOp objects** — objects that provide no-op default behaviour (turn-off for testing, or when not initialized)
   - consider NoOps object if the name states it and 100% of methods/var from the contract are empty, or resolved to default values

### Severity Bands:
- COMPLIANT (0 net type checks, 0 contract violations, 0 empty/fatal error methods)
- MINOR (<50% empty(non-fatal error) methods)
- SEVERE (1+ net type checks OR 1+ contract violations or 1+ fatalError methods or empty methods (non fatal methods) >= 50%)
---

## Quantitative Metrics Summary
| ID    | Metric              | Threshold                                | Severity   |
|-------|---------------------|------------------------------------------|------------|
| LSP-1 | Type check count    | 0 net type checks                        | COMPLIANT  |
| LSP-3 | Empty Methods       | 0 empty or fatal error methods           | COMPLIANT  |
| LSP-2 | Contract compliance | 0 contract violations                    | COMPLIANT     |
| LSP-3 | Empty Methods       | empty methods (non fatal methods) < 50%  | MINOR      |
| LSP-1 | Type check count    | 1+ net type checks                       | SEVERE     |
| LSP-2 | Contract compliance | 1+ contract violations                   | SEVERE     |
| LSP-3 | Fatal error methods | 1+ with fatal error/crash                | SEVERE     |
| LSP-3 | Empty Methods       | empty methods (non fatal methods) >= 50% | SEVERE     |
---