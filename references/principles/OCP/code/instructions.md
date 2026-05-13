---
name: ocp-code
type: code
---

# OCP Coding Instructions

These are mandatory rules that must be followed when writing code. Check each rule before writing — if any gate fails, stop and redesign before proceeding.

---

<rule id="OCP-1" name="No Hardcoded Dependencies">
Before using any concrete type (property, method call, object creation) inside a type:
- Ask: can this be swapped for a different implementation without modifying this file?
- YES (it is injected as a protocol-typed parameter) → proceed.
- NO (it is instantiated internally, accessed via `.shared`, `.default`, or a static call) → do not write it this way. Make it injectable via a protocol instead.
</rule>

<rule id="OCP-2" name="Injectable Dependencies Must Be Testable">
Before injecting a concrete (non-protocol) type:
- Ask: can tests substitute this dependency?
- Non-final class or class that can conform to a protocol → define a protocol, add conformance via extension, inject the protocol.
- Final class / enum with static members only / global function → wrap in an adapter struct that conforms to a protocol, inject the protocol.
- The goal: the consumer never names a concrete type — only the protocol.
</rule>

<rule id="OCP-3" name="Reuse Existing Protocols">
Before creating a new protocol:
- Search the project for an existing protocol covering this behavior.
- Exact or extensible match found → use or extend it, do not create a duplicate.
- Protocol + primary implementation → same file, named after the implementation.
- Additional conformers → separate files, named after the conformer.
</rule>

<exceptions>
- Factories / Builders — their job is to construct concrete objects. Internal construction is expected.
- Helpers — Encoders, Formatters, Locks, Queues, threading utilities with no business logic dependencies.
- Pure data structures — structs or classes with only stored properties, no behavior, no dependencies.
- Test code — unit tests, mocks, stubs, and test helpers are exempt. Test code intentionally uses concrete types.

If a dependency falls into an exception, proceed without wrapping it in a protocol.
</exceptions>
