---
name: code-smells-code
type: code
---

# Code Smells — Write-Time Constraints

These are mandatory rules that must be followed when writing code. Treat each rule as a hard constraint, not a suggestion. If you feel tempted to break one, that is usually a design signal — redesign the approach instead.

---

<rule id="CS-1" name="No Static Functions or Variables">
- Do not use static methods, vars, or getters to split logic or hold any logic.
- Use instance methods and dependency injection instead.
Note any static logic violations.
</rule>

<exceptions>
- Constants — `static let` for true constants is allowed.
- Use convenience `init` instead of static factory methods on the type.
- Build system / DSL files — files whose entire purpose is configuring a build system or describing a package manifest using an external SDK's prescribed DSL (e.g., Tuist `ProjectDescription`, SwiftPM `Package.swift`, Fastfile). These DSLs mandate static factory methods as their API surface — using them as directed is not a CS-1 violation. Signals: file imports `ProjectDescription`, `PackageDescription`, or similar build SDK; file is named `Project.swift`, `Package.swift`, `Workspace.swift`, or lives under a `Tuist/` directory.
</exceptions>
