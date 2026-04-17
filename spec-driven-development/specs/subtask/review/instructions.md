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

## Reporting

- Group findings by category: `structural`, `user_story_quality`, `vague_term`, `undefined_type`, `intent_described`, `implicit_contract`, `unverified_api`, `ambiguous_scope`, `implementation_leaking`, `ac_architecture_disconnect`.
- Per finding: `category`, `location` (section or phrase), `question` (what needs to be answered).
- Verdict: `pass` (0 findings) or `needs_clarification` (>0 findings).
