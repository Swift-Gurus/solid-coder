# Subtask — Validation Rules

Rules applied by `validate-spec` to subtask-type specs. Structure from `subtask/rule.md`; buildability checks are identical to features (Phase B in [feature/review/instructions.md](../../feature/review/instructions.md)) with one subtask-specific addition.

## Phase A — Structural Checks

- [ ] A.1 **Frontmatter** — `number`, `feature`, `type: subtask`, `status`, `blocked-by`, `blocking`, **`parent` required** (subtasks must have a parent).
- [ ] A.2 **Required sections (in order):** Title, Description, Input / Output, User Stories, Technical Requirements, Connects To, Diagrams, Test Plan, Definition of Done.
- [ ] A.3 **Technical Requirements is ALWAYS required** for subtasks. Flag its absence even if the subtask looks simple.
- [ ] A.4 **Conditional sections** — apply rules from `subtask/rule.md`:
  - `## UI / Mockup` required if the subtask touches a screen, view, or user interaction. Placeholder-only (`<!-- TODO -->`) counts as missing.
  - `## Current State` required only if `mode: rewrite`.
- [ ] A.5 **Diagrams completeness** — `## Diagrams` contains at minimum connection + flow. Sequence diagram required if the spec mentions async operations, callbacks, delegates, notifications, network calls, or multiple distinct actors.
- [ ] A.6 **Forbidden sections** — flag presence of `## Features` list (subtasks are leaves).

## Phase B — Buildability Scan (Standard)

Apply every check from [feature/review/instructions.md § Phase B](../../feature/review/instructions.md#phase-b--buildability-scan-standard):

- B.1 User story quality
- B.2 Vague terms
- B.3 Undefined types
- B.4 Intent-described operations
- B.5 Implicit consumer contracts
- B.6 Unverified external APIs
- B.7 Ambiguous scope boundaries
- B.8 Implementation leaking
- B.9 AC-architecture disconnects

All rules apply identically to subtasks. Do NOT duplicate the rule text here — read them from the feature review instructions.

## Phase C — Scope & Cohesion

Apply every check from [feature/review/instructions.md § Phase C](../../feature/review/instructions.md#phase-c--scope--cohesion):

- C.0 Applicability gate — subtasks are always leaf, so the gate never fires. Phase C always runs.
- C.1 SCOPE-1 — predicted production LOC.
- C.2 SCOPE-2 — cohesion groups.
- C.3 Split recommendation. When a subtask is recommended for split, the parent feature gains new sibling subtasks; the subtask itself either disappears (cohesion split) or stays with extracted helpers carved out (oversized-cohesive case).

All metric definitions live in [README § Scope Metrics](../../README.md#scope-metrics). Do NOT duplicate them here.

## Reporting

- Group findings by category: `structural`, `user_story_quality`, `vague_term`, `undefined_type`, `intent_described`, `implicit_contract`, `unverified_api`, `ambiguous_scope`, `implementation_leaking`, `ac_architecture_disconnect`, `scope_oversized`, `incohesive`, `oversized_cohesive`, `split_recommendation`.
- Per finding: `category`, `location` (section or phrase), `question` (what needs to be answered), and for Phase C: `severity` (MINOR / SEVERE) plus the per-input counts that produced the metric.
- Verdict:
  - `pass` — 0 findings across all phases.
  - `needs_clarification` — any Phase A or B finding, or any Phase C finding at SEVERE.
  - `advisory` — only Phase C findings at MINOR (spec is buildable but worth reviewing).
