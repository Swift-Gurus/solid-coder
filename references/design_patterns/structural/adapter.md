---
name: adapter
displayName: Adapter
category: structural
description: Convert the interface of a class into another interface clients expect
---

# Adapter

> Convert the interface of a class into another interface clients expect. Adapter lets classes work together that couldn't otherwise because of incompatible interfaces. — GoF

---

## When to Use

- You need to use an existing class but its interface doesn't match what your code expects
- You want to isolate a third-party or framework dependency behind a protocol you own
- You need to make an unowned type conform to a protocol without modifying it

---

## Structure

```swift
// Target interface (what clients expect)
protocol Target {
    func request()
}

// Adaptee (existing class with incompatible interface)
class Adaptee {
    func specificRequest() { ... }
}

// Adapter (bridges the gap)
final class Adapter: Target {
    private let adaptee: Adaptee

    init(adaptee: Adaptee) {
        self.adaptee = adaptee
    }

    func request() {
        adaptee.specificRequest()
    }
}
```

---

## Example

```swift
// Third-party SDK with incompatible interface
class ExternalAnalytics {
    func logEvent(_ name: String, parameters: [String: Any]) { ... }
}

// Protocol we own
protocol AnalyticsTracking {
    func track(_ event: String)
}

// Adapter bridges the external type to our protocol
final class ExternalAnalyticsAdapter: AnalyticsTracking {
    private let analytics: ExternalAnalytics

    init(analytics: ExternalAnalytics) {
        self.analytics = analytics
    }

    func track(_ event: String) {
        analytics.logEvent(event, parameters: [:])
    }
}

// Adapter to encapsulate static APIs of third-party/system frameworks

protocol Validator {
    var isInitialized: Bool { get }
}

struct SystemFramworkValidatorAdapter: Validator {
    var isInitialized: Bool {
        ThirdPartyOrSystemFramework.alreadyInitialized
    }
}

```

---

## Recognition Conditions

Checklist to verify a type is an Adapter. **ALL conditions must hold:**

1. **Protocol conformance** — the adapter conforms to a target protocol
2. **Wraps an adaptee** — has a stored property of the type being adapted
3. **Translates interface** — every protocol method delegates to the adaptee, translating between interfaces
