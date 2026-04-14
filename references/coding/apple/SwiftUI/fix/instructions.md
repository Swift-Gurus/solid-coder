---
name: swiftui-fix
type: fix
rules: PRINCIPLE_FOLDER_ABSOLUTE_PATH/refactoring.md
input_schema: PRINCIPLE_FOLDER_ABSOLUTE_PATH/review/output.schema.json
output_schema: output.schema.json
---

### Phase 0: Load Context

- [ ] **0.1 Read the review findings JSON** (provided as structured input_schema)
- [ ] **0.2 Read the source file** (provided as input)

#### Phase 1: Determine Fix Strategy

- [ ] **1.1 Read `scoring.final_severity` from findings**
    - SEVERE → full refactoring (see refactoring.md)

- [ ] **1.2 Identify which metrics triggered the severity**
    - SUI-1 (body complexity) → Extract Subview pattern
    - SUI-2 (view purity) → Move to ViewModel pattern (injected via interfaces, see examples and SUI-4 guidance)
    - SUI-3 (modifier chain) → Extract to Named Variable pattern
    - SUI-4 (VM injection) → Extract State + Actions protocols pattern (see examples)
    - SUI-5 (Preview containment) → Move into #Preview block pattern (see examples)
    - SUI-6 (preview coverage) → Create Preview File pattern
    - SUI-7 (container a11y ID) → Add `.accessibilityElement(children: .contain)` before `.accessibilityIdentifier(...)` pattern
    - SUI-8 (adaptive sizing) → Remove literal frame, apply proportional sizing
    - SUI-9 (actor isolation) → Remove type-level `@MainActor`, apply per-member isolation pattern
    - Multiple → combine patterns as needed

#### Phase 2: Identify Suggestions

