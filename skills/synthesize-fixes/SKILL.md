---
name: synthesize-fixes
description: Reconcile cross-principle fix suggestions into a conflict-free implementation plan.
argument-hint: <output-root>
allowed-tools: Read, Grep, Glob, Bash, Write
user-invocable: false
---

# Fix Synthesis

Reconciles fix suggestions from independent principle agents into a single, conflict-free implementation plan per file.

## Input
- OUTPUT_ROOT: $ARGUMENTS[0] — review output directory (e.g., `.solid_coder/refactor-20260302142957/`)

## Phase 1: Load Context

- [ ] 1.1 Glob for `{OUTPUT_ROOT}/by-file/*.output.json`
- [ ] 1.2 For each file, read the JSON — it contains `principles[]` with `findings[]` and `suggestions[]`
- [ ] 1.3 Read the source file referenced in the `file` field of each output

## Phase 2: Build Finding-to-Suggestion Map

For each file output:

- [ ] 2.1 **Collect all findings** across all principles into a flat list with their principle tag
- [ ] 2.2 **Collect all suggestions** across all principles into a flat list
- [ ] 2.3 **Build map**: for each finding ID, list ALL suggestions that include it in their `addresses` array
- [ ] 2.4 **Flag conflicts**: any finding addressed by suggestions from MORE THAN ONE principle is a conflict candidate
- [ ] 2.5 **Flag new types**: any suggestion with non-empty `verification.refactored_types` creates new code that must be checked

## Phase 3: Detect and Resolve Conflicts

Apply these three rules **in order** to every conflict candidate:

### Rule 1: Principle Authority

> A finding's own principle has authority over its resolution.

If finding `X-nnn` (where X is a principle prefix like `lsp`, `ocp`, `srp`) is addressed by:
- A suggestion from the **same principle** (`X-fix-nnn`), AND
- A suggestion from a **different principle** (`Y-fix-nnn`)

Then:
- The X-principle suggestion is **authoritative** for finding `X-nnn`
- Remove `X-nnn` from the Y-principle suggestion's `resolves` list
- Record this in `conflicts_detected`

**Example**: `lsp-001` is addressed by both `lsp-fix-001` (LSP) and `ocp-fix-001` (OCP). LSP wins for `lsp-001`. OCP keeps its own findings (`ocp-001`, `ocp-002`).

### Rule 2: Relocation Detection

> Moving a violation to a new type is not resolving it.

For each suggestion that creates new types (has `verification.refactored_types`):
- Check each `refactored_type`'s metrics against the finding's metric
- If the new type shows the **same violation metric > 0** (e.g., `type_checks: 1` for an LSP-1 finding, or `sealed_variation_points: 1` for an OCP-1 finding), the finding was **relocated, not resolved**
- Remove that finding from the suggestion's `resolves` list
- Add a `relocation_detected` note to `conflicts_detected`

**Metric-to-finding mapping**:
| Finding metric | Verification field to check |
|---|---|
| LSP-1 | `type_checks > 0` |
| LSP-2 | `contract_violations > 0` |
| LSP-3 | `empty_methods > 0` or `fatal_error_methods > 0` |
| OCP-1 | `sealed_variation_points > 0` |
| OCP-2 | `direct_untestable_count > 0` or `indirect_untestable_count > 0` |
| SRP-1 | `verbs > 5` and `stakeholders > 1` |

### Rule 3: Complementary Merging

> Compatible suggestions that touch the same file should be ordered, not duplicated.

For suggestions that survived Rules 1 and 2:
- If two suggestions modify the **same class** but address **different findings** with **no overlapping `resolves`** IDs, they are **compatible**
- Determine ordering: if suggestion A creates a type that suggestion B modifies, A has `depends_on: []` and B has `depends_on: [A.id]`
- If no dependency exists, order by severity (SEVERE first) then by principle order (OCP → LSP → SRP)

## Phase 4: Produce Reconciled Plan

- [ ] 4.1 Read the output schema from `${SKILL_DIR}/plan.schema.json`
- [ ] 4.2 For each file, build the plan JSON:
  - `actions`: ordered list of suggestions to implement, each with:
    - `suggestion_id`: original suggestion ID
    - `principle`: which principle authored it
    - `resolves`: finding IDs (after conflict resolution — may be fewer than original `addresses`)
    - `todo_items`: from the original suggestion
    - `depends_on`: suggestion IDs that must run first (from Rule 3)
    - `amended_todo_items`: additional steps needed to integrate with other fixes (e.g., "use `authCredential.userId` instead of `as? GoldenGateAuthCredential` downcast in LiveSessionProvider")
    - `note`: explanation of any synthesis decisions
  - `unresolved`: findings that no suggestion adequately resolves
  - `conflicts_detected`: all conflicts found and how they were resolved
- [ ] 4.3 Write to `{OUTPUT_ROOT}/synthesized/{filename}.plan.json`
- [ ] 4.4 Print summary:

  | File | Actions | Conflicts | Unresolved |
  |------|---------|-----------|------------|

## Constraints

- Do NOT invent new fix suggestions — only reorder, re-attribute, and annotate existing ones
- Do NOT modify the original `by-file/*.output.json` files
- Every finding MUST appear in exactly one of: an action's `resolves`, or `unresolved`
- The `todo_items` from original suggestions are preserved verbatim; use `amended_todo_items` for synthesis additions
- If no conflicts are detected, the plan is a straight pass-through of suggestions in severity order
