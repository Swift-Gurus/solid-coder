---
name: isp-code
type: code
---

# ISP Coding Instructions

These are mandatory rules that must be followed when writing protocols. Check each rule before writing — if any gate fails, stop and redesign before proceeding.

---

<rule id="ISP-1" name="Keep Protocols Narrow">
Before declaring a new protocol or adding a requirement to an existing one:
- Ask: will every conformer need to provide a real implementation of this?
- YES → proceed.
- NO (some conformers would leave it empty, stub it, or throw `fatalError`) → do not add it here. It belongs in a separate role protocol.
- Target: 5 requirements or fewer per protocol. Reaching 6+ is a signal to reconsider the design.
</rule>

<rule id="ISP-2" name="Split by Usage Groups">
Before declaring a protocol with multiple methods:
- Group the methods by which conformers would actually use them together.
- One group → single protocol, proceed.
- Two or more disjoint groups → split into separate role protocols and compose: `protocol P: A, B {}`.
- Prefer `protocol P: A, B {}` over `typealias P = A & B` — a typealias cannot be conformed to directly, which breaks decorator and adapter patterns that need a single nominal type.
</rule>

<rule id="ISP-3" name="Consumers Depend on the Narrowest Protocol">
Before declaring a dependency on a protocol:
- Ask: does the consumer actually use all the methods of this protocol?
- YES → proceed.
- NO → depend on a narrower role protocol that only declares what this consumer needs.
</rule>

<exceptions>
- Marker protocols — zero-requirement protocols used for type discrimination (e.g., `Sendable`, `Identifiable`). Always compliant.
- Composition protocols — `protocol P: A, B {}` where A and B are already narrow. The composition is not a violation.
- `@objc` protocols — method sets may be dictated by the framework.
- Test doubles — mocks, stubs, and fakes intentionally implement only a subset. Low coverage in test conformers is expected and not a violation.
- Protocols with default implementations — if non-implemented methods have protocol extension defaults, conformers are not forced. Not a violation.
</exceptions>
