---
name: synthesize-implementation
description: Reconciles arch.json with validation.json to produce an ordered implementation plan of /code directives.
argument-hint: <arch.json-path> <validation.json-path> --output <plan-path>
allowed-tools: Read, Grep, Glob, Bash, Write
user-invocable: true
---

# Implementation Plan Creator

Takes the architect's decomposition (`arch.json`) and the validator's codebase findings (`validation.json`), reconciles them, and produces a concrete, ordered implementation plan that `/code` can execute.

## Input

- ARCH_PATH: $ARGUMENTS[0] — path to `arch.json` (from `/plan`)
- VALIDATION_PATH: $ARGUMENTS[1] — path to `validation.json` (from `/validate-plan`)
- OUTPUT_PATH: extracted from `--output` flag — path to write `implementation-plan.json`
- GATEWAY: ${CLAUDE_PLUGIN_ROOT}/mcp-server/gateway.py

## Phase 0: Validate Inputs

- [ ] 0.1 Parse arguments. If `--output` is missing, abort with error: "Missing required --output argument."
- [ ] 0.3 Read `arch.json` from ARCH_PATH. Verify it has `spec_summary`, `components`, `wiring`, and `composition_root`. If any are missing, abort with error listing missing fields. Also load `spec_number` (optional), `acceptance_criteria[]`, `design_references[]`, `technical_requirements[]`, and `test_plan[]` — these are used to enrich directives in Phase 2.
- [ ] 0.4 Read `validation.json` from VALIDATION_PATH. Verify it has `components` and `summary`. If any are missing, abort with error listing missing fields.

## Phase 1: Discover & Load Principles

Load principle knowledge for informed reconciliation — NOT embedded in output.

- [ ] 1.1 Collect all unique `category` and `stack` values from `arch.json` components into a flat, deduplicated list of tags.
- [ ] 1.2 Call `mcp__plugin_solid-coder_docs__load_rules` with `mode: "synth-impl"` and `matched_tags: [tags from 1.1]` (omit matched_tags if no tags). Apply the returned rules.
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

  - [ ] 2.1.3 **`adjust`** — read the full validation match object (`matches[0]`), including `differences[]`, `responsibility_aligned`, `existing_interfaces`, `existing_fields`. Route by the category distribution before emitting any plan item.

    - [ ] 2.1.3.0 **Build the `tag_set`** — collect distinct values of `differences[].category` across `matches[0].differences[]`. Note `match_confidence`.

    - [ ] 2.1.3.1 **Route on `(tag_set, match_confidence)`**:

      | If `tag_set` contains… | And confidence is… | Action |
      |---|---|---|
      | `responsibility-mismatch` (any combination) | any | Drop to 2.1.4 conflict resolution. The validator over-classified — the existing type addresses a different problem. |
      | `scope-mismatch` | `high` or `medium` | Coordinated extraction (2.1.3.2). Existing logic is relevant but architecturally unreachable; duplication is the wrong answer. |
      | `scope-mismatch` | `low` | Fall through to 2.1.2 `create`. Reason: "Cross-scope match too weak to justify extraction overhead." |
      | only `coverage-gap` and/or `shape-mismatch` | `high` or `medium` | Single `modify` on `matches[0].file`. Directive must address every difference in place — broaden coverage, refactor surface. (Existing 2.1.3 behavior.) |
      | only `missing-entry` | `high` or `medium` | Single `modify` on `matches[0].file` with **append-only** directive — do not refactor surrounding content, only insert the missing rows/sections. |
      | only `other` | any | Treat as `shape-mismatch` (single `modify`). |

      After emitting plan items, proceed to 2.2 (breaking-change check) — except when 2.1.3.2 fired, which handles its own dependency wiring.

    - [ ] 2.1.3.2 **Coordinated extraction** — when 2.1.3.1 routed here:

      1. **Resolve the shared destination.** Read both manifests: the new component's intended package (inferred from the `scope-mismatch` text, the architect's `composition_root`, or the package owning the directory the architect implies) and the existing match's package. Find a package both already depend on. If none exists, do NOT extract — fall through to 2.1.2 `create` with reason: "No shared dependency path between consumer locations." Record the chosen destination in `notes`.

      2. **Emit `action: "modify"` on `matches[0].file`** — directive: relocate the type to the resolved shared destination. If `tag_set` also contains `coverage-gap`, broaden the relocated logic during the move so it covers every case the new component requires; list the broadened cases explicitly in the directive.

      3. **For each existing consumer of the moved type** (locate via grep on the symbol name, Phase 2.2-style): emit `action: "modify"` directive to update imports/access to the new location. If broadening happened AND the consumer relied on the narrower semantics, the consumer's directive must preserve that narrow behavior (typically a one-line local predicate filtering the broader result).

      4. **Emit `action: "create"` on the architect's new component** — directive: implement the required shape (struct, protocol conformance, access level) by **delegating** to the shared utility from step 2. Zero duplicated logic — only adaptation (signature, conformance, wrapper).

      Set `depends_on` so items 3 and 4 depend on item 2. Record reconciliation `notes`: "Cross-scope adjust resolved by extraction to <destination>. Differences addressed: <relocation | broadening | wrapping per-entry>."

    Record reconciliation decision: `action: "modify"` (with `existing_file`) for the predominant action, plus a `notes` field explaining which routing branch fired and why.

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

