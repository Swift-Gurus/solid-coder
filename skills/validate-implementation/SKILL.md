---
name: validate-implementation
description: Post-implementation checkpoint — verifies code against spec, arch, plan, and design references. Collects user screenshots and feedback.
argument-hint: <output-root>
allowed-tools: Read, Glob, Bash, Write, AskUserQuestion
output_schema: ${CLAUDE_PLUGIN_ROOT}/skills/synthesize-implementation/implementation-plan.schema.json
user-invocable: false
---

# Validate Implementation

Post-code checkpoint that gates the expensive refactor phase. Reads the full pipeline context (spec, arch, validation, implementation plan), checks what was built against what was planned, and collects user feedback for visual verification.

## Input

- OUTPUT_ROOT: $ARGUMENTS[0] — the implement run directory containing all pipeline artifacts

## Available Artifacts

The skill discovers what's available in OUTPUT_ROOT:

| File | Contains | Used for |
|------|----------|----------|
| `spec.md` | Original spec with user stories, acceptance criteria, definition of done | Verify all requirements are met |
| `resources/` | Design screenshots, mockups, schemas | Visual comparison with user screenshots |
| `arch.json` | Components, protocols, wiring, acceptance_criteria[], design_references[] | Verify all planned components exist |
| `validation.json` | Codebase matches, reuse annotations | Verify reuse decisions were followed |
| `implementation-plan.json` | Ordered plan_items[] with directives, acceptance_criteria[] | Verify each plan item was executed |

## Phase 1: Load Context

- [ ] 1.1 Glob `{OUTPUT_ROOT}/*` to discover available artifacts
- [ ] 1.2 Read `spec.md` — extract user stories, acceptance criteria, definition of done
- [ ] 1.3 Read `arch.json` — extract components[], acceptance_criteria[], design_references[]
- [ ] 1.4 Read `implementation-plan.json` — extract plan_items[], per-item acceptance_criteria
- [ ] 1.5 Check if `resources/` exists — list design files if present
- [ ] 1.6 Determine scope:
  - Has design references or resources? → visual validation needed
  - Has UI components (screen, view-component, modifier, viewmodel)? → visual validation needed
  - Has acceptance criteria? → criteria validation needed
  - None of the above? → return `{ "status": "skipped", "reason": "no design, UI, or criteria to validate" }`

## Phase 2: Spec Requirements Validation

- [ ] 2.1 Read the spec's user stories and acceptance criteria
- [ ] 2.2 For each criterion, quick check — does the code appear to address it?
  - Non-visual criteria → skim codebase for evidence (Grep/Glob, don't deep-read)
  - Visual criteria → defer to Phase 3

  | Criterion | Visual? | Likely met? | Notes |
  |-----------|---------|-------------|-------|
  |           |         |             |       |

## Phase 3: Visual Validation (if design references exist)

Only runs if Phase 1.6 determined visual validation is needed.

- [ ] 3.1 Load design reference images from `resources/` and `design_references[]`
- [ ] 3.2 For each design reference, ask user using AskUserQuestion: for a matching screenshot:
  - Include the resource filename and describe the state shown in it
  - Example: "Please provide a screenshot matching: `Screenshot 2026-03-30 at 5.19.04 PM.png` (empty state — no recent projects)"
  - Ask one at a time or grouped if multiple states of the same screen
  - Options: provide screenshot(s), 'Approved' if already verified
  - [ ] 3.2.1 If user provides screenshot(s) → structured comparison:
    - For each design/screenshot pair:
      - List every visual element in the design image
      - List every visual element in the implementation screenshot
      - Compare element by element
      - Classify differences: `missing` | `extra` | `wrong` | `clipped`
    - Record findings, then continue to next design reference (or Phase 4 if last)
  - [ ] 3.2.2 If user selects "Approved" → note visual validation approved by user
    - Continue to next design reference (or Phase 4 if last)

## Phase 4: Collect User Feedback

- [ ] 4.1 Present findings from Phase 2 and Phase 3 to user
- [ ] 4.2 Ask using AskUserQuestion:
  "Here's what I found. Select an option:"
  - **Approved** — everything looks correct, proceed to refactor
  - **Has Issues** — provide additional feedback on what's wrong
  - **Stop** — don't proceed, I'll fix things manually
- [ ] 4.3 If "Has Issues" → collect free-form feedback, add to findings

## Phase 5: Produce Fix Plan

Only runs if there are actionable findings (design mismatches, failed criteria, user feedback).

- [ ] 5.1 For each finding, produce a plan item in `implementation-plan.json` format:
  - `id`: `fix-001`, `fix-002`, etc.
  - `action`: `"modify"` (design fixes target existing files)
  - `file`: path to the file that needs fixing (from file_hint or search)
  - `directive`: specific fix instruction (e.g., "Replace app icon — use SF Symbol 'command' on blue rounded rectangle. Current icon is a gradient wave graphic.")
  - `depends_on`: `[]` (fixes are independent unless one depends on another)
  - `component`: component name if known
  - `notes`: what was wrong (expected vs actual)
  - `acceptance_criteria`: the spec criteria this fix addresses

- [ ] 5.2 Ask user using AskUserQuestion: to confirm directives — "Which of these should I fix?"
  - User can approve all, select specific ones, or dismiss all

- [ ] 5.3 Assemble `design-fix-plan.json` matching implementation-plan schema:
  - `spec_summary`: "Design fixes from validate-implementation"
  - `matched_tags`: read from the original `implementation-plan.json` in OUTPUT_ROOT
  - `plan_items[]`: approved fix items from 5.1
  - `reconciliation_decisions`: `[]` (not applicable)
  - `summary`: counts

- [ ] 5.4 Validate before writing — run:
  `! python3 ${CLAUDE_PLUGIN_ROOT}/skills/prepare-review-input/scripts/validate-output.py {OUTPUT_ROOT}/design-fix-plan.json ${CLAUDE_PLUGIN_ROOT}/skills/synthesize-implementation/implementation-plan.schema.json`
  If validation fails, fix the JSON and re-validate.
- [ ] 5.5 Write validated `design-fix-plan.json` to `{OUTPUT_ROOT}/`

## Phase 6: Output

Return result:
- `status`: `"approved"` | `"has_fixes"` | `"skipped"` | `"stopped"`
- `fixes_path`: path to `design-fix-plan.json` (if has_fixes)
- `fix_count`: number of approved fixes

## Constraints

- Do NOT self-evaluate visual design from code — require user screenshots for image comparison
- Do NOT build the project — ask the user to build and screenshot
- When comparing images, list specific elements and differences — not vague assessments
- Acceptance criteria verifiable from code (e.g., "uses protocol injection") can be checked without user input
- Missing components are always flagged — if arch.json says it should exist, verify it does
