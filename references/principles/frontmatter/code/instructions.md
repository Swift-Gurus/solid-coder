---
name: frontmatter-code
type: code
---

# Frontmatter — Write-Time Constraints

Hard rules. If you feel tempted to break one, that is a design signal — go back and
fix the frontmatter instead. Mirrors `create-type`'s four metadata checks.

---

<rule id="FM-1" name="Every Type Declaration Needs solid-frontmatter">
Before finishing a top-level class, struct, protocol, enum, or member-adding
extension — stop. Add a solid-frontmatter doc comment immediately above the
declaration (`solid-name`, `solid-category`, optional `solid-stack`/`solid-spec`,
`solid-description`). Use skill **solid-coder:create-type** to apply the naming
and frontmatter conventions before finishing the file.
</rule>

<exceptions id="FM-1">
- Private/fileprivate helper types under 10 lines — allowed without frontmatter.
- Extensions that only add protocol conformance with no new members.
</exceptions>

---

<rule id="FM-2" name="solid-name Must Match the Declared Type">
Before finishing a type's frontmatter — check that `solid-name` is exactly the
declared type's name, not an old name, abbreviation, or unrelated string.
</rule>

<exceptions id="FM-2">
- None.
</exceptions>

---

<rule id="FM-3" name="solid-category Must Be a Real Domain Role">
Before finishing a type's frontmatter — check that `solid-category` is not blank
and is one of: `abstraction`, `network`, `viewmodel`, `model`, `view-component`,
`screen`, `modifier`, `crud`, `utility`, `navigation`, `service`, `unit-test`,
`ui-test` — or another category that clearly names a distinct domain role by the
same convention. Never leave it blank, "TODO", or vague ("misc", "other").
</rule>

<exceptions id="FM-3">
- None.
</exceptions>

---

<rule id="FM-4" name="solid-stack Must Match Actual Dependencies">
Before finishing a type's frontmatter — check `solid-stack` against what the type
actually imports/depends on from: `swiftui`, `uikit`, `appkit`, `combine`,
`structured-concurrency`, `gcd`, `tca`, `core-data`, `swift-data`, `grdb`. Add
entries for dependencies present; remove entries for frameworks not used. Omit
the field entirely for pure-language types with no framework dependency.
</rule>

<exceptions id="FM-4">
- None.
</exceptions>

---

<rule id="FM-5" name="solid-description Must Be Capability-Level">
Before finishing a type's frontmatter — write `solid-description` as one
concise, keyword-rich sentence (or few sentences) at the capability level: what
the type does, when to use it, what problem it solves. Do not name concrete
implementation details (types, variables, APIs, values, wiring). Do not write
something vague ("A view", "A service", "Handles data"). For `abstraction`
category, start with "Contract for..." or "Contract that defines...".
</rule>

<exceptions id="FM-5">
- None.
</exceptions>
