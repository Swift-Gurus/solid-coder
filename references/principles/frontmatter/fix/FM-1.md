<fix id="FM-1" name="Missing solid-frontmatter">

<trigger>
One or more top-level type declarations (class, struct, protocol, enum, or a
member-adding extension) have no solid-frontmatter block immediately above them.
</trigger>

<strategy severity="SEVERE">
For each type missing frontmatter, insert a doc comment block immediately before
the declaration (before any attributes like `@Observable`, `@MainActor`), using
the language's doc-comment syntax (`/** ... */` in Swift, a module-level
triple-quoted string in Python):

```swift
/**
 solid-name: <TypeName>
 solid-category: <category>
 solid-description: <one capability-level sentence>
 */
```

**solid-category** — pick the closest match:
- `abstraction` — protocols, interfaces, generic type constraints
- `network` — API clients, request/response handling, endpoints
- `viewmodel` — presentation logic driving UI
- `model` — data models, DTOs, entities, value objects
- `view-component` — reusable UI element (row, card, button, cell)
- `screen` — full screen / page
- `modifier` — styling or behavior modifier
- `crud` — object that reads, writes, updates, deletes data
- `utility` — pure functions, formatters, helpers, extensions adding convenience methods
- `navigation` — routing, coordinators, deep linking
- `service` — business logic that doesn't fit any category above
- `unit-test` — unit tests, test helpers, fixtures
- `ui-test` — UI tests, snapshot tests, accessibility tests

Add `solid-stack: [swiftui, combine, ...]` only for frameworks the type actually
imports/depends on — omit if pure language with no framework dependency.

**solid-description** — one concise sentence describing the CAPABILITY, not the
implementation. Must not name concrete types, variables, values, or wiring.
For `abstraction` category, start with "Contract for..." or "Contract that defines...".
Bad: "A view" / "A service" / "Handles data".
</strategy>

<diagnosis>
List every top-level type declaration in the file lacking a preceding solid-frontmatter
block. Skip private/fileprivate helper types under 10 lines and extensions that only
add protocol conformance with no new members.
</diagnosis>

<todo>
- [ ] List all type declarations missing frontmatter from the findings
- [ ] For each: determine solid-category from the list above
- [ ] For each: determine solid-stack (omit if pure language, no framework dependency)
- [ ] Write a one-sentence, capability-level solid-description (no implementation detail)
- [ ] Insert the frontmatter block immediately above each declaration
- [ ] Verify: every top-level type in the file now has a frontmatter block
</todo>

<suggested_fix_must_include>
- The exact frontmatter block inserted for each type
- The category chosen and a one-line reason it fits
</suggested_fix_must_include>

</fix>
