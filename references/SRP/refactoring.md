---
name: srp
displayName: Single Responsibility Principle
category: solid
description: Patterns, examples of conforming/refactoring for SRP  
---
# Single Responsibility Principle (SRP)

> A class should have only one reason to change. — Robert C. Martin
---

## SRP Refactoring Approaches

This framework provides examples of how to refactor SRP, for different severity 

---

## Refactoring Depth by Severity

### MINOR — No Action Required

When verb count is 3+ with 1 cohesion group and 1 stakeholder. No refactoring needed — keep an eye on it.

### SEVERE — Refactoring

When there are 2+ cohesion groups or multiple stakeholders.

#### Two-Phase Extract (2+ cohesion groups or multiple stakeholders)

#### Phase 1: Extract Methods (Clarity)

Split a monolithic method into smaller methods within the same class.

```swift
// BEFORE: Monolithic method
func processTrades(stream: InputStream) {
    // 100+ lines doing: read, parse, validate, store, log
}

// AFTER Phase 1: Delegated methods (still in same class)
func processTrades(stream: InputStream) {
    let lines = readTradeData(stream)
    let trades = parseTrades(lines)
    storeTrades(trades)
}

private func readTradeData(_ stream: InputStream) -> [String] { ... }
private func parseTrades(_ lines: [String]) -> [TradeRecord] { ... }
private func storeTrades(_ trades: [TradeRecord]) { ... }
```

**Phase 1 achieves:** Clarity and readability
**Phase 1 doesn't achieve:** True SRP — still must modify the class to change behavior

#### Phase 2: Extract Types with Protocols (Abstraction)

Extract each cohesion group into a separate class behind a protocol. The original class becomes an orchestrator.

```swift
// Protocols for each responsibility
protocol TradeDataProvider {
    func getTradeData() -> [String]
}

protocol TradeParser {
    func parse(_ data: [String]) -> [TradeRecord]
}

protocol TradeStorage {
    func persist(_ trades: [TradeRecord])
}

// Orchestrator: ONE responsibility — process coordination
final class TradeProcessor {
    private let dataProvider: TradeDataProvider
    private let parser: TradeParser
    private let storage: TradeStorage

    init(dataProvider: TradeDataProvider,
         parser: TradeParser,
         storage: TradeStorage) {
        self.dataProvider = dataProvider
        self.parser = parser
        self.storage = storage
    }

    func processTrades() {
        let lines = dataProvider.getTradeData()
        let trades = parser.parse(lines)
        storage.persist(trades)
    }
}

// Implementations (each with single responsibility)
final class StreamTradeDataProvider: TradeDataProvider { ... }
final class SimpleTradeParser: TradeParser { ... }
final class DatabaseTradeStorage: TradeStorage { ... }
```

**After Phase 2:**
- `TradeProcessor`: 1 verb (orchestrates), 1 group, 1 stakeholder (Architect)
- `StreamTradeDataProvider`: 1 verb (reads), 1 group, 1 stakeholder (DevOps)
- `SimpleTradeParser`: 1 verb (parses), 1 group, 1 stakeholder (Data team)
- `DatabaseTradeStorage`: 1 verb (persists), 1 group, 1 stakeholder (DBA)

---

## Extract by Cohesion Group

The most common SEVERE refactoring. Each disjoint variable group becomes its own type.

```swift
// BEFORE: 2 cohesion groups in one class
class PartialDownloadViewHelper {
    // Group 1: Container/UI
    private var containerFactory: ContainerProviding
    private var container: Container?

    // Group 2: Observation
    private var observationProvider: ObservationProviding
    private var observationTokens: [Any] = []

    // Group 1 methods
    func setupContainer(...) { container = containerFactory.create(...) }
    func updateContainer(...) { container?.update(...) }

    // Group 2 methods
    func startObservations(...) { observationProvider.kinds(...).forEach(observe) }
    func cancelObservations() { observationTokens = [] }

    // Bridging method (touches both groups)
    func modelDidChange(...) {
        cancelObservations()
        setupContainer(...)
        startObservations(...)
    }
}

// AFTER: Each group extracted, original becomes coordinator
protocol DownloadObserving {
    func startObservations(for model: Model, projectUid: ProjectUid)
    func cancelObservations()
}

final class DownloadObservationManager: DownloadObserving {
    private let observationProvider: ObservationProviding
    private var observationTokens: [Any] = []
    // ... startObservations, cancelObservations, startObserving moved here
}

class PartialDownloadViewHelper {
    private let observationManager: DownloadObserving  // injected
    private var containerFactory: ContainerProviding
    private var container: Container?

    // Bridging method now delegates
    func modelDidChange(...) {
        observationManager.cancelObservations()  // delegates
        setupContainer(...)                       // still owns
        observationManager.startObservations(...) // delegates
    }
}
```

**Key:** The bridging method stays in the original class. It becomes the coordinator.

---

## Design Patterns for SRP Fixes

### Strategy Pattern — Replace Switch Statements

```swift
// BEFORE: switch embeds multiple strategies
func checkout(paymentType: PaymentType, amount: Double) {
    switch paymentType {
    case .creditCard: chargeCreditCard(amount)
    case .paypal: chargePayPal(amount)
    case .applePay: chargeApplePay(amount)
    }
}

// AFTER: each strategy is its own type
protocol PaymentStrategy {
    func processPayment(amount: Double)
}

final class OnlineCart {
    private let strategies: [PaymentType: PaymentStrategy]
    func checkout(paymentType: PaymentType, amount: Double) throws  {
        guard let paymentStrategy = strategies[paymentType] else {
           throw Error.DoesNotSupportPayment(paymentType)
        }
        paymentStrategy.processPayment(amount: amount)
    }
}
```

### Decorator Pattern — Cross-Cutting Concerns

```swift
// BEFORE: logging mixed into business logic
class Service {
    func execute() {
        logger.log("Starting")  // cross-cutting
        // business logic
        logger.log("Finished")  // cross-cutting
    }
}

// AFTER: decorator wraps the concern
protocol Executing { func execute() }

final class CoreService: Executing {
    func execute() { /* business logic only */ }
}

final class LoggingDecorator: Executing {
    private let wrapped: Executing
    func execute() {
        logger.log("Starting")
        wrapped.execute()
        logger.log("Finished")
    }
}
```

### Adapter Pattern — Third-Party Dependencies

```swift
// BEFORE: direct dependency on third-party type
class Analytics {
    private let firebase = FirebaseAnalytics()  // concrete third-party
    func track(_ event: String) { firebase.logEvent(event) }
}

// AFTER: protocol isolates the dependency
protocol AnalyticsTracking {
    func track(_ event: String)
}

final class FirebaseAdapter: AnalyticsTracking {
    let fbAnalytics = FirebaseAnalytics()
    func track(_ event: String) { fbAnalytics.logEvent(event) }
}
```

---


