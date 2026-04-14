---
name: testing-code
type: code
---

# Unit Testing Coding Instructions

Every test method you write must be validated against the testing metrics. Run this checklist twice — once before writing (plan your approach) and once after writing (verify what you wrote).

---

## For Every Test Method You Write

```
You wrote or are writing a test method.
         │
         ▼
TEST-1: Is the test isolated?
    Note isolation violations.
         │
         ▼
TEST-2: Is the test well-structured?
    Note structure violations.
         │
         ▼
TEST-3: Is the name descriptive?
    Note naming violations.
         │
         ▼
TEST-4: Are test doubles appropriate?
    Note test double violations.
         │
         ▼
TEST-5: Is the setup clean?
    - Is SUT construction repeated inline across multiple tests?
    Note setup complexity violations.
         │
         ▼
TEST-6: Are you using the right framework?
    Note framework violations.
         │
         ▼
Does the test fall into an exception? (see rule.md Exceptions)
    YES → Note it. Not a violation.
    NO  → Continue ▼
         │
         ▼
Validate all noted violations against severity bands in rule.md:
    COMPLIANT or MINOR → Proceed.
    SEVERE             → Do not leave it this way. Use loaded fix instructions to adjust.
```

## Exceptions — Not Violations

These are defined in rule.md. Do not expand this list.
