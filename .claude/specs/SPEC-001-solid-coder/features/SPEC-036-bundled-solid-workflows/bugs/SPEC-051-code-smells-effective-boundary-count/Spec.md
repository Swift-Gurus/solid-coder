---
number: SPEC-051
feature: code-smells-effective-boundary-count
type: bug
status: draft
parent: SPEC-036
blocked-by: []
blocking: []
---

# Code-smells scoring accepts a raw declaration count that contradicts an applied exclusion

## Description

The CS-2 workflow asks the model to collapse one behavioral contract and its first concrete implementation into one cohesive type boundary, but the submitted scalar can still contain the raw declaration count. The MCP scorer accepts that scalar without enough structured measurement evidence to validate that the authored exclusion affected the count, producing a false severe finding that blocks a compliant write.

## Steps to Reproduce

1. Prepare a source file containing exactly one behavioral contract and its first concrete implementation for the same cohesive capability.
2. Run the bundled code-smells workflow through the write-time health gate.
3. Have the model identify both declarations and state that they are treated as one cohesive boundary under the CS-2 exclusion.
4. Submit `class_struct_count: 2` while retaining that exclusion reasoning and evidence.
5. Observe: MCP applies the severe `value >= 2` band and blocks the write even though the accompanying audit says the two declarations form one counted boundary.

## Expected vs Actual

|          | Behavior |
|----------|----------|
| Expected | The submitted CS-2 measurement carries enough structured signals for MCP to validate the effective boundary count, and one contract plus its first cohesive implementation is scored as one boundary. |
| Actual   | MCP receives only the scalar value and audit text, accepts `2`, and scores it severe without detecting that the value contradicts the stated exclusion. |

## Affected Component

The bundled code-smells rule workflow and the flow-engine metric submission/scoring boundary defined under SPEC-039 and delivered by SPEC-036. Reproduced in run `271dd9c00e45409b88b7ce286c22027c`, where event 134 records CS-2 value `2` alongside reasoning that the declarations are one cohesive boundary.