- [ ] **2.1 Analyze findings** — read metrics (nesting depth, view expression count, impure method list, modifier chain flagged views)
- [ ] **2.2 Propose suggestion** — which body sections to extract, which methods to move to ViewModel, which inline views to extract to named variables
- [ ] **2.3 Create todo items** — concrete actionable steps to implement the fix:
    - [ ] For SUI-1: identify coherent body sections, name new subviews, define their inputs
    - [ ] For SUI-2: create ViewModel (if none exists by following SUI-4 guidance fix) or move impure methods to existing ViewModel, update view to read from ViewModel
    - [ ] For SUI-3: identify nested views with >2 modifiers, extract each to a `private var` with a descriptive name, replace inline usage with the variable reference
    - [ ] For SUI-4: extract State protocol (readable properties) and Actions protocol (methods the view triggers) from existing concrete ViewModel. Then choose injection style based on whether the view observes changes:
        - **Observable protocols** (State protocol extends `Observable`): add generic constraint to view (`struct MyView<S: MyState>: View`). Generic is required — SwiftUI's observation tracking needs the concrete type at compile time. Use `@State` only if the view owns the object lifecycle; use plain `let`/`var` if injected. For two-way bindings (`$vm.property`): use a local `@Bindable var bindable = vm` inside `body` to get the `$` projection — do NOT use manual `Binding(get:set:)`. State protocol properties that need binding must be `{ get set }`. See `bindable-view-compliant.swift` example.
        - **Non-observable protocols** (Actions protocol, data sources read once): use plain protocol-typed property (`let actions: MyActions`). No generic needed. See `stateful-view-compliant.swift` — `actions` is a plain protocol property, only `state` uses generic. See `non-observable-vm-compliant.swift` for a full example.
    - [ ] For SUI-5: identify all file-scope views and helper types only referenced from `#Preview`/`PreviewProvider`, move their declarations inside the `#Preview` block, update the preview return to use the now-nested types
    - [ ] For SUI-6: create a dedicated preview file in a `Previews/` folder at the component root. File named `{ViewName}Previews.swift`. Include `#Preview` blocks showing the view's key states (default, edge cases, different configurations). Use sample data — no real dependencies.
    - [ ] For SUI-7: for each flagged container, insert `.accessibilityElement(children: .contain)` immediately before the existing `.accessibilityIdentifier(...)` modifier. Choose the `children:` strategy:
        - `.contain` — children remain individually accessible (default, most common for test containers)
        - `.combine` — children merge into a single accessible element (use when the container is a single semantic unit, e.g., a label + value pair)
        - `.ignore` — children hidden from accessibility (rare, only when children are decorative)
    - [ ] For SUI-8: for each literal `.frame(width:height:)`, determine the fix based on context:
        - **Child/internal self-sizing** (view hardcodes its own or its sub-elements' size) → remove the frame entirely, let the parent control sizing using the proportional approach below
        - **Parent rigid sizing** (parent hardcodes a child's size) → replace with proportional approach:
            - `containerRelativeFrame` (preferred, iOS 17+) — when the size should be a fraction of the container. Does not disrupt stack layout negotiation.
            - `frame(minWidth:maxWidth:)` — when you need a flexible range with safety bounds
            - `frame(maxWidth: .infinity)` — when the view should fill available space
            - `GeometryReader` — last resort only. It returns a flexible preferred size that expands greedily, which breaks layout negotiation in stacks. Only use when `containerRelativeFrame` is not available or when you need the geometry for non-sizing purposes (e.g., scroll offsets, position-dependent effects).
    - [ ] For SUI-9: for each over-isolated type, apply per-member isolation:
        - **Type-level over-isolation** → remove `@MainActor` from the type declaration. Add `@MainActor` only to:
            - `@Published`/`@Observable`-tracked properties that Views read
            - Methods whose **sole purpose** is mutating those UI-driving properties
            - Direct UIKit/AppKit main-thread API calls
            - For fetch-then-assign methods: do NOT mark the whole method `@MainActor`. Keep the method unannotated and isolate the state mutation via a **separate `@MainActor` method** that handles the UI update (preferred — cleanest separation), or assign to a `@MainActor` property.
        - **Protocol-level over-isolation** → only flagged when a production conformer needs background work. Remove `@MainActor` from the protocol declaration. Add `@MainActor` only to specific requirements that must run on main thread (UI-state properties, UI-triggering methods). This frees that conformer to implement non-UI requirements on any executor. **Do NOT remove protocol-level `@MainActor` if all production conformers are `@MainActor`** — doing so causes Swift 6 "crosses into main actor-isolated code" errors.
        - **nonisolated escape hatch** → remove type-level `@MainActor`, remove all `nonisolated` keywords. Add `@MainActor` only to the members that actually need it — the previously-nonisolated members were already correct to be off main thread.
    - Each todo item should be a single, implementable action

#### Phase 3: Write suggested_fix

- [ ] **3.1 Write full code snippets** showing:
    - New subview structs with their properties (if SUI-1)
    - New or updated ViewModel with moved methods, State + Actions protocols, ViewModel conforming to both, view with generic constraint (if SUI-2/SUI-4)
    - Modified view with extracted subviews and delegated logic
    - Before/after of body structure
    - Container with `.accessibilityElement(children: .contain)` inserted before `.accessibilityIdentifier(...)` (if SUI-7)
    - Before/after of frame usage showing literal replaced with proportional sizing, design system token, or removed entirely (if SUI-8)
    - Before/after of type declaration showing type-level `@MainActor` replaced with per-member annotations (if SUI-9)
- [ ] **3.2 Predict post-fix metrics** (nesting depth, view expression count, impure count per view, fixed frame count, over-isolated type count)

#### Phase 4: Generate Output

- [ ] **4.1 Produce JSON matching output schema**
    - [ ] 4.1.1 Fill `suggested_fix` with the full text + code snippets from Phase 3
    - [ ] 4.1.2 Fill `todo_items` with the actionable steps from Phase 2.3
    - [ ] 4.1.3 Fill `verification` with predicted metrics from Phase 3.2
    - [ ] 4.1.4 Fill `addresses` with finding IDs this suggestion resolves

#### Constraints
- Include full code snippets in suggested_fix (subviews, ViewModels, modified parent)
- Todo items must be concrete and implementable (not vague)
- Preserve existing public API — external callers should see the same view interface
- All violations are SEVERE — apply full refactoring patterns
- Prefer `@Observable` macro over `ObservableObject` protocol for new ViewModels (iOS 17+)
