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
</exceptions>
