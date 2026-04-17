---
name: code-smells-code
type: code
---

# Code Smells — Write-Time Constraints

Hard rules to apply whenever you write or modify Swift code. Treat each rule as a constraint, not a suggestion. If you feel tempted to break one, that's usually a design signal — redesign the approach.

---

## CS-1: Do NOT use `static` as a lint-fix shortcut

When a linter or type-checker complains (e.g. "Cannot use instance member inside a static context", "Missing self reference", "Closure captures self"), do NOT resolve it by converting the method/property to `static`. That collapses the sealed-point / OCP violation from "injectable dependency" to "global call site" — a harder problem to fix later.

**Instead:**
- If the method uses instance state → keep it instance, fix the caller.
- If the method is stateless utility logic → extract to an instance on a small helper type and inject that, OR keep the method non-static on the current type.
- If the caller is in a closure and captures `self` → fix the capture (`[weak self]`, pass in values), not the method.

### Allowed `static` (exhaustive list — do NOT expand without updating this file)

A `static` member is acceptable ONLY when it falls into one of these categories:

1. **Compile-time constants** — `static let apiVersion = "v2"` where the value is a literal with no dependencies.
2. **Factory methods on value types** — `static func make(from: …) -> Self` on structs/enums that construct themselves from inputs. Only when the result is the containing type itself.
3. **Language-required static members** — `static func == (lhs:, rhs:)`, `static var allCases`, etc. — anything required to conform to a `static`-bearing protocol requirement (Equatable, CaseIterable, CustomStringConvertible, …).

### NOT allowed (common anti-patterns to refuse)

- **"Utility namespace" enums with `static func`** — `enum StringFormatting { static func …(…) }`. This is the single most-abused escape hatch. Even if the functions are "pure", prefer a small instance type that can be injected (`struct StringFormatter { func …(…) }`) so callers can substitute in tests and so future dependencies (Locale, a logger, a cache) don't force a rewrite.
- **"Wrapper" statics around framework APIs** — `static func assertEquals(…)` wrapping `XCTAssertEqual`. The fact that Apple exposes a static doesn't mean your wrapper should be static too. Wrap it on an instance type.
- `static var shared = …` / `static let shared = …` on any type that holds mutable state or has dependencies. That's a singleton — use dependency injection.
- Converting an instance method to `static` because "it doesn't use `self` right now".
- `static func` on a service/manager/coordinator to "make it easier to call". Services must be injected.
- `static var _cache: […] = [:]` — global mutable state disguised as cache.
- Adding `static` to escape a closure capture or actor isolation diagnostic.

### How to respond when asked to "just make it static"

If a spec, finding, or prompt explicitly asks you to introduce a `static` member that is NOT in the allowed list:
1. Do not apply the change.
2. Explain briefly which CS-1 category the request violates.
3. Propose the instance-based or DI-based alternative.

The caller can override by adding a directive in their prompt or in the consuming project's `CLAUDE.md`.

---

## CS-2: When splitting a type into pieces, use OCP or composition — not namespace statics

When a type has grown too big and you want to extract sub-concerns into their own types, the result must be **instance-backed**. Two valid shapes:

1. **OCP (protocol + injection)** — when the extracted piece has dependencies, policy, or substitutable behavior.
2. **Composition (plain helper instances held as properties)** — when the extracted piece is dependency-free, has one obvious implementation, and you don't need to swap it out.

Do NOT extract into a type that exists only to host static functions.

### The anti-pattern to refuse

Given a big class:

```swift
class OrderProcessor {
    func process(_ order: Order) {
        let validated = self.validate(order)
        let enriched  = self.enrich(validated)
        let priced    = self.price(enriched)
        self.save(priced)
    }
    private func validate(_:) -> Order { … }
    private func enrich(_:)   -> Order { … }
    private func price(_:)    -> Order { … }
    private func save(_:)              { … }
}
```

**DO NOT** split like this:

