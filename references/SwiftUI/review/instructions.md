---
name: swiftui-review
type: review
rules: PRINCIPLE_FOLDER_ABSOLUTE_PATH/rule.md
output_schema: output.schema.json
---

### Phase 0: Load Examples for context.
- [ ] **0.1 Read all examples** — Glob `PRINCIPLE_FOLDER_ABSOLUTE_PATH/Examples/*` and read every file found

#### Phase 1: Detection (SUI-1 through SUI-9 run independently and in parallel if possible)

- [ ] **1.1 SUI-1: Measure Body Complexity**
    - [ ] 1.1.1 Identify all view-returning properties — `body` plus any `var`/`func` returning `some View`
    - [ ] 1.1.2 For EACH view-returning property, measure:
        - Max nesting depth of view builder expressions (each View/container that takes @ViewBuilder closure = +1 depth). Modifiers do NOT add depth.
        - Count of distinct view expressions (Text, Image, Button, HStack, VStack, List, custom views, etc.). Modifiers are NOT separate expressions.

      | Property | Nesting Depth | Expression Count | Severity |
      |----------|--------------|------------------|----------|
      | body | ___ | ___ | ___ |
      | | | | |

    - [ ] 1.1.3 Unit severity = worst severity across all view-returning properties

- [ ] **1.2 SUI-2: Assess View Purity**
    - [ ] 1.2.1 List every method and computed property in the view struct (excluding `body`)
    - [ ] 1.2.2 Classify each as PURE_VIEW or IMPURE (DATA_FETCH, TRANSFORM, FORMAT, VALIDATE, COMPUTE)

      | Method/Property | Classification | Reason |
      |-----------------|---------------|--------|
      | | | |

    - [ ] 1.2.3 Count impure methods
      Impure count: ___
    - [ ] 1.2.4 Check for any DATA_FETCH (network, database, file I/O) — always SEVERE
      Has data fetch: ___

- [ ] **1.3 SUI-3: Measure Modifier Chain Length**
    - [ ] 1.3.1 For each `@ViewBuilder` closure in `body` and view-returning properties, identify nested child view expressions (NOT the top-level/outermost view returned by the property)
    - [ ] 1.3.2 For each nested child view, count chained modifiers (`.font()`, `.padding()`, `.background()`, `.frame()`, `.overlay()`, `.clipShape()`, etc.)
    - [ ] 1.3.3 Flag any nested child with modifier count > 2

      | View Expression | Location | Modifier Count | Severity |
      |----------------|----------|---------------|----------|
      | | | | |

    - [ ] 1.3.4 Max nested modifier chain: ___

- [ ] **1.6 SUI-6: Check Preview Coverage**
    - [ ] 1.6.1 List every `struct` conforming to `View` at file scope
    - [ ] 1.6.2 For each, search the same file for `#Preview` or `PreviewProvider` that instantiates it
    - [ ] 1.6.3 If not found in the same file, search in other files in the module for `#Preview` blocks or `PreviewProvider` structs that instantiate it (e.g., dedicated preview files)
    - [ ] 1.6.4 Record results:

      | View | File | Has Preview | Preview Location |
      |------|------|-------------|-----------------|
      | | | | |

    - [ ] 1.6.5 Views with no preview instantiation anywhere: count ___

- [ ] **1.7 SUI-7: Check Container Accessibility Identifiers**
    - [ ] 1.7.1 Identify all container views: `HStack`, `VStack`, `ZStack`, `LazyVStack`, `LazyHStack`, `LazyVGrid`, `LazyHGrid`, `List`, `ScrollView`, `Form`, `Group`
    - [ ] 1.7.2 For each container that has `.accessibilityIdentifier(...)`:
        - Check if `.accessibilityElement(children:)` appears in the modifier chain **before** `.accessibilityIdentifier(...)`
        - If missing → flag as VIOLATION
    - [ ] 1.7.3 Record results:

      | Container | Location | Has `.accessibilityElement` | Has `.accessibilityIdentifier` | Severity |
      |-----------|----------|----------------------------|-------------------------------|----------|
      | | | | | |

    - [ ] 1.7.4 Containers missing `.accessibilityElement`: count ___

