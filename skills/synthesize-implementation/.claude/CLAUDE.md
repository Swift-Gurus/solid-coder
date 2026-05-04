---
number: SPEC-004
feature: synthesize-implementation
status: done
blocked-by: [SPEC-002, SPEC-003]
blocking: [SPEC-001]
---

# /synthesize-implementation — Implementation Plan Creator

## Purpose

Takes the architect's decomposition (`arch.json`) and the validator's codebase findings (`validation.json`), reconciles them, and produces an ordered implementation plan of `/code` directives. This is the reconciliation point between what the architect designed and what the validator found in the codebase.

## Inputs / Outputs

| Direction | What | Format | Location |
|-----------|------|--------|----------|
| Input | Architecture decomposition | JSON (`arch.schema.json`) | Path from `$ARGUMENTS[0]` |
| Input | Codebase validation | JSON (`validation.schema.json`) | Path from `$ARGUMENTS[1]` |
| Input | Principle references | Markdown | `--refs-root` directory |
| Output | Implementation plan | JSON (`implementation-plan.schema.json`) | `--output` path |

## Connects To

| Upstream | Relationship |
|----------|-------------|
| `skills/plan` | Produces `arch.json` — components, wiring, composition root |
| `skills/validate-plan` | Produces `validation.json` — reuse status, matches, confidence scores |
| `skills/discover-principles` | Phase 1 — discover active principles by stack tags |
| `skills/parse-frontmatter` | Phase 1 — extract examples paths from rule.md |
| `skills/load-reference` | Phase 1 — load rule.md, fix/instructions.md, examples |
| `references/{PRINCIPLE}/` | Principle knowledge for informed reconciliation |

| Downstream | Relationship |
|------------|-------------|
| `skills/code` (via code-agent) | Consumes `plan_items[]` — each item is a `/code` directive |
| Orchestrator (SPEC-001, future) | Feeds plan items to code-agent in dependency order |

## Key Design Decisions

- **Principles inform, not embed** — principle knowledge is loaded to write better directives and resolve conflicts, but is NOT included in `implementation-plan.json`. The `/code` agent loads its own principles at execution time.
- **Spec context flows through arch.json** — `acceptance_criteria[]`, `design_references[]`, and `technical_requirements[]` are read from `arch.json` and distributed to individual plan items (Phase 2.5). Acceptance criteria and technical requirements are distributed as structured `acceptance_criteria[]` on each plan item — not embedded in directive text. Design references are attached to UI-related plan items. For `modify` actions, only `unsatisfied_criteria[]` from `validation.json` are included (criteria already met by existing code are excluded). Technical requirements are converted to concrete acceptance criteria so the code agent verifies them in its self-check phase.
- **Nothing from the spec is silently dropped** — Phase 2.6 collects every acceptance criterion and DoD item that wasn't matched to a component in Phase 2.5. Unmatched criteria that require producing an artifact become additional plan items. Constraints on existing work go to the top-level `acceptance_criteria[]`. A verification step (2.6.3) ensures 100% coverage — no criterion goes unaccounted for.
- **Validator findings are trusted but reconsidered** — the synthesizer uses `validation.json` directly and does NOT re-scan the codebase. However, when the validator says `create` but provides medium+ confidence matches, the synthesizer escalates to `adjust` — the validator found something relevant but classified conservatively. Only `low` confidence matches are truly ignored for `create` status.
- **Conflict resolution is local** — conflicts are resolved using a simple rule (high confidence + <=2 differences = adjust, else create new). No loop back to the architect.
- **File paths only for modify** — `create` actions omit `file` because the implementation agent determines file paths. `modify` actions require `file` from the validator's best match.
- **Breaking changes cascade** — when an adjustment changes a protocol/interface, the synthesizer greps for consumers and generates additional `modify` plan items.
- **Composition root is context, not special** — `composition_root` from `arch.json` is used in directive text but processed through normal reconciliation like any other component.
- **Categorized routing for `adjust`** — Phase 2.1.3 routes on `(tag_set, match_confidence)` where `tag_set` is the distinct set of `differences[].category` values from `matches[0]`. `scope-mismatch` with medium/high confidence triggers coordinated extraction (2.1.3.2) — relocate the existing utility to a shared package and rewire consumers, never duplicate. `responsibility-mismatch` always drops to 2.1.4 conflict resolution. `missing-entry` is append-only modify. This replaces the previous ad-hoc 2.1.4-style override that silently chose `create` for cross-scope matches.
- **Extraction requires an existing shared dependency** — 2.1.3.2 reads both packages' manifests and picks one both already depend on. If no shared dependency path exists, the synthesizer does NOT create new shared packages — it falls through to `create` with an explicit reason. Creating new shared packages is an architectural decision left to the developer.
- **Cross-spec extraction halts the whole spec** — when 2.1.3.2 resolves a destination outside the current spec's ancestor chain (the destination's owning spec, read from its package `.claude/CLAUDE.md` frontmatter, is not in the lineage), the synthesizer stops the entire plan: `status: "blocked"`, `plan_items: []`, halt details in `requires_cross_spec_action[]`. The orchestrator (`/implement`) Phase 3.5 reads the status and exits before code-agent runs. Halting the whole spec (not just the affected component) is intentional — partial implementations are worse than no implementation when the user must decide on cross-spec scope. The user creates or updates a spec for the destination, sets the appropriate `blocked-by`, and re-runs.

## Gotchas

- **Don't determine file paths for `create` actions** — that's the implementation agent's job. Only `modify` actions have `file`.
- **Don't re-scan the codebase for matches** — `validation.json` has the matches. Only grep for consumers when handling breaking changes (Phase 2.2).
- **Multiple matches** — always use `matches[0]` (sorted by confidence descending). Document the choice.
- **Empty plan is valid** — if all components are `reuse`, `plan_items` is an empty array. This is success, not failure.
- **Malformed input = hard stop** — if either input JSON is missing required fields, abort entirely. No partial reconciliation.

## Schema

Output plan schema: `implementation-plan.schema.json` in this skill's directory.