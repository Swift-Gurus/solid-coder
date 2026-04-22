---
name: ocp-code
type: code
---

# OCP Coding Instructions

Every dependency, API call, or object creation is a potential sealed variation point. Run this checklist twice — once before writing (plan your approach) and once after writing (verify what you wrote).

---

## Before Adding a Dependency

```
You are about to add a dependency (property, call, construction).
         │
         ▼
OCP-1: Classify the dependency:
    ABSTRACT (protocol-typed and injected)
       → Not a sealed point. Proceed.
    DIRECT → Continue ▼
         │
         ▼
Is it INJECTED or NON-INJECTED?
    INJECTED (passed via init, factory method, or default parameter)
       → Note it. Check testability (OCP-2): can the consumer be tested
         by substituting this dependency?
         YES → Note as testable.
         NO  → Note as untestable.
    NON-INJECTED (constructed internally, singleton, static access)
       → This is a sealed variation point. Continue ▼
         │
         ▼
Does it fall into an exception? (see rule.md Exceptions)
    YES → Note it. Not a sealed point.
    NO  → Note as sealed point. Continue ▼
         │
         ▼
Validate sealed point count + testability against severity bands in rule.md:
    COMPLIANT or MINOR → Proceed.
    SEVERE             → Do not write it this way. Use fix approach below.
```

## When SEVERE — Resolve

Use the loaded fix instructions to resolve the sealed variation point.

---

## Protocol & File Conventions

- Protocol + primary implementation → same file, named after the implementation
- Additional conformers → separate files, named after the conformer
- Always search the project for existing protocols before creating new ones