- [ ] **1.8 SUI-8: Check Adaptive Sizing**
    - [ ] 1.8.1 Find all `.frame()` calls with literal numeric `width:` or `height:` values
    - [ ] 1.8.2 Exclude exceptions listed in rule.md
    - [ ] 1.8.3 Record results:

      | View Expression | Location | Fixed Dimension | Severity |
      |----------------|----------|-----------------|----------|
      | | | | |

    - [ ] 1.8.4 Fixed frame violations: count ___

- [ ] **1.9 SUI-9: Check Actor Isolation Granularity**
    - [ ] 1.9.1 Find all `@MainActor` annotations on type declarations (`class`, `struct`, `protocol`, `extension`) — exclude `View` structs and UIKit/AppKit interop types (`UIViewRepresentable`, `UIViewControllerRepresentable`)
    - [ ] 1.9.2 For each annotated **class/struct**, classify every member:
        - NEEDS_MAIN — only members that **directly drive UI updates**:
            - `@Published` properties or `@Observable`-tracked properties that a View reads
            - Methods whose **sole purpose** is mutating those UI-driving properties (e.g., a method that sets `isLoading = true` then `items = newItems`)
            - Calls to UIKit/AppKit APIs that require main thread (`UIApplication.shared`, layout APIs)
        - BACKGROUND_SAFE — everything else:
            - Network calls, API requests, data fetching
            - Parsing, decoding, serialization
            - Computation, filtering, sorting, mapping
            - File I/O, database access, caching
            - Methods that **fetch then assign** — the fetch part doesn't need main; only the final state assignment does (use `@MainActor` on the assignment, not the whole method)
    - [ ] 1.9.3 Check for `nonisolated` escape hatches — any `nonisolated` keyword on members within a `@MainActor` type
    - [ ] 1.9.4 Check protocols — **conformer analysis required**:
        - For each `@MainActor protocol`, find all production conformers (exclude preview-only and test doubles)
        - If ALL production conformers are `@MainActor` → COMPLIANT (protocol correctly reflects conformer reality, avoids Swift 6 crossing errors)
        - If ANY production conformer needs background-safe work → SEVERE (protocol forces it onto main)
        - If NO production conformers exist (only preview/test) → COMPLIANT
    - [ ] 1.9.5 Record results:

      | Type | Kind | Total Members | Background-Safe | nonisolated Count | Conformer Check | Severity |
      |------|------|--------------|-----------------|-------------------|-----------------|----------|
      | | | | | | | |

    - [ ] 1.9.6 Types with over-broad `@MainActor`: count ___

#### Phase 2: Filter Out Exceptions

- [ ] **2.1 Cross-check exceptions** — mark exceptions

  | View | Exception reason |
  |------|------------------|
  | | |
- [ ] **2.2 Exclude exceptions** — exclude exceptions from analysis

#### Phase 3: Scoring

- [ ] **3.1 Determine severity**
    - [ ] 3.1.1 Body complexity: nesting ___, expressions ___, severity: ___
    - [ ] 3.1.2 View purity: impure count ___, has data fetch ___, severity: ___
    - [ ] 3.1.3 Modifier chain: max nested chain ___, severity: ___
    - [ ] 3.1.4 Preview coverage: views without preview ___, severity: ___
    - [ ] 3.1.5 Container accessibility: containers missing `.accessibilityElement` ___, severity: ___
    - [ ] 3.1.6 Adaptive sizing: fixed frame violations ___, severity: ___
    - [ ] 3.1.7 Actor isolation granularity: over-broad `@MainActor` types ___, severity: ___
    - [ ] 3.1.8 Adjust severity considering exceptions.
    - [ ] 3.1.9 Final severity: ___

#### Phase 4: Output

- [ ] **4.1 Report Violations**
    - [ ] 4.1.1 Show body complexity measurements
    - [ ] 4.1.2 Show view purity classification table
    - [ ] 4.1.3 Show modifier chain length table (if any flagged)
    - [ ] 4.1.4 Show cross-reference table with found exceptions
    - [ ] 4.1.5 Show preview coverage table (if any views lack previews)
    - [ ] 4.1.6 Show container accessibility table (if any containers flagged)
    - [ ] 4.1.7 Show adaptive sizing table (if any fixed frames flagged)
    - [ ] 4.1.8 Show actor isolation table (if any over-broad @MainActor types flagged)
