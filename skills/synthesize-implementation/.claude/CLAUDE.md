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
- **Spec context flows through arch.json** — `acceptance_criteria[]`, `design_references[]`, `design_decisions[]`, and `technical_requirements[]` are read from `arch.json` and embedded into individual plan item directives. Each directive gets only the criteria, designs, decisions, and technical specs relevant to its component. For `modify` actions, only `unsatisfied_criteria[]` from `validation.json` are included (criteria already met by existing code are excluded). Technical requirements carry verbatim code blocks (type definitions, file structure, API signatures) so the code agent has exact specifications.
- **Validator findings are trusted but reconsidered** — the synthesizer uses `validation.json` directly and does NOT re-scan the codebase. However, when the validator says `create` but provides medium+ confidence matches, the synthesizer escalates to `adjust` — the validator found something relevant but classified conservatively. Only `low` confidence matches are truly ignored for `create` status.
- **Conflict resolution is local** — conflicts are resolved using a simple rule (high confidence + <=2 differences = adjust, else create new). No loop back to the architect.
- **File paths only for modify** — `create` actions omit `file` because the implementation agent determines file paths. `modify` actions require `file` from the validator's best match.
- **Breaking changes cascade** — when an adjustment changes a protocol/interface, the synthesizer greps for consumers and generates additional `modify` plan items.
- **Composition root is context, not special** — `composition_root` from `arch.json` is used in directive text but processed through normal reconciliation like any other component.

## Gotchas

- **Don't determine file paths for `create` actions** — that's the implementation agent's job. Only `modify` actions have `file`.
- **Don't re-scan the codebase for matches** — `validation.json` has the matches. Only grep for consumers when handling breaking changes (Phase 2.2).
- **Multiple matches** — always use `matches[0]` (sorted by confidence descending). Document the choice.
- **Empty plan is valid** — if all components are `reuse`, `plan_items` is an empty array. This is success, not failure.
- **Malformed input = hard stop** — if either input JSON is missing required fields, abort entirely. No partial reconciliation.

## Schema

Output plan schema: `implementation-plan.schema.json` in this skill's directory.