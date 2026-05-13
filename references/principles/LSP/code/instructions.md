---
name: lsp-code
type: code
---

# LSP Coding Instructions

These are mandatory rules that must be followed when writing code. Check each rule before writing — if any gate fails, stop and redesign before proceeding.

---

<rule id="LSP-1" name="No Type Checks Against Abstractions">
Before writing `is`, `as?`, `as!`, or `type(of:)` against a concrete type:
- This means the abstraction is wrong — the caller knows about subtypes it should not care about.
- Stop. Redesign: move the type-specific behavior into the type itself via a protocol method, and call that instead.
- Exception: the type being checked is external (not found in the project, local packages, or local frameworks) — framework-forced casts are acceptable.
</rule>

<rule id="LSP-2" name="Honor the Base Contract in Overrides">
Before writing an `override` method in a subclass:
- Do NOT add new guard clauses or preconditions that the base method does not have — this strengthens the precondition and breaks substitutability.
- Do NOT remove or relax guarantees the base method provides — this weakens the postcondition.
- Do NOT expose or bypass invariants the base class protects (e.g., turning `private(set)` state into a writable property).
- The override must be a drop-in replacement — any caller using the base type must get correct behavior with the subtype.
</rule>

<rule id="LSP-3" name="No Empty or Crashing Protocol Implementations">
Before leaving a protocol method with an empty body or a crash assertion:
- Empty body `{}` or `fatalError` / `preconditionFailure` means this conformer cannot fulfill the contract.
- Stop. The protocol is too wide for this conformer — either split the protocol (apply ISP) or reconsider the conformance.
- Exception: NoOp objects — a type explicitly named as NoOp where 100% of methods are intentionally empty (used as a null object or test stand-in). This is a known pattern, not a violation.
</rule>

<exceptions>
- Framework-forced casts — `as? HTTPURLResponse`, `as NSError`, `as? UIView` — the framework API requires this and the type is not developer-owned.
- NoOp objects — type name explicitly states NoOp and every method is intentionally empty. Compliant by design.

Validate noted violations:
- MINOR (empty non-fatal methods < 50% of protocol requirements) → Proceed with caution.
- SEVERE (1+ type check against owned type, 1+ contract violation in override, 1+ `fatalError` method, OR empty methods ≥ 50%) → Do not write it this way. Use loaded fix instructions.
</exceptions>
