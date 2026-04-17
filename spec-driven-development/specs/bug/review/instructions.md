# Bug — Validation Rules

Rules applied by `validate-spec` to bug-type specs. Structure from `bug/rule.md`. Validation is **status-aware** — draft bugs are reports, ready bugs have a fix plan. Do not apply the Phase B buildability scan to bugs; bug text is reproduction-driven, not requirement-driven.

## Phase A — Structural Checks (status-aware)

- [ ] A.1 **Frontmatter** — `number`, `feature`, `type: bug`, `status`, `blocked-by`, `blocking`, `parent`.

### When `status: draft` (Phase 1 — Report)

- [ ] A.2 **Required Phase 1 sections:** Title, Description, Steps to Reproduce, Expected vs Actual, Affected Component.
- [ ] A.3 **Phase 2 sections are optional at this stage** — do NOT flag the absence of Root Cause, Fix Plan, Diagrams, Test Plan, or Definition of Done.
- [ ] A.4 **UI / Mockup (conditional)** — required if the bug is visual (screenshot attached to `resources/` or inline mockup).

### When `status: ready` / `in-progress` / `done` (Phase 2 — Ready)

- [ ] A.5 **Required Phase 1 sections (still present):** Title, Description, Steps to Reproduce, Expected vs Actual, Affected Component.
- [ ] A.6 **Required Phase 2 sections:** Root Cause, Fix Plan, Diagrams, Test Plan, Definition of Done.
- [ ] A.7 **Diagrams completeness** — `## Diagrams` contains at minimum connection + flow showing the failing path AND the fixed path. Sequence diagram required if the bug involves async/multi-actor interactions.
- [ ] A.8 **Regression test required** — `## Test Plan` must include at least one test case that exactly matches the reproduction steps and asserts the expected (corrected) behavior. Without this, the bug can re-surface undetected.

## Phase A.9 — Forbidden Sections (any status)

Flag presence of:
- `## User Stories` (bugs use repro steps instead)
- `## Technical Requirements` (the fix is bounded by the bug)
- `## Features` list
- `## Current State` (that's for rewrite epics)
- `## Input / Output` (covered by Affected Component + repro)

## Phase B — Buildability Scan (skipped)

**Not applied to bugs.** Bug text is reproduction-driven, not requirement-driven. The Phase B checks (vague terms, undefined types, intent-described operations, implicit consumer contracts, unverified APIs, ambiguous scope, implementation leaking, AC-architecture disconnects) are built for features/subtasks that describe new behavior — they don't fit a bug report.

Only the structural checks from Phase A run against bugs.

## Reporting

- Group findings by category: `structural`, `missing_phase_1_section`, `missing_phase_2_section`, `missing_regression_test`, `forbidden_section`.
- Per finding: `category`, `location` (section name), `question` (what needs to be answered / added).
- Verdict: `pass` (0 findings) or `needs_clarification` (>0 findings).
