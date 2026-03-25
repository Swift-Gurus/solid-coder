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
    - Each todo item should be a single, implementable action

#### Phase 3: Write suggested_fix

- [ ] **3.1 Write full code snippets** showing:
    - New subview structs with their properties (if SUI-1)
    - New or updated ViewModel with moved methods, State + Actions protocols, ViewModel conforming to both, view with generic constraint (if SUI-2/SUI-4)
    - Modified view with extracted subviews and delegated logic
    - Before/after of body structure
- [ ] **3.2 Predict post-fix metrics** (nesting depth, view expression count, impure count per view)

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
