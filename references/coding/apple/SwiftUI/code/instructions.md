---
name: swiftui-code
type: code
---

# SwiftUI Coding Instructions

These are mandatory rules that must be followed when writing SwiftUI code. Check each rule before writing — if any gate fails, stop and redesign before proceeding.

---

<rule id="SUI-1" name="Keep Body Simple">
Before adding more views to `body` or any view-returning computed property:
- Max nesting depth: 1 level of `@ViewBuilder` closures. Reaching depth 2 → extract into a named subview.
- Max distinct view expressions: 4. Reaching 5 (`Text`, `Image`, `Button`, `HStack`, custom views, etc.) → extract into a named subview.
- Modifiers do NOT count as nesting or expressions — only view types do.
- Each view-returning property is measured independently — complexity does not disappear by moving it out of `body` into a helper `var`.
</rule>

<rule id="SUI-2" name="Views Are Dumb">
Before writing any method or computed property in a View struct (other than `body`):
- It must ONLY toggle simple UI state (`showSheet = true`, `isExpanded.toggle()`) or return `some View`.
- NEVER in a View: network calls, database reads, sorting/filtering collections, input validation, business rule checks, calculations, state machine transitions.
- All of those belong in the ViewModel. Move them there before writing.
- Exception: inline SwiftUI format specifiers (`Text(price, format: .currency(code: "USD"))`) and single-line action forwarding (`func retry() { viewModel.retry() }`) are pure view.
</rule>

<rule id="SUI-3" name="Extract Nested Views with Modifiers">
Before adding 2 or more modifiers to a child view inside a `@ViewBuilder` closure:
- Extract it into a named `var` or separate subview instead.
- Applies only to nested child views inside closures — NOT to the outermost view returned by `body` or a computed property.
</rule>

<rule id="SUI-4" name="Inject ViewModel via Protocol">
Before storing a ViewModel in a View:
- Never reference a concrete ViewModel class — always depend on protocol interfaces.
- If the protocol extends `Observable` → use a generic constraint: `struct MyView<VM: StateProtocol & ActionsProtocol>: View`. A plain protocol-typed property will not work with SwiftUI's observation tracking.
- If the protocol does NOT extend `Observable` → a plain protocol-typed property is fine.
- For two-way bindings with a generic Observable VM → use `@Bindable` inside `body`, never manual `Binding(get:set:)` wrappers.
- NEVER use `didSet` on `@Observable` properties to mutate the same property — it causes recursive observation tracking crashes. Use private backing storage with a computed get/set instead.
</rule>

<rule id="SUI-5" name="Preview-Only Views Inside #Preview">
Before declaring a View struct that is only used in previews:
- Declare it inside the `#Preview` block or `PreviewProvider` struct — not at file scope.
- File-scope view structs compile into the production binary. A view only referenced from `#Preview` is dead production code.
</rule>

<rule id="SUI-6" name="Every View Needs a Preview">
Before finishing any file-scope View struct:
- Add a `#Preview` block or `PreviewProvider` that instantiates it — in the same file or a dedicated preview file.
- Views without previews cannot be visually validated during development.
</rule>

<rule id="SUI-7" name="Accessibility Identifier on Containers">
Before adding `.accessibilityIdentifier(...)` to a container view (`HStack`, `VStack`, `ZStack`, `List`, `ScrollView`, `Form`, `LazyVStack`, `LazyHStack`, `LazyVGrid`, `LazyHGrid`, `Group`):
- Add `.accessibilityElement(children: .contain)` (or `.combine`/`.ignore`) BEFORE `.accessibilityIdentifier(...)` in the modifier chain.
- Without this, the container is invisible to the accessibility tree and XCUI tests will fail to find it.
- Exception: a custom container view that already applies `.accessibilityElement(children:)` internally — callers adding `.accessibilityIdentifier(...)` externally are compliant.
</rule>

<rule id="SUI-8" name="No Fixed Frames">
Before writing `.frame(width:)` or `.frame(height:)` with a literal numeric value:
- Do NOT hardcode point values. Use the layout system instead.
- Allowed: `frame(maxWidth: .infinity)`, `frame(minWidth:)`, `frame(maxWidth:)`, `frame(idealWidth:)`, `containerRelativeFrame`, `GeometryReader`-based calculations.
- Exception: the prompt or spec explicitly specifies a fixed size.
</rule>

<rule id="SUI-9" name="Per-Member @MainActor, Not Type-Level">
Before marking an entire class, struct, or protocol `@MainActor`:
- Check each member: does it need the main thread?
- NEEDS MAIN: properties tracked by `@Observable`/`@Published` that drive UI, methods whose only job is mutating those properties, direct UIKit/AppKit main-thread calls.
- BACKGROUND SAFE: network calls, parsing, decoding, computation, filtering, sorting, file I/O, database access. A method that fetches then assigns is background-safe — only the final state mutation needs main.
- If ANY member is background-safe → do NOT mark the type `@MainActor`. Annotate only the members that need it.
- `nonisolated` on members inside a `@MainActor` type is a smell — it means the type-level annotation is too broad.
- For protocols: type-level `@MainActor` is only correct if ALL production conformers are legitimately `@MainActor`.
- Exception: SwiftUI `View` structs (value types, compiler-inferred), `UIViewRepresentable`/`UIViewControllerRepresentable` and AppKit equivalents (inherently main-thread), `@main` app entry point.
</rule>

<exceptions>
- App entry point — `@main` struct with `WindowGroup`/`Scene`. High nesting is expected at the app root.
- Preview providers — `#Preview` blocks and `PreviewProvider` structs are not production code.
</exceptions>
