---
name: strategy
displayName: Strategy
category: behavioral
description: Define a family of algorithms, encapsulate each one, and make them interchangeable
---

# Strategy

> Define a family of algorithms, encapsulate each one, and make them interchangeable. Strategy lets the algorithm vary independently from clients that use it. — GoF

---

## When to Use

- A class has a switch/if-else chain selecting between different behaviors based on a type or enum
- You want to add new behavior variants without modifying the existing class
- Different algorithms need to be swappable at runtime

---

## Structure

```swift
// Strategy protocol
protocol Algorithm {
    func execute(input: Input) -> Output
}

// Concrete strategies
final class AlgorithmA: Algorithm {
    func execute(input: Input) -> Output { ... }
}

final class AlgorithmB: Algorithm {
    func execute(input: Input) -> Output { ... }
}

// Context — uses strategy via protocol, doesn't know which implementation
final class Processor {
    private let algorithm: Algorithm

    init(algorithm: Algorithm) {
        self.algorithm = algorithm
    }

    func process(input: Input) -> Output {
        algorithm.execute(input: input)
    }
}
```

---

## Example

```swift
protocol PaymentMethod {
    func process(amount: Double) async throws
}

final class CreditCardPayment: PaymentMethod {
    func process(amount: Double) async throws { ... }
}

final class PayPalPayment: PaymentMethod {
    func process(amount: Double) async throws { ... }
}

// Context with dictionary of strategies
final class PaymentProcessor {
    private let methods: [PaymentType: PaymentMethod]

    init(methods: [PaymentType: PaymentMethod]) {
        self.methods = methods
    }

    func processPayment(amount: Double, type: PaymentType) async throws {
        guard let method = methods[type] else {
            throw PaymentError.unsupportedType(type)
        }
        try await method.process(amount: amount)
    }
}

// Adding a new payment type = new class, zero modification to PaymentProcessor
```

---

## Recognition Conditions

Checklist to verify a type uses the Strategy pattern. **ALL conditions must hold:**

1. **Protocol-typed strategy** — the context holds one or more protocol-typed properties representing the algorithm
2. **No type switching** — the context has no switch/if-else on type or enum to select behavior
3. **Closed for modification** — adding a new variant requires only a new conforming type, not changes to the context
