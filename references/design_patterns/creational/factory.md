---
name: factory
displayName: Factory
category: creational
description: A separate type whose job is constructing other types, exposed behind a protocol so consumers depend on the contract rather than a specific concrete implementation
---

# Factory

> A separate type whose responsibility is constructing other types, exposed behind a protocol so consumers depend on the construction contract, not on a specific concrete implementation.

---

## Intent

Construction is itself a dependency. When the rules for building an object can vary — by environment, tenant, test context, or policy — that variance deserves its own abstraction. A factory type makes the construction strategy itself substitutable, without forcing consumers to know which concrete producer is in use.

---

## Structure

- A protocol describes the construction contract (`make…` / `build…` methods and their inputs)
- A concrete type conforms to the protocol and implements the actual construction
- The concrete type is instantiable — it has a normal initializer and may hold state (caches, clocks, configuration)
- Consumers receive the factory **instance** through their own initializer; they do not reference it by name

```swift
protocol ReportMaking {
    func makeReport(for user: User) -> any Report
}

struct RemoteReportFactory: ReportMaking {
    private let client: any HTTPClient

    init(client: any HTTPClient) {
        self.client = client
    }

    func makeReport(for user: User) -> any Report {
        RemoteReport(client: client, user: user)
    }
}

final class Dashboard {
    private let reports: any ReportMaking

    init(reports: any ReportMaking) {
        self.reports = reports
    }
}
```

---

## When to Use

- Construction logic itself must be swappable (production vs test, A/B routing, per-tenant behavior)
- The factory needs to hold its own dependencies (a client, a logger, a cache)
- The target is polymorphic — different inputs produce different concrete types and the choice is a policy decision
- Multiple unrelated consumers will build the same kind of object and should share the construction path

If production construction is stable and only user input varies, reach for a factory **method** (see `factory-method.md`) before introducing a factory type.

---

## Anti-pattern

A namespace type that exposes only static construction methods — it has no stored state, cannot be instantiated, and cannot be injected. Every consumer that needs to build an X calls the namespace directly by name.

Consequences:

- Every call site hardcodes the dependency on that specific namespace. Swapping construction strategies requires editing every call site.
- Tests cannot substitute the construction path with a stub without touching production code.
- Adding a variant (different cache, different logger, per-environment routing) forces modification rather than extension.

Naming such a type "Factory" does not change the shape. The rule is structural, not nominal.

---

## Recognition Conditions

ALL must hold:

1. Conforms to a protocol that describes its construction contract
2. Is instantiable — a normal initializer, not a namespace of static-only members
3. Consumers receive the factory instance through their own initializer and do not reference it by name from inside their implementation

---

## Related

- `factory-method.md` — construction expressed as a secondary initializer on the target type itself. Prefer this when production construction is stable and only user input varies.
- `builder.md` — step-by-step construction where many options accumulate before the target is produced.
