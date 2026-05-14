<fix id="SUI-9" name="Actor Isolation Granularity">

<trigger>
`@MainActor` applied to an entire class, struct, or protocol when only specific
members need main-thread isolation, OR `nonisolated` escape hatches on members
within a `@MainActor` type.
</trigger>

<strategy severity="SEVERE">
Remove type-level `@MainActor`. Apply per-member isolation only to properties and
methods that directly drive UI updates.
</strategy>

<todo>
**Type-level over-isolation:**
- [ ] Remove `@MainActor` from the type declaration
- [ ] Add `@MainActor` only to:
  - `@Published`/`@Observable`-tracked properties that Views read
  - Methods whose sole purpose is mutating those UI-driving properties
  - Direct UIKit/AppKit main-thread API calls
- [ ] For fetch-then-assign methods: keep the method unannotated; isolate only the final state mutation via a separate `@MainActor` method or by assigning to a `@MainActor` property
- [ ] Remove all `nonisolated` keywords — they signal the type annotation is too broad

**Protocol-level over-isolation** (only when a production conformer needs background work):
- [ ] Remove `@MainActor` from the protocol declaration
- [ ] Add `@MainActor` only to specific requirements: UI-state properties, UI-triggering methods
- [ ] **Do NOT remove protocol-level `@MainActor` if ALL production conformers are `@MainActor`** — doing so causes Swift 6 "crosses into main actor-isolated code" errors

**Exceptions (do NOT change):**
- SwiftUI `View` structs — value types, `@MainActor` is harmless and often compiler-inferred
- `UIViewRepresentable` / `UIViewControllerRepresentable` / AppKit equivalents — inherently main-thread
</todo>

<suggested_fix_must_include>
- Before/after of the type declaration showing `@MainActor` moved from type-level to per-member
- Fetch-then-assign method split into background fetch + `@MainActor` state update
- `nonisolated` keywords removed
</suggested_fix_must_include>

</fix>