```swift
enum OrderValidation   { static func validate(_:) -> Order { … } }
enum OrderEnrichment   { static func enrich(_:)   -> Order { … } }
enum OrderPricing      { static func price(_:)    -> Order { … } }
enum OrderPersistence  { static func save(_:)              { … } }

class OrderProcessor {
    func process(_ order: Order) {
        let v = OrderValidation.validate(order)
        let e = OrderEnrichment.enrich(v)
        let p = OrderPricing.price(e)
        OrderPersistence.save(p)
    }
}
```

### DO — shape 1: OCP (protocol + injection) when sub-concerns have dependencies or substitutable behavior

Use this when the piece you're extracting might: depend on other services (logger, cache, clock), vary by product/locale/test, or otherwise need substitution.

```swift
protocol OrderValidating { func validate(_ order: Order) -> Order }
protocol OrderEnriching  { func enrich(_ order: Order)  -> Order }
protocol OrderPricing    { func price(_ order: Order)   -> Order }
protocol OrderPersisting { func save(_ order: Order) }

struct DefaultOrderValidator: OrderValidating { func validate(_:) -> Order { … } }
struct DefaultOrderEnricher:  OrderEnriching  { func enrich(_:)   -> Order { … } }
struct DefaultOrderPricer:    OrderPricing    { func price(_:)    -> Order { … } }
struct DefaultOrderPersister: OrderPersisting { func save(_:) { … } }

final class OrderProcessor {
    private let validator: OrderValidating
    private let enricher: OrderEnriching
    private let pricer: OrderPricing
    private let persister: OrderPersisting

    init(validator: OrderValidating,
         enricher: OrderEnriching,
         pricer: OrderPricing,
         persister: OrderPersisting) {
        self.validator = validator
        self.enricher  = enricher
        self.pricer    = pricer
        self.persister = persister
    }

    func process(_ order: Order) {
        let v = validator.validate(order)
        let e = enricher.enrich(v)
        let p = pricer.price(e)
        persister.save(p)
    }
}
```

### DO — shape 2: Composition with concrete helpers when sub-concerns have no dependencies
Use this when the piece is a **pure, dependency-free** helper — no policy, no logger, no substitution — and you don't need to swap it in tests. Keep them as instance properties of the owning class, held directly by concrete type. No protocol, no DI ceremony, but still **instance-based**, not static.

```swift
struct OrderValidator { func validate(_ order: Order) -> Order { … } }
struct OrderEnricher  { func enrich(_ order: Order)  -> Order { … } }
struct OrderPricer    { func price(_ order: Order)   -> Order { … } }
struct OrderPersister { func save(_ order: Order) { … } }

final class OrderProcessor {
    private let validator = OrderValidator()
    private let enricher  = OrderEnricher()
    private let pricer    = OrderPricer()
    private let persister = OrderPersister()

    func process(_ order: Order) {
        let v = validator.validate(order)
        let e = enricher.enrich(v)
        let p = pricer.price(e)
        persister.save(p)
    }
}
```

If a helper later needs substitution or gains dependencies, lift it to shape 1 without touching other helpers.

### Decision checklist before extracting

Ask in order:

1. **Does the piece have (or might plausibly gain) dependencies, policy, or substitution needs?** → Shape 1: protocol + injection.
2. **Is the piece pure and dependency-free, and you're sure it will stay that way?** → Shape 2: concrete helper held as an instance property.
3. **Is it a pure transform on a primitive type (no policy, no dependencies)?** → `extension <Primitive> { func … }`.

The answer is **never** "put it in an `enum` as `static func`".

### Allowed shapes when splitting

- `extension <InputType> { func … }` for pure primitive transforms.
- `protocol <Role>ing { func … }` + `struct Default<Role>: <Role>ing { func … }` + inject, for concerns with dependencies.
- A plain `struct/class` with instance methods (no static), held as a property on the owner, for dependency-free helpers.

### Forbidden shapes when splitting

- `enum X { static func … }` / `struct X { static func … }` / `class X { static func … }`.
- Any new type introduced solely to host one or more static functions.

---

## (Room for future smells)

Add new rules as `CS-3`, `CS-4`, … with the same structure: rule statement → allowed exceptions → "instead" example.
