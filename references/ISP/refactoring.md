---
name: isp
displayName: Interface Segregation Principle
category: solid
description: Patterns, examples of conforming/refactoring for ISP
---
# Interface Segregation Principle (ISP)

> No client should be forced to depend on methods it does not use. — Robert C. Martin
---

## ISP Refactoring Approaches

This framework provides examples of how to refactor ISP violations, for different severity levels.

---

## Refactoring Depth by Severity

### MINOR — No Action Required

When protocol width is 6-8 with all conformers at >= 60% coverage. No splitting needed — keep an eye on it. Consider adding documentation about intended usage.

### SEVERE — Refactoring

When protocol width > 8, any conformer coverage < 60%, or 2+ cohesion groups detected.

#### Protocol Split by Cohesion Group

The most common SEVERE refactoring. Each disjoint usage group becomes its own protocol.

```swift
// BEFORE: Wide protocol with 2 cohesion groups
protocol DataManaging {
    // Group 1: Read operations
    func fetch(id: String) -> Data
    func fetchAll() -> [Data]
    func search(query: String) -> [Data]

    // Group 2: Write operations
    func save(_ data: Data)
    func delete(id: String)
    func update(id: String, data: Data)

    // Group 3: Export operations
    func export(_ data: Data, format: ExportFormat) -> String
    func exportAll(format: ExportFormat) -> String
}

// ReadOnlyCache only needs Group 1
final class ReadOnlyCache: DataManaging {
    func fetch(id: String) -> Data { /* real */ }
    func fetchAll() -> [Data] { /* real */ }
    func search(query: String) -> [Data] { /* real */ }
    func save(_ data: Data) { }              // empty — forced
    func delete(id: String) { }              // empty — forced
    func update(id: String, data: Data) { }  // empty — forced
    func export(_ data: Data, format: ExportFormat) -> String { "" }  // stub
    func exportAll(format: ExportFormat) -> String { "" }             // stub
}

// AFTER: Split into role-specific protocols
protocol DataReading {
    func fetch(id: String) -> Data
    func fetchAll() -> [Data]
    func search(query: String) -> [Data]
}

protocol DataWriting {
    func save(_ data: Data)
    func delete(id: String)
    func update(id: String, data: Data)
}

protocol DataExporting {
    func export(_ data: Data, format: ExportFormat) -> String
    func exportAll(format: ExportFormat) -> String
}

// Composition protocol preserves backward compatibility
// Use protocol (not typealias) so decorators/wrappers can conform to the combined type
protocol DataManaging: DataReading, DataWriting, DataExporting {}

// ReadOnlyCache now only conforms to what it uses
final class ReadOnlyCache: DataReading {
    func fetch(id: String) -> Data { /* real */ }
    func fetchAll() -> [Data] { /* real */ }
    func search(query: String) -> [Data] { /* real */ }
}

// Full implementation conforms to all
final class DatabaseManager: DataManaging {
    func fetch(id: String) -> Data { /* real */ }
    func fetchAll() -> [Data] { /* real */ }
    func search(query: String) -> [Data] { /* real */ }
    func save(_ data: Data) { /* real */ }
    func delete(id: String) { /* real */ }
    func update(id: String, data: Data) { /* real */ }
    func export(_ data: Data, format: ExportFormat) -> String { /* real */ }
    func exportAll(format: ExportFormat) -> String { /* real */ }
}
```

**After Split:**
- `DataReading`: 3 methods, ReadOnlyCache 100% coverage
- `DataWriting`: 3 methods, DatabaseManager 100% coverage
- `DataExporting`: 2 methods, DatabaseManager 100% coverage
- `DataManaging` composition protocol: backward-compatible for consumers that need everything, and conformable for decorators/wrappers

---

#### Role Interface Pattern

When conformers serve different roles, define protocols by consumer role rather than by data grouping.

```swift
// BEFORE: One protocol, two distinct consumer roles
protocol UserService {
    func getUser(id: String) -> User
    func updateProfile(id: String, profile: Profile)
    func authenticate(credentials: Credentials) -> Token
    func revokeToken(_ token: Token)
    func listPermissions(userId: String) -> [Permission]
}

// ProfileViewController only uses profile methods
// AuthenticationManager only uses auth methods

// AFTER: Role-based interfaces
protocol UserProfileProviding {
    func getUser(id: String) -> User
    func updateProfile(id: String, profile: Profile)
}

protocol UserAuthenticating {
    func authenticate(credentials: Credentials) -> Token
    func revokeToken(_ token: Token)
}

protocol UserPermissionChecking {
    func listPermissions(userId: String) -> [Permission]
}

// Consumers depend only on the role they need
final class ProfileViewController {
    private let userService: UserProfileProviding  // narrow dependency
    // ...
}

final class AuthenticationManager {
    private let authService: UserAuthenticating  // narrow dependency
    // ...
}
```

**Key:** Name protocols by what the consumer NEEDS, not by what the provider IS.

---

#### Default Implementation via Protocol Extension

When a protocol is mostly used in full but 1-2 methods are optional for some conformers, provide defaults instead of splitting.

```swift
// BEFORE: Most conformers implement all, but some don't need report()
protocol Worker {
    func prepare()
    func execute()
    func cleanup()
    func report() -> String
}

// AFTER: Default for optional method
protocol Worker {
    func prepare()
    func execute()
    func cleanup()
    func report() -> String
}

extension Worker {
    func report() -> String { return "" }  // sensible default
}

// FireAndForgetWorker no longer forced to stub report()
final class FireAndForgetWorker: Worker {
    func prepare() { /* real */ }
    func execute() { sendRequest() }
    func cleanup() { /* real */ }
    // report() uses default — no empty stub needed
}
```

**When to use defaults vs splitting:**
- Default: 1-2 methods are optional, most conformers implement everything
- Split: Clear cohesion groups, conformers cluster into distinct usage patterns

---

## Design Patterns for ISP Fixes

### Composition over Inheritance

```swift
// BEFORE: Fat interface inherited by all
protocol Animal {
    func eat()
    func sleep()
    func fly()
    func swim()
    func run()
}

// Penguins can't fly, eagles can't swim — forced empty implementations

// AFTER: Capability-based composition
protocol Eating { func eat() }
protocol Sleeping { func sleep() }
protocol Flying { func fly() }
protocol Swimming { func swim() }
protocol Running { func run() }

final class Eagle: Eating, Sleeping, Flying, Running {
    func eat() { /* real */ }
    func sleep() { /* real */ }
    func fly() { /* real */ }
    func run() { /* real */ }
}

final class Penguin: Eating, Sleeping, Swimming, Running {
    func eat() { /* real */ }
    func sleep() { /* real */ }
    func swim() { /* real */ }
    func run() { /* real */ }
}
```

### Consumer-Side Protocol Narrowing

When you cannot modify the protocol (third-party or shared module), narrow at the consumer side.

```swift
// Can't modify ThirdPartyService protocol (7 methods)
// But our ViewModel only needs 2 methods

protocol DataFetching {
    func fetch(id: String) -> Data
    func fetchAll() -> [Data]
}

// Extension conformance — no wrapper needed
extension ThirdPartyServiceImpl: DataFetching {
    // Already has these methods — conformance is free
}

// ViewModel depends on narrow protocol
final class ViewModel {
    private let fetcher: DataFetching  // only sees 2 methods
}
```

---
