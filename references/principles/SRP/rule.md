---
name: srp
displayName: Single Responsibility Principle
category: solid
description: Verb counting and cohesion group analysis with direct severity scoring
required_patterns:
  - structural/facade
bands:
  SRP-1:
    verb_count:
      minor:
        greater_than_or_equal: 3
      severe:
        greater_than: 5
  SRP-2:
    cohesion_groups:
      severe:
        greater_than_or_equal: 2
  SRP-3:
    stakeholder_count:
      severe:
        greater_than_or_equal: 2
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

<definition id="SRP-1" name="Verb Count">
List every distinct action (verb) the class performs. Not method names — what it actually *does*
</definition>

<detection id="SRP-1" name="Verb Count">
Measure the distinct responsibilities expressed as action verbs by the supplied unit. Apply this procedure exactly:

1. Ignore initializers, deinitializers, and factory methods.
2. For every remaining method, identify one primary externally meaningful action that describes the method's complete outcome.
3. Calls, branches, fallbacks, collection operations, cache operations, formatting primitives, and storage primitives that merely implement that outcome are not additional actions.
4. Add another action for a method only when it performs an independently changeable responsibility that is not required to achieve its primary outcome.
5. Keep distinct primary actions from different methods distinct. Do not merge them merely because their labels are synonyms.
6. Before submitting, build one evidence entry per counted action containing the method, action, and rationale. `verb_count` must equal the number of evidence entries. Submit only the metric fields required by the output schema.

Example: a load method that checks a cache and falls back to storage performs the single action "load"; cache lookup and storage lookup are implementation details. A save method that invalidates its cache performs the single action "save" when invalidation is required to keep the saved result consistent.
</detection>

### SRP-2: **Cohesion Groups** (methods using disjoint variable sets)

<definition id="SRP-2" name="Cohesion Groups">
A class is cohesive when its methods manipulate its variables. High cohesion = most methods use most variables.

**From Clean Code Chapter 10:**
> "In general the more variables a method manipulates the more cohesive that method is to its class. A class in which each variable is used by each method is maximally cohesive."
</definition>

<detection id="SRP-2" name="Cohesion Groups">
Measure cohesion groups in the supplied unit. Apply this procedure exactly:

1. Ignore lifecycle methods and list which instance variables each remaining method directly uses.
2. Connect methods when they share an instance variable, including transitive connections, and form the resulting method groups.
3. Do not remove a method merely because it uses variables from both sides of a group. Remove it as an orchestrator only when it coordinates independently meaningful operations. A method that needs all of those variables to produce one cohesive result is not an orchestrator and keeps the group connected.
4. A cache and its backing storage belong to the same data-access group when the methods use them together to provide consistent save/load/invalidate behavior.
5. Formatting machinery and presentation templates belong to the same presentation group when methods combine them to produce rendered output.
6. Before submitting, build one evidence entry per group containing its methods, variables, and rationale. `cohesion_groups` must equal the number of evidence entries. Submit only the metric fields required by the output schema.
</detection>

### SRP-3: Stakeholder count (additional gate)

<definition id="SRP-3" name="Stakeholder Count">
A class/function/struct/module/instance should have one reason to change
</definition>

<detection id="SRP-3" name="Stakeholder Count">
Measure distinct stakeholders who could independently request changes to the supplied unit. Apply this procedure exactly:

1. Count change-driving concerns demonstrated by the unit's behavior, not every framework type, dependency, implementation mechanism, or hypothetical team.
2. Merge backing storage, caching, and cache consistency into one data-access stakeholder when they jointly implement retrieval and persistence behavior.
3. Merge templates, number formatting, string formatting, and collection layout into one presentation stakeholder when they jointly produce displayed output.
4. Count security, operations, product policy, validation, or other stakeholders only when code in the unit demonstrates independently changeable behavior for that concern. Do not infer them solely from a type name.
5. Before submitting, build one evidence entry per stakeholder containing the stakeholder, methods, and rationale. `stakeholder_count` must equal the number of evidence entries. Submit only the metric fields required by the output schema.
</detection>

<exceptions>
1. **Facade / Coordinator** (see @facade.md)
   A class that only coordinates protocol-typed subsystems has one responsibility: coordination.

   Check the Facade Recognition Conditions (ALL must hold):
    1. Every stored property / init parameter is protocol-typed
    2. Every method body is pure delegation — no business logic, no branching on own mutable state
    3. Class creates no objects internally — all dependencies injected via init
   If ALL conditions hold: cohesion groups = 1 (coordination), final severity = COMPLIANT
</exceptions>

<severity-bands id="SRP-1">
<band severity="COMPLIANT"><condition>verb_count &lt;= 2 and cohesion_groups == 1</condition></band>
<band severity="MINOR"><condition>verb_count &gt;= 3 and verb_count &lt;= 5 and cohesion_groups == 1 and stakeholder_count &lt;= 1</condition></band>
<band severity="SEVERE"><condition>verb_count &gt; 5 and cohesion_groups == 1</condition></band>
<band severity="SEVERE"><condition>verb_count &gt;= 3 and stakeholder_count &gt;= 2</condition></band>
</severity-bands>

<severity-bands id="SRP-2">
<band severity="COMPLIANT"><condition>cohesion_groups &lt;= 1</condition></band>
<band severity="SEVERE"><condition>cohesion_groups &gt;= 2</condition></band>
</severity-bands>

<severity-bands id="SRP-3">
<band severity="COMPLIANT"><condition>stakeholder_count &lt;= 1</condition></band>
<band severity="SEVERE"><condition>stakeholder_count &gt;= 2</condition></band>
</severity-bands>

---

## Quantitative Metrics Summary
| ID    | Metric          | Threshold                        | Severity  |
|-------|-----------------|----------------------------------|-----------|
| SRP-0 | Exception       | falls into exception category    | COMPLIANT |
| SRP-1 | Verbs           | 1-2 verbs, 1 group               | COMPLIANT |
| SRP-1 | Verbs           | 3-5 verbs, 1 group, 1 stakeholder | MINOR    |
| SRP-1 | Verbs           | 6+ verbs, 1 group                | SEVERE    |
| SRP-1 | Verbs           | 3+ verbs, 2+ stakeholders        | SEVERE    |
| SRP-2 | Cohesion groups | 2+ groups                        | SEVERE    |
---
