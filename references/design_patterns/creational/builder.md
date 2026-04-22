---
name: builder
displayName: Builder
category: creational
description: Step-by-step construction of a complex object where many options are optional or combinable and a single initializer signature would be unwieldy
---

# Builder

> Separate the construction of a complex object from its representation so that the same construction process can create different representations. — GoF

---

## Intent

Construction happens in stages. State accumulates through a sequence of calls; at the end, a terminal step produces the target. Builders exist because some objects have too many optional parameters, too many interdependent combinations, or a construction order that doesn't fit a single initializer signature.

---

## Structure

One builder instance accumulates state across a sequence of setter calls. A terminal method (commonly named `build()`) returns the constructed target. The builder is disposable — one build call, then discard and construct a fresh builder for the next target.

```swift
struct ReportQueryBuilder {
    private var filters: [Filter] = []
    private var sort: Sort?
    private var limit: Int?

    mutating func adding(filter: Filter) -> Self {
        filters.append(filter)
        return self
    }

    mutating func ordered(by sort: Sort) -> Self {
        self.sort = sort
        return self
    }

    mutating func limited(to limit: Int) -> Self {
        self.limit = limit
        return self
    }

    func build() -> ReportQuery {
        ReportQuery(filters: filters, sort: sort, limit: limit)
    }
}

// Call site
let query = ReportQueryBuilder()
    .adding(filter: .active)
    .adding(filter: .byOwner(user))
    .ordered(by: .createdAt)
    .limited(to: 50)
    .build()
```

---

## When to Use

- The target has many optional or mutually-exclusive parameters and initializer overloads would multiply
- Construction proceeds in a natural order (configure → validate → build)
- A fluent call-site reads better than a long argument list
- Different combinations of the same inputs can produce different valid results

## When NOT to Use

- All parameters are known up front and a single call suffices — use a **factory method** on the target type (a secondary initializer with defaults)
- The construction is stable and only one input varies — again, a factory method
- There are only two or three parameters — a direct initializer is simpler than a builder

---

## Anti-pattern

A "builder" that is a namespace with a single terminal function and no accumulated state is not a builder — it's a factory method dressed up. Without a sequence of setters that mutate builder state, the pattern has no purpose; a plain factory method on the target type is simpler and carries fewer types.

A builder that is reused across multiple constructions without resetting state produces accidental coupling between the built objects. Each build should start from a fresh builder.

---

## Recognition Conditions

ALL must hold:

1. The builder is **instantiable** and holds mutable state (or uses fluent returns of `Self`)
2. State **accumulates** across multiple setter calls — at least one setter per construction sequence
3. A **terminal method** (commonly `build()`) returns the constructed target
4. A **fresh builder instance** is used for each construction — builders are not reused across builds
