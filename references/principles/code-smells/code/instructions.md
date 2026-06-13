---
name: code-smells-code
type: code
---

# Code Smells — Write-Time Constraints

Hard rules. If you feel tempted to break one, that is a design signal — redesign the approach instead.

---

<rule id="CS-1" name="No Static Logic for Splitting Responsibilities">
Before writing a static method, class method, or module-level function that contains
business logic — stop. Use an instance method or extract a factory type instead.

- Caller always needs the same defaults → add a convenience init with default arguments.
- Callers need different configurations → extract a dedicated factory type.
</rule>

<exceptions id="CS-1">
- True constants (static let, module-level constants) — allowed.
- Build system / code-generator DSL files — files whose sole purpose is configuring
  a build system (e.g. Tuist ProjectDescription, SwiftPM Package.swift, Fastfile).
</exceptions>

---

<rule id="CS-2" name="One Class or Struct Per File">
Before defining a second class or struct in a file — stop.
Move it to its own file named after the type.
</rule>

<exceptions id="CS-2">
- Private extensions that exist solely to support the file's primary type.
</exceptions>

---

<rule id="CS-3" name="No Inline Type Definitions Inside Function Scopes">
Before defining a class, struct, enum, interface, or protocol inside a function
or method body — stop. Move it to file scope with a descriptive name,
or use an existing mock/stub framework.
</rule>

<exceptions id="CS-3">
- Anonymous closures and lambdas are not type definitions — allowed.
- Build system / code-generator DSL files (same exception as CS-1).
</exceptions>
