---
name: synthesize-implementation
description: Reconciles arch.json with validation.json to produce an ordered implementation plan of /code directives.
argument-hint: <arch.json-path> <validation.json-path> --output <plan-path> --refs-root <references-dir>
allowed-tools: Read, Grep, Glob, Bash, Write
user-invocable: true
---

# Implementation Plan Creator

Takes the architect's decomposition (`arch.json`) and the validator's codebase findings (`validation.json`), reconciles them, and produces a concrete, ordered implementation plan that `/code` can execute.

## Input

- ARCH_PATH: $ARGUMENTS[0] — path to `arch.json` (from `/plan`)
- VALIDATION_PATH: $ARGUMENTS[1] — path to `validation.json` (from `/validate-plan`)
- OUTPUT_PATH: extracted from `--output` flag — path to write `implementation-plan.json`
- REFS_ROOT: extracted from `--refs-root` flag — principle references directory (e.g., `references/`)

## Phase 0: Validate Inputs

- [ ] 0.1 Parse arguments. If `--refs-root` is missing, abort with error: "Missing required --refs-root argument."
- [ ] 0.2 If `--output` is missing, abort with error: "Missing required --output argument."
- [ ] 0.3 Read `arch.json` from ARCH_PATH. Verify it has `spec_summary`, `components`, `wiring`, and `composition_root`. If any are missing, abort with error listing missing fields.
- [ ] 0.4 Read `validation.json` from VALIDATION_PATH. Verify it has `components` and `summary`. If any are missing, abort with error listing missing fields.

## Phase 1: Discover & Load Principles

Load principle knowledge for informed reconciliation — NOT embedded in output.

- [ ] 1.1 Collect all `stack` values from `arch.json` components into a flat, deduplicated list of tags.
- [ ] 1.2 Use skill **solid-coder:discover-principles** with `--refs-root {REFS_ROOT}` and `--matched-tags {comma-separated tags}`. If no stack tags exist, omit `--matched-tags` to get only always-active (tagless) principles.
- [ ] 1.3 For each active principle:
  1. Use skill **solid-coder:parse-frontmatter** on `{principle_folder}/rule.md` to extract `examples` paths
  2. Use skill **solid-coder:load-reference** to load the `examples` paths from step 1
  3. Use skill **solid-coder:load-reference** to load `{principle_folder}/rule.md` and `{principle_folder}/fix/instructions.md`
- [ ] 1.4 Build lookup: `principle_id -> { rule, fix_instructions, examples }` for use in reconciliation.
- [ ] 1.5 Loaded principle knowledge informs three things during Phase 2:
  - **Conflict resolution** (2.1.4) — prefer types that already satisfy principle constraints
  - **Breaking change assessment** (2.2) — whether an adjustment violates principle rules
  - **Directive quality** (2.1.2, 2.1.3) — write directives that describe the right patterns (e.g., "inject via protocol" not "use singleton")

## Phase 2: Reconcile Architecture with Validation

Process each component from `arch.json` against its validation result. Read `composition_root` from `arch.json` for context in directive generation (e.g., "inject X into ProductAssembly"). If `composition_root` is empty string, skip — single-component features may not need one.

FOR EACH component in `arch.json` DO:

