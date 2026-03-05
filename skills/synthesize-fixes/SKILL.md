---
name: synthesize-fixes
description: Holistic fix planner — reads all findings from all principles, loads principle fix knowledge dynamically, and generates a unified, cross-checked fix plan per file.
argument-hint: <output-root> <rules-path>
allowed-tools: Read, Grep, Glob, Bash, Write
user-invocable: false
---

# Holistic Fix Planner

Generates a unified, cross-principle-aware fix plan for each file. Unlike per-principle fix generation, this skill sees ALL findings simultaneously and cross-checks every proposed fix against ALL principles' metrics to prevent cascading violations.

## Input
- OUTPUT_ROOT: $ARGUMENTS[0] — iteration output directory (e.g., `.solid_coder/refactor-20260302/1`)
- RULES_PATH: $ARGUMENTS[1] — principle references root (e.g., `references/`)

## Phase 1: Load Context

- [ ] 1.1 Glob for `{OUTPUT_ROOT}/by-file/*.output.json`
- [ ] 1.2 For each file output JSON, read the JSON — it contains `principles[]` with `findings[]` (suggestions may be empty)
- [ ] 1.3 Read the source file referenced in the `file` field of each output
- [ ] 1.4 Collect the set of principle agent IDs (e.g., `srp`, `ocp`, `lsp`) that have **non-COMPLIANT** severity across all files
- [ ] 1.5 If ALL files are COMPLIANT (no findings), write empty plans and stop

## Phase 2: Load Principle Fix Knowledge

Load fix knowledge **only for principles that have findings** (keeps context bounded as rules scale).

- [ ] 2.1 For EACH principle agent ID from step 1.4, resolve to the principle folder: `{RULES_PATH}/{UPPERCASE_AGENT_ID}/`
- [ ] 2.2 Read `{principle_folder}/fix/instructions.md` — fix strategies and severity-based approach
- [ ] 2.3 Read `{principle_folder}/refactoring.md` — refactoring patterns and code examples
- [ ] 2.4 Read `{principle_folder}/rule.md` — metric definitions (needed for cross-verification)
- [ ] 2.5 Read `{principle_folder}/Examples` — examples of violations and compliant
- [ ] 2.6 **Load patterns** — Parse `required_patterns` from rule.md frontmatter. For each entry, read `{RULES_PATH}/design_patterns/{entry}.md`
- [ ] 2.7 Build a lookup: `principle_id → { fix_instructions, refactoring_patterns, metrics, patterns }`

## Phase 3: Generate Holistic Fix Plan

FOR each file that has non-COMPLIANT findings:

### 3.1 Gather All Findings
- [ ] Collect ALL findings from ALL principles for this file into a single list
- [ ] Group findings by unit (class/struct/enum) they affect

### 3.2 Determine Fix Strategy Per Unit
FOR each unit with findings:
- [ ] Read each principle's `fix/instructions.md` severity-based strategy for this unit
- [ ] Identify what refactoring pattern each principle suggests (extract type, inject dependency, split protocol, etc.)
- [ ] **Look for synergies**: do multiple principles' fixes align? (e.g., SRP extraction + OCP protocol injection can be done in one step)
- [ ] **Look for conflicts**: would one principle's fix introduce violations for another? (e.g., SRP extraction creating sealed variation points)

### 3.3 Design Unified Fix Actions
FOR each unit:
- [ ] Create fix actions that satisfy ALL principles simultaneously
- [ ] For each action, follow the fix strategy from the owning principle's `fix/instructions.md`
- [ ] **Cross-check each action against every loaded principle's metrics:**

  | Check | Question | Metric Source |
  |-------|----------|---------------|
  | SRP | Does any new/modified type have >1 cohesion group or >1 stakeholder? | SRP rule.md |
  | OCP | Does any new type introduce sealed variation points or untestable deps? | OCP rule.md |
  | LSP | Does any new protocol introduce empty methods for existing conformers? Type checks? | LSP rule.md |

- [ ] If a cross-check fails, **adjust the fix** before finalizing:
  - SRP fail → split the extracted type further
  - OCP fail → inject dependencies via protocol instead of concrete reference
  - LSP fail → split the protocol so conformers only implement what they support
- [ ] Record cross-check results in the action

### 3.4 Write Suggested Fix
FOR each action:
- [ ] Write full code snippets showing:
  - Protocol definitions (if any)
  - Extracted/modified types with init and moved methods
  - Modified original class with injected dependencies
  - Before/after of key methods
- [ ] Create concrete `todo_items` — each a single implementable step
- [ ] Fill `suggested_fix` with the full text + code snippets
- [ ] Record which finding IDs this action `resolves`

### 3.5 Order Actions
- [ ] Apply Rule 3 (Complementary Merging): if action A creates a type that action B modifies, B depends on A
- [ ] Order by: dependency graph first, then severity (SEVERE → MODERATE → MINOR)

### 3.6 Verify Completeness
- [ ] Every finding must appear in exactly one action's `resolves` list, OR in `unresolved`
- [ ] Apply Rule 1 (Principle Authority): if a finding is resolved by multiple actions, the action from the finding's own principle wins
- [ ] Apply Rule 2 (Relocation Detection): if a fix merely moves a violation to a new type without resolving it, mark as `unresolved` with reason

END (per file)

## Phase 4: Output

- [ ] 4.1 Read the output schema from `${SKILL_DIR}/plan.schema.json`
- [ ] 4.2 For each file, write `{OUTPUT_ROOT}/synthesized/{filename}.plan.json` matching the schema:
  - `file`: source file path
  - `actions[]`: ordered list of fix actions, each with:
    - `suggestion_id`: generated ID (e.g., `holistic-fix-001`)
    - `principle`: primary principle this action addresses
    - `resolves[]`: finding IDs resolved (after cross-check — may address findings from multiple principles)
    - `todo_items[]`: concrete implementation steps
    - `suggested_fix`: full code snippets (protocols, types, modified class)
    - `depends_on[]`: action IDs that must run first
    - `cross_check_results[]`: per-principle verification
    - `note`: explanation of design decisions
  - `unresolved[]`: findings no action resolves, each with `finding_id` and `reason`
  - `conflicts_detected[]`: cross-principle conflicts found and how resolved
- [ ] 4.3 Print summary:

  | File | Actions | Cross-Checks Passed | Unresolved |
  |------|---------|---------------------|------------|

## Constraints

- Load principle fix knowledge DYNAMICALLY — only for principles that have findings
- Cross-check every fix against ALL loaded principles' metrics before finalizing
- If a cross-check fails, adjust the fix — do NOT emit a fix known to violate another principle
- Do NOT invent findings — only address findings from the review outputs
- Include full code snippets in `suggested_fix` (protocols, types, modified class)
- `todo_items` must be concrete and implementable (not vague)
- Preserve existing public API of the source file
- If all findings for a file are COMPLIANT, write an empty plan (no actions) and skip
- Every finding MUST appear in exactly one of: an action's `resolves`, or `unresolved`
