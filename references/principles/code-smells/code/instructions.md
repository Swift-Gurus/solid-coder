---
name: code-smells-code
type: code
---

# Code Smells — Write-Time Constraints

Hard rules. If you feel tempted to break one, that is a design signal — redesign the approach instead.

---

<rule id="CS-1" name="No Static Logic for Splitting Responsibilities">
Do not use static methods, class methods, or module-level functions to hold or
split business logic across a type.

Fix:
- If the caller always needs the same defaults → add a convenience init with
  default arguments on the concrete type.
- If callers need different configurations → extract a dedicated factory type
  that owns construction logic as instance methods.

Do NOT create a static factory method on the type itself.
</rule>

<exceptions id="CS-1">
- True constants (static let, module-level constants) — allowed.
- Build system / code-generator DSL files — files whose sole purpose is
  configuring a build system or describing a package manifest using an external
  SDK's prescribed DSL (e.g. Tuist ProjectDescription, SwiftPM Package.swift,
  Fastfile, CMakeLists, Makefile helpers, code-gen scripts). These DSLs mandate
  static or module-level functions as their prescribed API surface.
</exceptions>

---

<rule id="CS-2" name="One Class or Struct Per File">
A file must contain at most one class or struct definition.

Fix: move each additional class or struct into its own file named after the type.
</rule>

<exceptions id="CS-2">
- Private extensions in the same file that exist solely to support the file's
  primary type (internal implementation helpers, not reusable outside the file).
</exceptions>
