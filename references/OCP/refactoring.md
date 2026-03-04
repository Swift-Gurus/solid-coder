---
name: ocp
displayName: Open/Closed Principle
category: solid
description: Patterns, examples of conforming/refactoring for OCP
---
# Open/Closed Principle (OCP)

> "Software entities should be open for extension, but closed for modification." — Bertrand Meyer
---

## OCP Refactoring Approaches

This framework provides examples of how to refactor OCP violations, matched to the type of sealed variation point found.

---

## Refactoring Depth by Severity

### COMPLIANT — No Action Required

0 sealed points, 0 untestable concrete dependencies. Code is already open for extension.

### MINOR — Light Touch

0 sealed points, 1-2 testable concrete injected dependencies. Consider introducing protocols for concrete dependencies.

### SEVERE — Full Refactoring

1+ sealed points or 1+ untestable concrete dependencies. Full protocol extraction + dependency injection + removal of singletons/switches.

---

## Refactoring by Sealed Point Type

### 1. Dependency Injection — Replace Singletons/Static References

The most common SEVERE refactoring. Each `.shared`/`.default`/`static` reference becomes an injected protocol.
We need to create or find existed interface that includes definition of the called functionality.

```swift
// BEFORE: Singleton and Static API references (2 sealed points)
class UserDatabaseManager {
    func updateUserData() async throws {
         let user = try await NetworkManager.shared.fetchUserData()
         try await  DatabaseRealmAdapter.saveUser(user)
        }
        
    }
}

// AFTER: Protocol + Dependency Injection (0 sealed points)
protocol NetworkFetching {
    func fetchUserData() async throws
}

extension NetworkManager: NetworkFetching {}

protocol UserPersisting {
    func saveUser(_ user: User) async throws
}

// if the object is owned by the developer, switch static to instance.
final class DatabaseRealmAdapter: UserPersisting {
   // switched function from static to instance
   func saveUser(_ user: User) async throws {
      
   }
}

// if not owned by a developer an adapter or bridge can be used

struct DatabaseRealmAdapterWrapper: UserPersisting {
  func saveUser(_ user: User) async throws {
    try await DatabaseRealmAdapter.saveUser(user)
  }
}

final class UserDatabaseManager {
    private let network: NetworkFetching
    private let database: UserPersisting

    init(network: NetworkFetching, database: UserPersisting) {
        self.network = network
        self.database = database
    }

    func updateUserData() async throws  {
        let user = try await network.fetchUserData()
        try await  database.saveUser(user)
    }
}

// call site  UserDatabaseManager(network: NetworkManager.shared, database: DatabaseRealmAdapter()) or 
// call site  UserDatabaseManager(network: NetworkManager.shared, database: DatabaseRealmAdapterWrapper()) 
```

### 2. Strategy Pattern — Replace Switch/If-Else on Types

Each case in a switch becomes a separate conforming type behind a protocol.

```swift
// BEFORE: Switch on type (3 sealed points from 3 cases)
class PaymentProcessor {
    func processPayment(amount: Double, type: PaymentType) async throws  {
        switch type {
        case .creditCard:
            try await CreditCardPayment(amont: amount).proccess
        case .paypal:
            let process = PaypalPayment().createProccess()
            Task { proccess.acceptPayment(amount) }
        case .bitcoin:
            let bitcoinAddressGenerator = BitcoinAddressGenerator()
            let address = BitcoinAddressGenerator().address
            try await BitcoinSystem().waitForConfirmation(address, amount)
        }
    }
}

// AFTER: Strategy pattern (0 sealed points)
protocol PaymentMethod {
    func process(amount: Double) -> async throws
}

protocol PaymentProcessor {
    func processPayment(amount: Double, type: PaymentType) async throws 
}

final class PaymentProcessorStrategy: PaymentProcessor {
    private let paymentMethods: [PaymentType: PaymentMethod]
    private let alwaysThrowError: PaymentMethod
    init(paymentMethods: [PaymentType: PaymentMethod], alwaysThrowError: PaymentMethod) {
        self.paymentMethod = paymentMethod
        self.alwaysThrowError = alwaysThrowError
    }

    func processPayment(amount: Double, type: PaymentType) async throws  {
       let method =  paymentMethods[type] ?? alwaysThrowError
       try await method.proccess(amount: amount)
    }

}

// Each payment type is an independent extension
final class CreditCardPayment: PaymentMethod {
    func process(amount: Double) -> async throws { ... }
}

final class PayPalPayment: PaymentMethod {
    func process(amount: Double) -> async throws { ... }
}

// Adding Apple Pay = new class, ZERO modification to PaymentProcessor
final class ApplePayPayment: PaymentMethod {
    func process(amount: Double) -> async throws { ... }
}

// Factory to construct PaymentProcessor
final class PaymentProccessorFactory() {
    var proccessor: PaymentProcessor {
        PaymentProcessorStrategy(methods, allwaysthrowerror)
    }
    
    var methods: [PaymentType: PaymentMethod] {
        [
         .creditCard: CreditCardPayment,
        ]
    }
}
```

### 3. Decorator Pattern — Replace Behavior via Parameters

Boolean/enum parameters controlling cross-cutting behavior become composable wrappers.

```swift
// BEFORE: Behavior via parameter (1 sealed point per flag)
protocol DataFetcher {
    func fetch(_ request: URLRequest, cached: Bool, retryCount: Int) -> Data
}

// AFTER: Decorator chain (0 sealed points)
protocol DataFetcher {
    func fetch(_ request: URLRequest) -> Data
}

final class NetworkDataFetcher: DataFetcher {
    func fetch(_ request: URLRequest) -> Data { /* network call */ }
}

final class CachedDataFetcher: DataFetcher {
    private let wrapped: DataFetcher
    private var cache: [URL: Data] = [:]

    init(wrapping fetcher: DataFetcher) { self.wrapped = fetcher }

    func fetch(_ request: URLRequest) -> Data {
        if let cached = cache[request.url!] { return cached }
        let data = wrapped.fetch(request)
        cache[request.url!] = data
        return data
    }
}

final class RetryDataFetcher: DataFetcher {
    private let wrapped: DataFetcher
    private let maxRetries: Int

    init(wrapping fetcher: DataFetcher, maxRetries: Int = 3) {
        self.wrapped = fetcher
        self.maxRetries = maxRetries
    }

    func fetch(_ request: URLRequest) -> Data {
        // retry logic wrapping wrapped.fetch(request)
    }
}

// Usage: composable, each concern independent
let fetcher = RetryDataFetcher(
    wrapping: CachedDataFetcher(
        wrapping: NetworkDataFetcher()
    )
)
```
