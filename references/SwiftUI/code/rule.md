# SwiftUI Coding Gotchas

Common mistakes the code agent makes. These are NOT covered by examples or review rules — they are behavioral patterns to avoid.

---

## 1. Bindings with protocol-constrained Observable ViewModels

When a view uses a generic ViewModel constrained to an Observable protocol (`<VM: SomeState & SomeActions>`), use `@Bindable` to create bindings — never create manual `Binding(get:set:)` wrappers to re-pass the VM's properties.

```swift
struct SettingsView<VM: SettingsState & SettingsActions>: View {
    @State private var vm: VM

    var body: some View {
        // WRONG — manual Binding to bridge protocol properties
        TextField("Name", text: Binding(
            get: { vm.name },
            set: { vm.name = $0 }
        ))

        // RIGHT — @Bindable works with protocol-constrained generics
        // because Observable conformance is guaranteed by the constraint
        @Bindable var bindable = vm
        TextField("Name", text: $bindable.name)
    }
}
```

This applies whenever a view has a generic VM constrained to an Observable protocol and needs two-way bindings (TextField, Toggle, Slider, sheets). The `@Bindable` wrapper works because the generic constraint guarantees Observable conformance at compile time — no need to bridge manually.

---

## 2. @Observable + didSet causes recursive observation tracking crashes

`didSet` on `@Observable` properties interacts poorly with the macro's synthesized accessors. Setting the property inside its own `didSet` causes recursive observation tracking and crashes at runtime.

```swift
// WRONG — crashes: recursive observation tracking
@Observable
final class LayoutState {
    var splitRatio: Double = 0.5 {
        didSet { splitRatio = Self.clamped(splitRatio) }  // recursive crash
    }
}

// RIGHT — private backing storage with computed property
@Observable
final class LayoutState {
    private var _splitRatio: Double = 0.5

    var splitRatio: Double {
        get { _splitRatio }
        set { _splitRatio = Self.clamped(newValue) }
    }
}
```

This applies to any `didSet` that modifies the property itself (clamping, validation, normalization). Use private backing storage + computed get/set instead.
