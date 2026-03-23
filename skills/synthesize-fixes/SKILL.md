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
- [ ] 1.3 Read the source file referenced in the `file_path` field of each output
- [ ] 1.4 Collect the set of principle agent IDs (e.g., `srp`, `ocp`, `lsp`) that have **non-COMPLIANT** severity across all files
- [ ] 1.5 If ALL files are COMPLIANT (no findings), write empty plans and stop

## Phase 2: Load Principle Fix Knowledge

Load fix knowledge **only for principles that have findings** (keeps context bounded as rules scale).

- [ ] 2.1 For EACH principle agent ID from step 1.4, resolve to the principle folder: `{RULES_PATH}/{UPPERCASE_AGENT_ID}/`
- [ ] 2.2 **Parse rule frontmatter** — Run:
  `! python3 ${CLAUDE_PLUGIN_ROOT}/skills/parse-frontmatter/scripts/parse-frontmatter.py {principle_folder}/rule.md`
- [ ] 2.3 **Load references** — Run:
  `! python3 ${CLAUDE_PLUGIN_ROOT}/skills/load-reference/scripts/load-reference.py <files_to_load paths from step 2.2>`
- [ ] 2.4 **Load fix knowledge** — Run:
  `! python3 ${CLAUDE_PLUGIN_ROOT}/skills/load-reference/scripts/load-reference.py {principle_folder}/fix/instructions.md {principle_folder}/rule.md`
- [ ] 2.5 **Build a lookup:** `principle_id → { fix_instructions, metrics, patterns, examples }`

## Phase 3: Draft Fix Actions

Generate one draft action per principle per unit. Each draft is focused on a single principle — do NOT consider other principles yet.

FOR each file that has non-COMPLIANT findings:

### 3.1 Gather & Group
- [ ] Collect ALL findings from ALL principles for this file into a single list
- [ ] Group findings by unit (class/struct/enum) they affect

### 3.2 Draft Per-Principle Actions

**Principle order:** Process principles from smallest to largest blast radius 
    - Resolve dependencies before restructuring. The order is: Functions -> Any UI -> OCP → LSP → ISP → SRP. 
    - Each principle's fixes build on the previous:
        - OCP resolves sealed dependencies so LSP can fix abstractions cleanly, 
        - ISP splits fat protocols so extracted types get narrow interfaces,  
        - SRP extracts types that already have proper injection.

FOR each unit with findings, FOR each principle **in the order above** that has findings on this unit:
- [ ] Using ONLY that principle's `fix/instructions.md` from the Phase 2 lookup
- [ ] Generate a draft action:
  - `suggestion_id`: e.g., `draft-srp-001`
  - `principle`: the owning principle
  - `resolves[]`: finding IDs from THIS principle only
  - `suggested_fix`: full code snippets (protocols, extracted types, modified class, before/after)
  - `todo_items`: concrete implementable steps
- [ ] Do NOT consider other principles — focus on one concern at a time

### 3.3 Collect
- [ ] Collect all draft actions for this file into a list

END (per file)

---

## Phase 4: Verify & Patch

Cross-check each draft action against every OTHER active principle's metrics. Patch violations using that principle's fix patterns. This reuses the same rule.md and fix/instructions.md already loaded in Phase 2 — no separate recipe files needed.

FOR each draft action:

### 4.1 Identify Cross-Check Targets
- [ ] All OTHER active principles (from Phase 1.4) that are not the action's own principle

### 4.2 Run Cross-Checks
FOR each cross-check principle:
- [ ] Read the proposed code in the action's `suggested_fix`
- [ ] Apply that principle's `rule.md` metrics to the proposed code. Specifically check for new or modified types/protocols introduced by the fix:
  - **SRP**: Count cohesion groups and verbs in any new/modified type. Does any have >1 cohesion group or 2+ stakeholders?
  - **OCP**: Count sealed variation points in any new/modified type. Are there singletons, static calls, or internal construction?
  - **LSP**: Check any new protocol — will conformers have empty methods? Are there type checks against the new types?
  - **ISP**: Check any new/modified protocol — does it force conformers to implement methods they don't need? Would any realistic conformer leave a method empty?
  - **SwiftUI**: Check body complexity (SUI-1), view purity (SUI-2), modifier chains (SUI-3), VM injection (SUI-4) on any new/modified views.
- [ ] Record result: `{ principle, passed: true/false, detail: "what was checked and why" }`

### 4.3 Patch Failures
IF any cross-check fails:
- [ ] Load the failing principle's `fix/instructions.md` from the Phase 2 lookup
- [ ] Apply its standard fix pattern to patch the action's `suggested_fix`:
  - **SRP fail** → split the extracted type further along cohesion group boundaries
  - **OCP fail** → wrap concrete dependencies behind protocols, inject via init instead of direct/singleton reference
  - **LSP fail** → split the protocol so conformers only implement what they use; remove type checks by improving the abstraction
  - **ISP fail** → split the fat protocol into focused role protocols; conformers adopt only what they need
  - **SwiftUI fail** → extract subviews (SUI-1), move logic to ViewModel (SUI-2), extract modifier chains to named variables (SUI-3), inject VM via protocol interfaces (SUI-4)
