---
name: code-smells
displayName: Code Smells
category: practice
profile:
  - code
description: Write-time constraints against structural anti-patterns. Language-agnostic.
---

# Code Smells

Write-time constraints that prevent structural anti-patterns regardless of language.
No review subagents — loaded only during code writing.

---

## Metrics

### CS-1: Static logic used to split responsibilities

<definition id="CS-1" name="Static Logic">
Static functions, class methods, or module-level functions used to hold or split
business logic across a type — not constants, not a build-system DSL.
</definition>

<detection id="CS-1" name="Static Logic">
Count static or class methods that contain business logic (branching, construction,
transformation). Exclude pure constants and build-system DSL files.
</detection>

<severity-bands id="CS-1">
  <band severity="COMPLIANT"><condition>static_logic_count == 0</condition></band>
  <band severity="SEVERE"><condition>static_logic_count >= 1</condition></band>
</severity-bands>

---

### CS-2: Multiple class or struct definitions in one file

<definition id="CS-2" name="Multiple Types Per File">
Count of distinct class or struct definitions in a single source file, excluding
private extensions that exist solely to support the file's primary type.
</definition>

<detection id="CS-2" name="Multiple Types Per File">
Count top-level class and struct declarations in the file. Private extensions
scoped to the file's primary type do not count as separate types.
</detection>

<severity-bands id="CS-2">
  <band severity="COMPLIANT"><condition>class_struct_count <= 1</condition></band>
  <band severity="SEVERE"><condition>class_struct_count >= 2</condition></band>
</severity-bands>

---

## Quantitative Metrics Summary

| ID   | Metric                  | Threshold          | Severity  |
|------|-------------------------|--------------------|-----------|
| CS-1 | Static logic count      | 0                  | COMPLIANT |
| CS-1 | Static logic count      | >= 1               | SEVERE    |
| CS-2 | Class/struct count      | <= 1               | COMPLIANT |
| CS-2 | Class/struct count      | >= 2               | SEVERE    |
