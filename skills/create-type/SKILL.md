---
name: create-type
description: Enforce naming conventions, file organization, and solid- frontmatter when creating new types. Applies to any new class, struct, protocol, enum, etc.
argument-hint: <file-path> [<file-path> ...]
allowed-tools: Read, Grep, Glob, Edit, Write
user-invocable: false
---

# Create Type

Enforce naming conventions, file organization, and `/** solid-... */` frontmatter when creating new types.

## Input

- FILES: $ARGUMENTS — one or more file paths (existing files to annotate, or context for new types being created)

## Phase 1: Naming Conventions

Apply these naming rules when creating or reviewing type names:

### 1.1 Protocol / Interface Naming

**Actor protocols** (the type that performs an action) — use `-ing` suffix:
- Reading/fetching: `ProductReading`, `UserReading`, `OrderReading`
- Saving/creating: `ProductSaving`, `UserSaving`, `OrderSaving`
- Updating: `ProductUpdating`, `UserUpdating`, `OrderUpdating`
- Deleting: `ProductDeleting`, `UserDeleting`, `OrderDeleting`
- Non-CRUD actions: `-ing` form of the verb — `TokenRefreshing`, `RouteResolving`, `EventDispatching`

**Subject protocols** (the type that receives/supports an action) — use `-able` suffix:
- `Playable`, `Configurable`, `Cacheable`, `Searchable`, `Validatable`

**General contracts** (not action-oriented) — use `-Providing` or descriptive name:
- `ThemeProviding`, `AnalyticsProviding`, `LogProviding`

### 1.2 Implementation Naming

- Implementation name = domain noun + role: `ProductFetchService`, `UserRepository`, `OrderCache`
- If protocol + one implementation share a file → file named after the implementation
  - e.g., `ProductFetchService.swift` contains `protocol ProductReading` + `final class ProductFetchService: ProductReading`

### 1.3 File Naming

- File name matches the primary type name: `ProductFetchService.swift`, `OrderDetailScreen.swift`
- Protocol + single implementation → one file, named after the implementation
- Additional conformers (decorators, adapters) → separate file each, named after the conformer
- Small helpers (<10 lines, or private/fileprivate) → stay in the source file
- New files go in the same directory as the source file unless a specific structure dictates otherwise
- Copy necessary `import` statements to each new file

## Phase 2: Identify Types Needing Frontmatter

- [ ] 2.1 Read each file
- [ ] 2.2 Find all top-level type declarations: `class`, `struct`, `protocol`, `enum`, `extension`
- [ ] 2.3 For each type, check if it already has a `/** solid-name:` or `/** solid-description:` block immediately above it
  - If yes → skip
  - If no → needs frontmatter

## Phase 3: Determine Metadata

For each type needing frontmatter:

- [ ] 3.1 **solid-name** — the type name (e.g., `GenericRow`, `ProductFetchService`)
- [ ] 3.2 **solid-category** — what the type **does** (domain role):
  - `abstraction` — used for any protocols, interfaces, generic type constraints
  - `network` — used for any API clients, request/response handling, endpoints
  - `viewmodel` — used for any presentation logic driving UI
  - `model` — used for any data models, DTOs, entities, value objects
  - `view-component` — used for reusable UI element (row, card, button, cell)
  - `screen` — used for full screen / page
  - `modifier` — used for full styling or behavior modifier
  - `crud` — used for full objects that reads, writes, updates, deletes data
  - `utility` — used for pure functions, formatters, helpers, and extensions that add convenience functionality (new methods, computed properties, static helpers) beyond protocol conformance
  - `navigation` — used for routing, coordinators, deep linking
  - `service` - anything that doesn't fall into any mentioned categories that can be qualified as business logic
  - `unit-test` — used for unit tests, test helpers, fixtures, shared test utilities for business logic
  - `ui-test` — used for UI tests, snapshot tests, accessibility tests

  Categories are extensible — use the closest match or introduce a new one if none fits.

- [ ] 3.3 **solid-stack** — frameworks/technologies this type uses. These feed directly into rule activation (e.g., `swiftui` activates SwiftUI review rules). Only include what the type actually imports or depends on:
  - `swiftui`, `uikit`, `appkit`
  - `combine`, `structured-concurrency`, `gcd`
  - `tca` (The Composable Architecture)
  - `core-data`, `swift-data`, `grdb`

  Omit if the type is pure Swift with no framework dependencies.

- [ ] 3.4 **solid-description** — keyword-rich description of what this type does, when to use it, and what problem it solves. Can be multiple sentences. Write it so that someone grepping for related concepts will find it — include domain terms, structural hints, and the key nouns that describe the type's purpose. This is the primary field used for discovery via grep.

  For protocols/interfaces, start with "Contract for..." or "Contract that defines...":
  - Good: "Contract for reading and fetching product data from remote or local sources. Supports pagination and filtering by category."
  - Good: "Contract that defines cacheable behavior. Types conforming to this can be stored in and retrieved from the app's cache layer."

  For implementations:
  - Good: "Compact expandable chip that renders a tool call with name, status, and collapsible detail panel. Used in lists and feeds to show inline tool invocation results."
  - Good: "Resolves a model ID string into a human-readable display name using a cached lookup table. Handles fallback for unknown model identifiers."

  Bad: "A view" / "A service" / "Handles data"

## Phase 4: Insert Frontmatter

- [ ] 4.1 For each type, insert a doc comment block **immediately before** the type declaration (before any attributes like `@Observable`, `@MainActor`, etc.):

```swift
/**
 solid-name: ProductReading
 solid-category: abstraction
 solid-description: Contract for reading product data from remote or local sources. Supports pagination and filtering by category.
 */
protocol ProductReading { ... }

/**
 solid-name: ProductFetchService
 solid-category: network
 solid-stack: [combine, structured-concurrency]
 solid-description: Fetches product data from the REST API. Implements pagination, category filtering, and response caching.
 */
final class ProductFetchService: ProductReading { ... }
```

- [ ] 4.2 Preserve existing doc comments — if a type already has `///` or `/** ... */` comments that are NOT solid-frontmatter, place the solid block above them.

## Phase 5: Output

- [ ] 5.1 List every type that received frontmatter
- [ ] 5.2 List types that were skipped (already had frontmatter)
- [ ] 5.3 Flag any naming convention violations found

## Constraints

- Do NOT modify any code logic — only insert doc comment blocks and flag naming issues
- Do NOT change existing doc comments or annotations
- Do NOT add frontmatter to private/fileprivate nested types — only top-level declarations
- Do NOT add frontmatter to extensions that merely add protocol conformance (e.g., `extension Foo: Codable {}`)
- DO add frontmatter (category: `utility`) to extensions that add convenience functionality — new methods, computed properties, static helpers, or subscripts beyond what a protocol requires
