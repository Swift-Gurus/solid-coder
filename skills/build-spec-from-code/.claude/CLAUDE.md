---
number: SPEC-009
feature: build-spec-from-code
status: done
blocked-by: []
blocking: []
---

# build-spec-from-code — Code-to-Spec Generator

## Description

User-invocable skill that reads existing code, extracts functionalities as user stories, builds an integration map, interviews the user about the desired target state, and produces a rewrite spec with subtasks. The spec has `mode: rewrite` in frontmatter so the implement pipeline treats it as greenfield.

## Input

- `$ARGUMENTS[0]` — file path(s) or directory pointing at existing code to analyze.

## Output

- Parent spec with `mode: rewrite`, `## Current State` section, user stories (target behavior), integration map
- Rebuild subtask (`mode: rewrite`) — greenfield implementation
- Bridge subtask (conditional) — adapter between old and new interfaces
- Migrate subtask (conditional) — update consumers to use new interface directly

All written to `.claude/specs/` following the hierarchy.

## Connects To

| Skill | Relationship |
|-------|-------------|
| **solid-coder:find-spec** | Spec numbering (`next-number`), parent selection, ancestor loading |
| **solid-coder:validate-spec** | Buildability gate (`--interactive`) on all generated specs |
| **build-spec-query.py** | Path resolution (`resolve-path`) — reuses build-spec's script |

| Downstream | Relationship |
|------------|-------------|
| `/implement` | Consumes generated specs. Rebuild subtask triggers rewrite mode in validate-plan. |
| `validate-plan` | Reads `mode: rewrite` from arch.json, skips search, classifies all as `create` |

## Design Decisions

- **Functionalities over architecture** — analysis extracts what the code does (user stories with edge cases as acceptance criteria), not how it's structured. Target architecture is decided in the interview, not inherited from current state.
- **LLM analysis, not AST** — uses Read + Grep, no new Python script. Language-flexible. Future S-26 (tree-sitter) would improve accuracy.
- **Interview after analysis** — show extracted stories + diagrams + integration map before asking what to change. User makes informed decisions.
- **Conditional subtasks** — bridge/migrate only if consumers found AND user confirms. Avoids unnecessary work for isolated components.
- **`mode: rewrite` in frontmatter** — clean signal that flows through pipeline. validate-plan handles it internally, orchestrator unchanged.
- **Rebuild is greenfield** — the whole point of rewrite mode. Integration with old world is a separate subtask with its own spec.
- **Reuses build-spec infrastructure** — path resolution, spec numbering, validate-spec, same spec format. No duplication.
- **Black box analysis** — diagrams treat the current component as a black box: hide internals, show only inputs/outputs/external connections. This captures the interface contract the rewrite must satisfy, not the implementation to replace.
- **Diagrams from code** — flow, sequence, and connection diagrams generated during analysis and presented to user before interview. Both current state and target state diagrams included in the spec.
- **Technical Requirements are boundary-only** — capture what the component must satisfy (needs authenticated user context, must handle offline), not how the old code did it (uses SessionProvider.shared, checks Reachability singleton). The section adapts to context: UI rewrites get colors/fonts/screenshots, non-UI get API contracts/performance/threading.
- **Subtasks are scaffolds** — rebuild/bridge/migrate subtasks get frontmatter only. The user runs `/build-spec` on each subtask to flesh it out, then task breakdown. This skill doesn't write subtask bodies.

## Gotchas

- Large targets (50+ files) may overwhelm context. The skill warns and suggests narrowing scope.
- Mixed concerns in the target code should produce multiple rewrite specs, not one massive spec.
- The integration map is critical for the bridge subtask — if consumers are missed, the bridge will be incomplete.
- Rebuild subtask depends on S-43 (validate-plan rewrite mode bypass) being implemented.