- [ ] 2.1 **Reconcile** — find the matching component in `validation.json` by `name`. If `matches[]` has >1 entry, use `matches[0]` (sorted by confidence descending) and document the choice. Based on `status`, apply one of:

  - [ ] 2.1.1 **`reuse`** — emit NO plan item. Record reconciliation decision: `action: "reuse"`, `existing_file` from `matches[0].file`.

  - [ ] 2.1.2 **`create`** — first check `matches[]`. If non-empty and `matches[0].match_confidence` is `medium` or `high`, the validator found something relevant — escalate to adjust: follow 2.1.3 using `matches[0]`. The directive should describe how to extend or adapt the existing type to fulfill the architect's component (e.g., add a protocol conformance, add a case to an enum, extend with new methods). Record reconciliation decision with reason: "Validator classified as create but existing type at {file} can be adjusted."

    If `matches[]` is empty OR `matches[0].match_confidence` is `low` → emit plan item with `action: "create"`. Directive includes: type name, category, responsibility, interfaces it must expose, dependencies it consumes, produces, and fields (for models) — all from `arch.json`. No `file` field — the implementation agent resolves file paths. Record reconciliation decision: `action: "create"`, `existing_file: null`.

  - [ ] 2.1.3 **`adjust`** — read the full validation match object (`matches[0]`), including `differences[]`, `existing_interfaces`, `existing_fields`. Emit plan item with `action: "modify"`, `file` from `matches[0].file`. Directive describes the specific adjustments needed, informed by `differences[]` — the validator has already done the comparison. Record reconciliation decision: `action: "modify"`, with `existing_file`.

  - [ ] 2.1.4 **`conflict`** — apply conflict resolution rule:

    Prefer existing type when ALL of the following are true:
    - `matches[0].match_confidence` is `high`
    - Number of `matches[0].differences[]` is <= 2

    If conditions met → follow 2.1.3 (`adjust`).

    Otherwise → follow 2.1.2 (`create`), with reason:
    - Low confidence: "Existing type has different purpose"
    - Too many differences: "Existing type needs too many changes — cheaper to create new"
    - Use skill **solid-coder:create-type** naming conventions to produce a differentiated name if the arch.json name collides with an existing type

- [ ] 2.2 **Breaking change check** — if 2.1 produced a `modify` action, check whether the change is breaking. A change is **breaking** when it requires updates to consumer call sites: changing method signatures, adjusting protocol interfaces (adding/removing/renaming requirements), modifying init parameters. Adding a new method to a concrete type (not a protocol requirement) is NOT breaking.

  If the modification IS breaking:
  - [ ] 2.2.1 Grep the codebase for all call sites of the affected protocol/type
  - [ ] 2.2.2 For each affected consumer file, emit an additional plan item: `action: "modify"`, with the consumer `file` path
  - [ ] 2.2.3 Consumer directive describes the specific interface change the consumer must adapt to
  - [ ] 2.2.4 Consumer plan items `depends_on` the adjustment plan item
  - [ ] 2.2.5 If >5 consumers, flag in `notes` that this is a high-impact change

END (per component)

## Phase 3: Order Plan Items

- [ ] 3.1 Assign IDs: `plan-001`, `plan-002`, etc.
- [ ] 3.2 Build `depends_on` for each item:
  - If item A creates a type that item B depends on → B depends on A
  - Consumer modification items depend on the adjustment they respond to (from 2.2)
- [ ] 3.3 Sort by dependency graph first, then by category order: protocols/abstractions → data models → implementations/services → views → wiring/composition
- [ ] 3.4 Verify: no item appears before its dependencies in the sorted list

## Phase 4: Output

- [ ] 4.1 Read the output schema from `${SKILL_DIR}/implementation-plan.schema.json`
- [ ] 4.2 Assemble `implementation-plan.json`:
  - `spec_summary`: from `arch.json`
  - `plan_items[]`: ordered list from Phase 3
  - `reconciliation_decisions[]`: one per `arch.json` component from Phase 2
  - `summary`: counts — `create` (new files), `modify` (existing files changed), `reuse` (no plan item)
- [ ] 4.3 If `plan_items` is empty (all components are `reuse`), note: "All components already exist — nothing to implement."
- [ ] 4.4 Write to OUTPUT_PATH
- [ ] 4.5 Print summary table:

  | Component | Status | Action | File |
  |-----------|--------|--------|------|

  And totals: `N create, N modify, N reuse`

## Constraints

- Principles inform decisions but are NOT embedded in the output — `/code` loads its own principles
- Do NOT re-compare `arch.json` components against codebase files — the validator already did this. Use `validation.json` findings directly
- Do NOT determine file paths for `create` actions — the implementation agent resolves paths at execution time
- Do NOT loop back to the architect — resolve conflicts locally using the conflict resolution rule
- If `arch.json` or `validation.json` is malformed, abort with clear error — do not attempt partial reconciliation
- Every `arch.json` component must appear in exactly one reconciliation decision
- Directives should describe patterns informed by loaded principles (e.g., "inject via protocol" not "use singleton") without embedding the rules themselves