## Phase 2.5: Enrich Directives

For each plan item produced in Phase 2, enrich its `directive` with spec context from `arch.json`:

- [ ] 2.5.1 **Acceptance criteria** — find criteria from `arch.json.acceptance_criteria[]` relevant to this plan item's component. For `modify` actions, also check `validation.json` matches — include only `unsatisfied_criteria[]` (criteria the existing code doesn't meet). Append to the directive: "Must fulfill: <criteria list>". Track which criteria were attached to at least one plan item.

- [ ] 2.5.2 **Design references** — if the component is a view, screen, or UI-related (`category` contains view, screen, modifier, or `stack` contains swiftui): find relevant `design_references[]` from `arch.json`. For `inline` type: embed the mockup/diagram markdown directly in the directive. For `file` type: include the path as "Reference design: <path>".

- [ ] 2.5.3 **Technical requirements** — scan `technical_requirements[]` from `arch.json` for subsections relevant to this component (type definitions, file structure, usage patterns that mention this component's name or type). For relevant subsections: convert the requirement into concrete acceptance criteria and append to the plan item's `acceptance_criteria[]`. Preserve code blocks verbatim within the criterion text. If a technical requirement cannot be associated with a specific component, add it to root-level `acceptance_criteria[]` for post-implementation verification.

- [ ] 2.5.4 **Test plan** — find test cases from `arch.json.test_plan[]` where `component` matches this plan item's component name. Attach matching test cases to the plan item's `test_cases[]`. Track which test cases were attached to at least one plan item.

## Phase 2.6: Create Plan Items for Unmatched Criteria and Test Cases

After Phase 2.5, some `arch.json.acceptance_criteria[]` and `arch.json.test_plan[]` entries will not have been attached to any plan item. These MUST become plan items or top-level fields — nothing from the spec is silently dropped.

- [ ] 2.6.1 Collect every criterion from `arch.json.acceptance_criteria[]` (across all stories, including Definition of Done) that was NOT attached to any plan item in Phase 2.5.1.
- [ ] 2.6.2 For EACH unmatched criterion:
  - If fulfilling it requires producing any artifact → create an additional plan item with `action: "create"` and a directive describing what to produce. Set `depends_on` to the plan items whose components the criterion exercises or depends on.
  - If it describes a constraint on existing work (nothing new to produce, only to verify) → place in top-level `acceptance_criteria[]` for post-implementation verification.
- [ ] 2.6.3 Collect every test case from `arch.json.test_plan[]` where `component` is `null` or was NOT matched to any plan item in Phase 2.5.4. For each:
  - Create a plan item with `action: "create"`, directive describing the test to write, and `test_cases[]` containing the test case. Set `depends_on` to plan items whose components the test exercises.
- [ ] 2.6.4 Verify: all `arch.json.acceptance_criteria[]` are accounted for (attached to items, created as items, or in top-level criteria). All `arch.json.test_plan[]` entries are accounted for (attached to items or created as items). If any are missing, stop and report.

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
  - `spec_number`: from `arch.json` (pass through unchanged, omit if not present)
  - `spec_summary`: from `arch.json`
  - `matched_tags[]`: the deduplicated tags from Phase 1.1 (categories + stacks)
  - `plan_items[]`: ordered list from Phase 3
  - `reconciliation_decisions[]`: one per `arch.json` component from Phase 2
  - `summary`: counts — `create` (new files), `modify` (existing files changed), `reuse` (no plan item)
- [ ] 4.3 If `plan_items` is empty (all components are `reuse`), note: "All components already exist — nothing to implement."
- [ ] 4.4 Write to OUTPUT_PATH.
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
- NEVER truncate output — no `head`, `tail`, `| head -N`, or line limits on any command, script, or file read. Always read the full content.
