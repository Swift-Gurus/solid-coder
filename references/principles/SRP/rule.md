---
name: srp
displayName: Single Responsibility Principle
category: solid
description: Verb counting and cohesion group analysis with direct severity scoring
required_patterns:
  - structural/facade
---

# Single Responsibility Principle (SRP)

> A class should have only one reason to change. — Robert C. Martin
---

## The SRP Metrics Framework

This framework provides objective scoring for SRP compliance. The primary                                                                                                                                                                                                                                                                                
metrics are verb count and cohesion group analysis — both directly observable
from code. Stakeholder labels are derived from confirmed structural findings
for reporting purposes.

## Metric:

### SRP-1: Verb count

List every distinct action (verb) the class performs. Not method names — what it actually *does*

**Detection:**

Count the distinct actions (verbs) the class performs. Not method names — what it actually *does*.

1. **Read every method** (skip init/deinit/factory methods) and extract the verb (what it does, not what it's called)
2. **List all verbs** — do NOT merge or deduplicate synonyms (merging introduces bias)
3. **Count distinct verbs**

Example verbs: reads, writes, validates, calculates, sends, logs, persists, transforms, notifies

**Result:** Raw verb count used in scoring and cross-referenced with SRP-2.

### SRP-2: **Cohesion Groups** (methods using disjoint variable sets)

**Definition:** A class is cohesive when its methods manipulate its variables. High cohesion = most methods use most variables.

**From Clean Code Chapter 10:**
> "In general the more variables a method manipulates the more cohesive that method is to its class. A class in which each variable is used by each method is maximally cohesive."


**Detection:** Sets of methods that use the same instance variables

- **Bridge Method Rule Case:** 
If a single method accesses variables from two otherwise disjoint sets, it is an **orchestrator** — not a unifier.
Remove it from the graph, count the remaining components. If 2+ components exist, count those as separate cohesion groups. The bridge
method itself belongs to whichever group it primarily coordinates, or is reported separately as an orchestration concern.

See `Examples/` for violation and compliant code samples demonstrating cohesion groups and bridge methods.

### SRP-3: Stakeholder count (additional gate)

A class/function/struct/module/instance should have one reason to change

**Detection:**

A "reason to change" is a **distinct stakeholder** who could independently require modification.

#### The Stakeholder Test

Ask: "Who would request this change?"

| Stakeholder/Force | Example Change Request |
|-------------------|------------------------|
| DBA / Data Team | "Switch from PostgreSQL to MongoDB" |
| UX Designer | "Change the output format" |
| Business Analyst | "Update the validation rules" |
| Security Team | "Change how we log sensitive data" |
| DevOps | "Switch from file storage to S3" |
| Product Owner | "Add a new business rule" |

If different stakeholders could independently request changes to the same class → **multiple responsibilities**.

### Exceptions(NOT violations):
1. **Facade / Coordinator** (see @facade.md)
   A class that only coordinates protocol-typed subsystems has one responsibility: coordination.

   Check the Facade Recognition Conditions (ALL must hold):
    1. Every stored property / init parameter is protocol-typed
    2. Every method body is pure delegation — no business logic, no branching on own mutable state
    3. Class creates no objects internally — all dependencies injected via init
   If ALL conditions hold: cohesion groups = 1 (coordination), final severity = COMPLIANT

### Severity Bands:
- ✅ **COMPLIANT** (1 cohesion group, 1-2 verbs)
- ⚠️ **MINOR** (1 cohesion group, 3+ verbs, 1 stakeholder — no action, keep an eye on it)
- 🔥 **SEVERE** (any of the following):
    - 2+ cohesion groups (structural proof — always SEVERE)
    - 3+ verbs + 2+ stakeholders (cross-check escalation)
---

## Quantitative Metrics Summary
| ID    | Metric          | Threshold                        | Severity  |
|-------|-----------------|----------------------------------|-----------|
| SRP-0 | Exception       | falls into exception category    | COMPLIANT |
| SRP-1 | Verbs           | 1-2 verbs, 1 group               | COMPLIANT |
| SRP-1 | Verbs           | 3+ verbs, 1 group, 1 stakeholder | MINOR     |
| SRP-1 | Verbs           | 3+ verbs, 2+ stakeholders        | SEVERE    |
| SRP-2 | Cohesion groups | 2+ groups                        | SEVERE    |
---

<definition id="SRP-1" name="Verb Count">
A verb is a distinct action the class performs — what it actually *does*, not what a method is called. Count distinct verbs extracted from all non-init/deinit/factory methods. The verb count measures how many distinct responsibilities are expressed through behaviour.
</definition>

<detection id="SRP-1">
1. Read every method (skip init/deinit/factory methods) and extract the verb — what it actually does, not the method name.
2. List all verbs — do NOT merge or deduplicate synonyms.
3. Count distinct verbs.
Metric keys: verb_count (integer), cohesion_groups (integer), stakeholder_count (integer).
</detection>

<severity-bands id="SRP-1">
<band severity="COMPLIANT"><condition>verb_count &lt;= 2 and cohesion_groups == 1</condition></band>
<band severity="MINOR"><condition>verb_count &gt;= 3 and cohesion_groups == 1 and stakeholder_count &lt;= 1</condition></band>
<band severity="SEVERE"><condition>verb_count &gt;= 3 and stakeholder_count &gt;= 2</condition></band>
</severity-bands>

<definition id="SRP-2" name="Cohesion Groups">
A cohesion group is a set of methods that share the same instance variables. Disjoint variable sets indicate multiple responsibilities. Apply the Bridge Method Rule: if a single method accesses variables from two otherwise disjoint sets, it is an orchestrator — remove it from the graph, count remaining components.
</definition>

<detection id="SRP-2">
1. Build a method-variable access matrix: for each method, record which instance variables it reads or writes.
2. Group methods into clusters that share at least one variable.
3. Apply Bridge Method Rule: if one method connects two otherwise-disjoint groups, remove it and count the remaining components.
4. Count the number of resulting cohesion groups.
Metric keys: cohesion_groups (integer).
</detection>

<severity-bands id="SRP-2">
<band severity="COMPLIANT"><condition>cohesion_groups &lt;= 1</condition></band>
<band severity="SEVERE"><condition>cohesion_groups &gt;= 2</condition></band>
</severity-bands>

<definition id="SRP-3" name="Stakeholder Count">
A stakeholder is a distinct person or team who could independently request a change to this class. Different stakeholders represent different reasons to change, which is the core SRP violation signal.
</definition>

<detection id="SRP-3">
Ask "Who would request this change?" for each group of methods. Count distinct stakeholder types (DBA, UX Designer, Business Analyst, Security Team, DevOps, Product Owner, etc.).
Metric keys: stakeholder_count (integer).
</detection>

<severity-bands id="SRP-3">
<band severity="COMPLIANT"><condition>stakeholder_count &lt;= 1</condition></band>
<band severity="MINOR"><condition>stakeholder_count == 1</condition></band>
<band severity="SEVERE"><condition>stakeholder_count &gt;= 2</condition></band>
</severity-bands>

<exceptions>
1. Facade / Coordinator — a class whose every dependency is protocol-typed, every method is pure delegation with no business logic, and no objects are constructed internally. Its single responsibility is coordination. Final severity: COMPLIANT regardless of verb or cohesion counts.
</exceptions>

