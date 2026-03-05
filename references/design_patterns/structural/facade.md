---
name: facade
displayName: Facade
category: structural
description: Provide a unified interface to a set of interfaces in a subsystem
---

# Facade (Coordinator)

> Provide a unified interface to a set of interfaces in a subsystem. Facade defines a higher-level interface that makes the subsystem easier to use. — GoF

---

## When to Use

- A class that encapsulates multiple subsystems but owns no business logic itself
- After extracting concerns into separate types, the original class becomes a thin orchestrator
- You want to simplify a complex set of dependencies behind a single entry point

---

## Structure

```swift
protocol SubsystemA {
    func doA()
}

protocol SubsystemB {
    func doB()
}

// Facade — coordinates subsystems, owns no logic
final class Facade {
    private let a: SubsystemA
    private let b: SubsystemB

    init(a: SubsystemA, b: SubsystemB) {
        self.a = a
        self.b = b
    }

    func perform() {
        a.doA()
        b.doB()
    }
}
```

## Recognition Conditions

Checklist to verify a class is a Facade. **ALL conditions must hold:**

1. **All-protocol dependencies** — every stored property / init parameter is protocol-typed
2. **Pure delegation** — every method body calls one or more dependencies; no business logic, no branching on own mutable state, no computation beyond forwarding
3. **No internal construction** — the class creates no objects internally; all dependencies are injected via init
