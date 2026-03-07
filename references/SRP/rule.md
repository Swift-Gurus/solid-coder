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

**Example: 🔥 Low Cohesion (Multiple Responsibilities):**
```swift
// 🔥 Violation: 3 cohesion groups → SEVERE
class OrderProcessor {
    // Group 1 variables (validation)
    private var validationRules: [Rule] = []
    private var errorMessages: [String] = []

    // Group 2 variables (payment)
    private var paymentGateway: Gateway?
    private var transactionId: String?

    // Group 3 variables (email)
    private var emailService: EmailService?
    private var emailTemplate: Template?

    // Group 1 methods - ONLY use validationRules, errorMessages
    func validateOrder(_ order: Order) -> Bool { ... }
    func addValidationRule(_ rule: Rule) { ... }

    // Group 2 methods - ONLY use paymentGateway, transactionId
    func processPayment(_ amount: Double) -> Bool { ... }
    func refundPayment() -> Bool { ... }

    // Group 3 methods - ONLY use emailService, emailTemplate
    func sendConfirmation(_ order: Order) { ... }
    func sendReceipt() { ... }
}
```
**Analysis:**
- 6 variables: 3 distinct groups
- 6 methods: 3 distinct groups (2 methods per group)
- **Cohesion groups:** 3 + -> 🔥 SEVERE
- **Verbs**: validates, adds-rules, processes-payment, refunds, sends-confirmation, sends-receipt (6 verbs) → SEVERE (4+ in single group not even needed — 2+ groups already SEVERE)

**Why this matters:** Low cohesion reveals hidden responsibilities. Each cohesion group = separate stakeholder:
- **Group 1** → Business Analyst (validation rules)
- **Group 2** → Payments Team (gateway changes)
- **Group 3** → Marketing (email content)

**Example: 🔥 Low Cohesion (Multiple Responsibilities via Bridge Method):**

```swift
// 🔥 Violation: 2 cohesion groups connected by bridge method → SEVERE
class ReportManager {
// Group 1: Data fetching
private var dataSource: DataSource
private var cache: [String: Report]

      // Group 2: Export
      private var exportFormat: ExportFormat
      private var outputPath: URL

      // Bridge method — touches BOTH groups
      func generateReport(for query: Query) {
          let data = fetchData(for: query)   // Group 1
          export(data, to: outputPath)        // Group 2
      }

      // Group 1 only
      func fetchData(for query: Query) -> ReportData { ... }
      func clearCache() { ... }

      // Group 2 only
      func export(_ data: ReportData, to path: URL) { ... }
      func setExportFormat(_ format: ExportFormat) { ... }
}
```
**Analysis:**
- Remove bridge method → 2 disjoint components remain
- Group 1 (Data): dataSource, cache
- Group 2 (Export): exportFormat, outputPath
- **Cohesion groups:** 2 -> 🔥 SEVERE
- **Verbs**: fetch, clear, export, configure, orchestrate


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

