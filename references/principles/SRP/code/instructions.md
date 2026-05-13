---
name: srp-code
type: code
---

# SRP Coding Instructions

These are mandatory rules that must be followed when writing code. Check each rule before writing — if any gate fails, stop and redesign before proceeding.

---

<rule id="SRP-1" name="One Responsibility">
Before creating a new type, complete this sentence: "This type ___s [domain noun]."
- One verb phrase that names what it actually *does* (not just what it's called) → proceed.
- Two or more verb phrases needed → split into separate types before writing.
</rule>

<rule id="SRP-2" name="Shared Fields">
Before adding a method to an existing type, look at what it actually does (not its name) and which instance fields it uses:
- Uses the same fields as existing methods → proceed.
- Needs its own separate fields that existing methods don't touch → it belongs in a different type.
- Touches fields from two otherwise unrelated groups of methods → it is a bridge/orchestrator. The type should be split; the bridging method becomes a Facade coordinating the two.
</rule>

<rule id="SRP-3" name="Stakeholder Check">
Before adding a method, ask: "Who would request a change to this?"
- Same stakeholder as the existing methods (same team, same reason to change) → proceed.
- Different stakeholder (different team, different domain, different reason to change) → it belongs in a different type.
</rule>

<rule id="SRP-4" name="Delegation over Implementation">
Before implementing logic that belongs to another concern:
- Stop. Extract a protocol for that concern and inject it instead.
- Never implement a second concern inline — coordinate via a dependency.
</rule>

<exceptions>
- Facade / Coordinator — a type whose every dependency is protocol-typed and whose every method is pure delegation (no logic, no construction, no transformation). Its single responsibility is coordination. Proceed.
</exceptions>
