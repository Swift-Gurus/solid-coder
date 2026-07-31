---
name: frontmatter
displayName: Frontmatter
category: practice
profile:
  - code
description: Write-time constraints requiring every type declaration to carry correct solid-frontmatter metadata. Language-agnostic.
bands:
  FM-1:
    missing_frontmatter_count:
      severe:
        greater_than_or_equal: 1
  FM-2:
    name_mismatch_count:
      severe:
        greater_than_or_equal: 1
  FM-3:
    invalid_category_count:
      severe:
        greater_than_or_equal: 1
  FM-4:
    incorrect_stack_count:
      severe:
        greater_than_or_equal: 1
  FM-5:
    bad_description_count:
      severe:
        greater_than_or_equal: 1
---

# Frontmatter

Write-time constraints ensuring every type carries `solid-` frontmatter and that each
field is correct. Mirrors `create-type`'s four metadata checks (name, category, stack,
description) plus presence. No review subagents — loaded only during code writing.

---

## Metrics

### FM-1: Missing solid-frontmatter on a type declaration

<definition id="FM-1" name="Missing Frontmatter">
solid-frontmatter is a structured doc-comment block (`solid-name`, `solid-category`,
optional `solid-stack`/`solid-spec`, `solid-description`) placed immediately above a
type declaration, in the language's doc-comment syntax (`/** ... */` in Swift, a
module-level docstring in Python). Every top-level type declaration must carry one.
</definition>

<detection id="FM-1" name="Missing Frontmatter">
For each top-level class, struct, protocol, enum, or member-adding extension declaration,
check the comment immediately preceding it for a solid-frontmatter block. Count each
declaration missing one. Do not count private/fileprivate helper types under 10 lines,
or extensions that only add protocol conformance with no new members.
</detection>

---

### FM-2: solid-name does not match the declared type

<definition id="FM-2" name="Name Mismatch">
`solid-name` is the frontmatter field naming the unit declared immediately below it —
it makes the type findable by name when grepping frontmatter blocks.
</definition>

<detection id="FM-2" name="Name Mismatch">
For each type with an existing frontmatter block, compare `solid-name` against the
actual declared type/class/struct/protocol/enum name. Count each mismatch.
</detection>

---

### FM-3: solid-category is invalid or blank

<definition id="FM-3" name="Invalid Category">
`solid-category` is a frontmatter field tagging the type with a single domain role
from a fixed vocabulary: `abstraction` (protocols, interfaces, generic type
constraints), `network` (API clients, request/response handling, endpoints),
`viewmodel` (presentation logic driving UI), `model` (data models, DTOs, entities,
value objects), `view-component` (reusable UI element — row, card, button, cell),
`screen` (full screen / page), `modifier` (styling or behavior modifier), `crud`
(object that reads, writes, updates, deletes data), `utility` (pure functions,
formatters, helpers, convenience extensions), `navigation` (routing, coordinators,
deep linking), `service` (business logic not covered above), `unit-test` (unit
tests, test helpers, fixtures), `ui-test` (UI, snapshot, accessibility tests).
</definition>

<detection id="FM-3" name="Invalid Category">
For each type with an existing frontmatter block, check `solid-category` against the
vocabulary above. A category outside this list is acceptable only if it clearly names
a distinct domain role by the same convention (lowercase, hyphenated, noun-like).
Blank, placeholder ("TODO"), or vague values ("misc", "other", "stuff") count as
violations. Count each violation.
</detection>

---

### FM-4: solid-stack is incomplete or incorrect

<definition id="FM-4" name="Incorrect Stack">
`solid-stack` is a frontmatter field tagging the frameworks/technologies the type
actually imports or depends on, from a fixed vocabulary: `swiftui`, `uikit`, `appkit`,
`combine`, `structured-concurrency`, `gcd`, `tca` (The Composable Architecture),
`core-data`, `swift-data`, `grdb`. These tags feed directly into rule activation
(e.g. `swiftui` activates SwiftUI review rules) and are omitted entirely when the
type is pure language with no framework dependency.
</definition>

<detection id="FM-4" name="Incorrect Stack">
For each type with an existing frontmatter block, compare `solid-stack` against the
type's actual imports/usages. Flag: a listed entry the code doesn't import/use, or a
clear dependency on one of the fixed-vocabulary technologies that is missing from the
list. Do not flag omission of `solid-stack` entirely when the type has no framework
dependency — that is correct, not a violation. Count each violation.
</detection>

---

### FM-5: solid-description violates the description-quality rules

<definition id="FM-5" name="Bad Description">
`solid-description` is a keyword-rich frontmatter field describing what the type
does, when to use it, and what problem it solves — written so that someone grepping
for related concepts finds it. It is the primary field used for discovery via grep.
</definition>

<detection id="FM-5" name="Bad Description">
For each type with an existing frontmatter block, check `solid-description`:
- Must describe the CAPABILITY at the interface level — ask "would this sentence still
  be true if the implementation changed entirely?" If not, it's implementation, not capability.
- Must NOT name any concrete implementation thing: types, variables, APIs, values,
  colors, layout details, composition steps, wiring to other components.
- Must NOT be vague: "A view", "A service", "Handles data" with no substance.
- For `abstraction` category: MUST start with "Contract for..." or "Contract that defines...".
Count each frontmatter block whose description fails any of the above.
</detection>

---

## Quantitative Metrics Summary

| ID   | Metric                    | Threshold | Severity  |
|------|----------------------------|-----------|-----------|
| FM-1 | Missing frontmatter count  | 0         | COMPLIANT |
| FM-1 | Missing frontmatter count  | >= 1      | SEVERE    |
| FM-2 | Name mismatch count        | 0         | COMPLIANT |
| FM-2 | Name mismatch count        | >= 1      | SEVERE    |
| FM-3 | Invalid category count     | 0         | COMPLIANT |
| FM-3 | Invalid category count     | >= 1      | SEVERE    |
| FM-4 | Incorrect stack count      | 0         | COMPLIANT |
| FM-4 | Incorrect stack count      | >= 1      | SEVERE    |
| FM-5 | Bad description count      | 0         | COMPLIANT |
| FM-5 | Bad description count      | >= 1      | SEVERE    |
