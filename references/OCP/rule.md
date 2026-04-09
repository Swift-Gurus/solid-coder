---
name: ocp
displayName: Open/Closed Principle
category: solid
description: Sealed variation point counting and testability analysis with direct severity scoring
required_patterns:
  - structural/adapter
---

# Open/Closed Principle (OCP)

> "Software entities should be open for extension, but closed for modification." — Bertrand Meyer
---

## The OCP Metrics Framework

This framework provides objective scoring for OCP compliance. The primary
metrics are sealed variation point count and testability — both directly
observable from code.

## Metrics:

### OCP-1: Sealed Variation Points

Count the number of dependency/behavior points in the class that are hardcoded and NOT behind abstractions.

**Definition:** A "sealed variation point" is a place where adding a new behavior or swapping an implementation requires modifying this class instead of extending it.

**Detection:**

1. **List every dependency** the class uses (properties, parameters, method calls to external types)
2. **Classify each as** 
   - ABSTRACT (protocol-typed and injected) 
   - DIRECT (passed in construction methods or used directly in class) 
     - INJECTED (concrete class, singleton, static) passed into construction of the object (init, factory methods, convenience inits)
       - construction methods (init, create type factory methods, convenience methods) can have defatult arguments -> consider INJECTED
     - NON-INJECTED (concrete class, singleton, static, instantiated internally) used internally without injection
   - INDIRECT (concrete class, singleton, static passed indirectly by dependencies)
3. **Check exceptions** — exclude from count (see Exceptions section below)
4. **Count concrete dependencies DIRECT NON-INJECTED** that are NOT exceptions = sealed points from dependencies
5. **Sum** = total sealed variation points

**Result:** 
Count of DIRECT by category INJECTED, NON-INJECTED

| Type | Count | Example         |
|------|-------|-----------------|
| INJECTED | 1 | Networkmanager  |
| NON-INJECTED | 2 | Analytics.shared |

Count of INDIRECT

| INDIRECT | Count | Example |
|----------|-------|---------|

**Example: 🔥 Sealed Variation Points (Singleton References):**
```swift
// 🔥 Violation: 2 sealed DIRECT NON-INJECTED variation points → SEVERE
class UserDatabaseManager {
    func updateUserData(completion: @escaping ((Error?) -> Void)) {
        // Sealed point 1: NetworkManager.shared (singleton)
        NetworkManager.shared.fetchUserData { (user, error) in
            guard let user = user else {
                completion(error)
                return
            }
            // Sealed point 2: DatabaseRealmAdapter.shared (singleton)
            DatabaseRealmAdapter.shared.saveUser(user) { completion($0) }
        }
    }
}
```
**Analysis:**
- `NetworkManager.shared` → DIRECT NON-INJECTED (singleton) → 1 sealed point
- `DatabaseRealmAdapter.shared` → DIRECT NON-INJECTED (singleton) → 1 sealed point
- **Sealed variation points: 2 DIRECT NON-INJECTED** → SEVERE  from OCP-1 alone


### OCP-2: Testability

**Definition:** A class is OCP-compliant when it can be tested without modifying its source. Testability is a proxy for extensibility.

**Detection:**
- Use the analysis from OCP-1 to validate if CONCRETE has extension/testability points 
- For every DIRECT INJECTED AND INDIRECT dependency perform OCP-1 analysis. 
 - If the DIRECT INJECTED and INDIRECT is not compliant with OCP-1, and we cannot subclass it mark it - UNTESTABLE

*Note* we can subclass any class that is not final.

**Result:** Count CONCRETE UNTESTABLE.

| CONCRETE  | TYPE     | TESTABLE |
|-----------|----------|-----------|
| Networkmanager | DIRECT INJECTED   | YES       |
| Database      | DIRECT INJECTED   | NO        |
| Observer      | INDIRECT | NO        |


### Exceptions (0 points — NOT violations):
1. **Factories/Builders** creating objects — that's their job
2. **Helpers** — with no dependencies — Encoders, Formatters, Locks, Queues, Multithreading.
3. **Pure data structures** — no business logic, no dependencies, no side effects
4. **Boundary Adapters** - (see @adapter.md) - applies ONLY when wrapping truly static-only APIs.
5. **Pure Views UI elements** - UI elements that don't have any business logic dependencies.
6. **Test code** — unit tests, UI tests, integration tests, mocks, stubs, fakes, and test helpers are exempt. Test code intentionally uses concrete types and is not subject to OCP review.
    When encountering a `.shared` / `.default` / static access, **inspect the returned type** before deciding:

    | Returned type | Can instantiate / subclass? | Action | Boundary Adapter? |
    |---------------|---------------------------|--------|-------------------|
    | Concrete class (non-final) | Yes — can subclass | Protocol extension conformance + inject the instance | **No** |
    | Concrete final class | Yes — can instantiate | Protocol extension conformance + inject the instance | **No** |
    | Protocol / interface | Already abstract | Depend on the protocol directly | **No** |
    | Enum with static members only | No | Wrap in adapter struct | **Yes** |
    | Global function / constant | No | Wrap in adapter struct | **Yes** |

    Boundary Adapter Recognition Conditions (ALL must hold):
    - API is not owned by dev (search in project/local packages/local framework files)
    - API doesn't support instantiation: enums with only static members, global constants, static global functions
    - The type **cannot** be subclassed or instantiated — only then is a wrapper struct justified
      

### Severity Bands:
- ✅ **COMPLIANT** (0 sealed points, 0 untestable dependencies)
- ⚠️ **MINOR** (0 sealed points, 1-2 testable DIRECT dependencies)
- 🔥 **SEVERE** (1+ sealed points or 1+ untestable DIRECT or INDIRECT dependencies)
---

## Quantitative Metrics Summary
| ID    | Metric                  | Threshold                                         | Severity   |
|-------|-------------------------|---------------------------------------------------|------------|
| OCP-1 | Sealed variation points | 0 sealed points                                   | COMPLIANT  |
| OCP-2 | Testability score | 0 sealed points, 1-2 testable DIRECT INJECTED dependencies | MINOR      |
| OCP-1 | Sealed variation points | 1+ sealed non-injected points                     | SEVERE     |
| OCP-2 | Testability score       | 1+ untestable dependencies                        | SEVERE  |

---
