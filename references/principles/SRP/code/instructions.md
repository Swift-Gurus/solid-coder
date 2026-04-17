---
name: srp-code
type: code
---

# SRP Coding Instructions

Every method or property you add to a type may introduce a second responsibility. Run this checklist twice — once before writing (plan your approach) and once after writing (verify what you wrote).

---

## Before Adding Functionality to a Type

```
You are about to add a method or property to a type.
         │
         ▼
SRP-1: Name the verb — what does this functionality actually do?
    (fetches, parses, persists, validates, formats, sends, caches, logs)
    Count total distinct verbs on the type including the new one.
         │
         ▼
SRP-2: Which instance variables does this functionality use?
    Check against existing cohesion groups — does it join an existing group
    or create a new disjoint set?
    Note the cohesion group count.
         │
         ▼
SRP-3: Who would request changes to this functionality?
    Name the stakeholder. Check against existing stakeholders on the type.
    Note the stakeholder count.
         │
         ▼
Does this functionality fall into an exception? (see rule.md Exceptions)
    YES → Note it. Not a violation.
    NO  → Continue ▼
         │
         ▼
Validate verb count + cohesion groups + stakeholders against severity bands in rule.md:
    COMPLIANT or MINOR → Proceed.
    SEVERE             → Do not add it here. Use fix approach below.
```

## When SEVERE — Restructure

Do not add the functionality here. Use the loaded fix instructions to restructure the type.

## When Designing a New Type

Before writing the first line:

1. **State the responsibility in one verb phrase** — "fetches products", "persists user data"
2. **If you need two verbs** (e.g., "fetches and caches") → that's likely two types
3. **List the instance variables** — if they fall into disjoint groups, split before writing

## Exceptions — Not Violations

These are defined in rule.md. Do not expand this list.