- [ ] Update `todo_items` to include the patch steps
- [ ] Re-run the failed cross-check on the patched code
- [ ] If still fails → move the affected findings to `unresolved[]` with reason explaining why the patch was insufficient
- [ ] Add a `note` explaining what was patched and why

### 4.4 Record Results
- [ ] Record all `cross_check_results` on the action

**Unresolved findings are not failures.** The synthesizer's job is to not make things worse and be honest about what it couldn't fix. Unresolved findings surface as new findings in the next iteration's re-review, where they get their own focused fix with fresh context. Do NOT attempt to recursively fix your own fixes.

END (per action)

---

## Phase 5: Merge & Order

Combine actions that touch the same unit, resolve overlaps, and produce the final ordered plan.

### 5.1 Merge Synergistic Actions
FOR each file, FOR each unit with multiple actions:
- [ ] Check if actions are synergistic — do they modify the same type in complementary ways?
  - Example: SRP extracts a type + OCP injects its deps → one combined action that extracts AND injects
- [ ] When merging:
  - Combine `resolves[]` from both actions
  - Union `todo_items`, reordering so extraction steps come before injection steps
  - Rewrite `suggested_fix` to show the combined result (not two separate snippets)
  - Set `principle` to the higher-severity action's principle
  - Preserve `cross_check_results` from both actions
  - Add `note` explaining the merge decision

### 5.2 Dependency Ordering
- [ ] If action A creates a type that action B modifies → B depends on A
- [ ] Build `depends_on[]` for each action

### 5.3 Sort
- [ ] Order by: dependency graph first, then severity (SEVERE → MINOR)

### 5.4 Verify Completeness
- [ ] Every finding MUST appear in exactly one action's `resolves[]` OR in `unresolved[]`
- [ ] **Principle Authority**: if a finding is claimed by multiple actions, the action from the finding's own principle wins
- [ ] **Relocation Detection**: if a fix merely moves a violation to a new type without resolving it, mark as `unresolved` with reason

END (per file)

---

## Phase 6: Validate merged fixes against rules
Merging actions in Phase 5 can introduce new violations that didn't exist in the individually-verified drafts. Re-validate only actions that were created or modified during Phase 5.

FOR EVERY suggested_fix that was **merged in step 5.1**:
    - [ ] 6.1 Read the proposed code in the action's `suggested_fix`
    - [ ] 6.2 Apply `rule.md` of every loaded principle to the merged code
    - [ ] 6.3 IF violations found:
        - [ ] 6.3.1 Adjust `suggested_fix` using `fix/instructions.md` for each violation
        - [ ] 6.3.2 Adjust `todo_items` to reflect the changes
        - [ ] 6.3.3 Re-validate the adjusted fix against all loaded principles
    - [ ] 6.4 IF still fails → move affected findings to `unresolved[]` with reason explaining why the patch was insufficient
END (per fix)

## Phase 7: Output

- [ ] 7.1 Read the output schema from `${SKILL_DIR}/plan.schema.json`
- [ ] 7.2 For each file, write `{OUTPUT_ROOT}/synthesized/{filename}.plan.json` matching the schema:
  - `file_path`: source file path
  - `actions[]`: ordered list of fix actions, each with:
    - `suggestion_id`: generated ID (e.g., `holistic-fix-001`)
    - `principle`: primary principle this action addresses
    - `resolves[]`: finding IDs resolved (after cross-check — may span multiple principles)
    - `todo_items[]`: concrete implementation steps
    - `suggested_fix`: full code snippets (protocols, types, modified class)
    - `depends_on[]`: action IDs that must run first
    - `cross_check_results[]`: per-principle verification results
    - `note`: explanation of design decisions, merges, or patches applied
  - `unresolved[]`: findings no action resolves, each with `finding_id` and `reason`
  - `conflicts_detected[]`: cross-principle conflicts found and how resolved
- [ ] 7.3 Print summary:

  | File | Actions | Cross-Checks Passed | Unresolved |
  |------|---------|---------------------|------------|

## Constraints

- Load principle fix knowledge DYNAMICALLY — only for principles that have findings
- Phase 3 (Draft) is single-principle focused — do NOT cross-check during drafting
- Phase 4 (Verify & Patch) reuses each principle's existing rule.md metrics and fix/instructions.md patterns — no separate recipe files
- If a cross-check fails and patch fails, mark as `unresolved` — do NOT recursively fix fixes
- Do NOT invent findings — only address findings from the review outputs
- Include full code snippets in `suggested_fix` (protocols, types, modified class)
- `todo_items` must be concrete and implementable (not vague)
- Preserve existing public API of the source file
- If all findings for a file are COMPLIANT, write an empty plan (no actions) and skip
- Every finding MUST appear in exactly one of: an action's `resolves`, or `unresolved`
