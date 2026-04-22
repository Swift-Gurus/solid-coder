---
name: code-smells-code
type: code
---

# Code Smells — Write-Time Constraints

Hard rules to apply whenever you write or modify Swift code. Treat each rule as a constraint, not a suggestion. If you feel tempted to break one, that's usually a design signal — redesign the approach.

---

## CS-1: Do NOT use `static` functions/varialbes

- Don't use static methods/vars/getter to split logic nor to have any logic, unless you have instructions from the user


### Exeption for CS-1
- Constants 
- Instead of using factory methods ont the type use convenience init

---

