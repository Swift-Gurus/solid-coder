---
number: SPEC-001
feature: implement
status: done
blocked-by: [SPEC-002, SPEC-003, SPEC-004]
blocking: []
---

# /implement — Spec-to-Code Orchestrator

## Purpose

Top-level orchestrator that takes a feature spec file and coordinates sub-skills to architect, validate, synthesize, implement, and review — all in one command. Does not write code itself.

## Inputs / Outputs

| Direction | What | Format | Location |
|-----------|------|--------|----------|
| Input | Feature spec | Markdown with YAML frontmatter (`number` field required) | User-provided path |
| Output | Architecture decomposition | JSON | `{OUTPUT_ROOT}/arch.json` |
| Output | Codebase validation | JSON | `{OUTPUT_ROOT}/validation.json` |
| Output | Implementation plan | JSON | `{OUTPUT_ROOT}/implementation-plan.json` |
| Output | Source files | Swift | Created/modified by code-agent |
| Output | Orchestrator log | JSON | `{OUTPUT_ROOT}/implement-log.json` |

`OUTPUT_ROOT` = `CURRENT_PROJECT/.solid_coder/implement-{spec-number}-<YYYYMMDDhhmmss>/`

## Flow

```
spec file → Phase 1: /plan → arch.json
                                 ↓
           Phase 2: /validate-plan → validation.json
                                 ↓
           Phase 3: /synthesize-implementation → implementation-plan.json
                                 ↓
           Phase 4: code-agent → source files
                                 ↓
           Phase 4.5: /validate-implementation → user screenshots + feedback
                      ↓ approved        ↓ has_fixes
                      ↓           code-agent fixes → re-validate
                      ↓                ↓
           Phase 5: /refactor changes --iterations 1 → safety review
```

## Connects To

| Skill/Agent | Phase | Relationship |
|-------------|-------|-------------|
| `mcp__plugin_solid-coder_specs__parse_spec` | 0 | Validates spec frontmatter |
| `solid-coder:plan` | 1 | Produces `arch.json` |
| `solid-coder:validate-implementation` | 4.5 | User checkpoint — collects screenshots/feedback, gates refactor |
| `solid-coder:validate-plan` | 2 | Produces `validation.json` |
| `solid-coder:synthesize-implementation` | 3 | Produces `implementation-plan.json` |
| `code-agent` | 4 | Executes plan items, writes source files |
| `solid-coder:refactor` | 5 | Reviews implemented code against principles |

## Design Decisions

- **Orchestrator never reads phase outputs** — only passes file paths between phases. This keeps the orchestrator thin and decoupled from schema changes.
- **No loopback** — the synthesizer reconciles arch/validation conflicts. The orchestrator is strictly sequential.
- **No short-circuit** — even when `plan_items[]` is empty (all reuse), all phases run. This keeps the orchestrator simple and predictable. Short-circuiting is a future improvement.
- **Phase 5 defaults to 1 iteration** — safety review runs by default. Use `--iterations 0` to skip. Stages all Phase 4 output via `git add`, then runs `/refactor changes --iterations N`.
- **Logging is opt-in** — per-phase timestamps and `implement-log.json` only written when `--verbose` is passed. Default: off.
- **Partial failure preserved** — if code-agent fails mid-plan, completed items are kept. No rollback.

## Gotchas

- Input MUST be a spec file with frontmatter — inline prompts are not accepted.
- The `number` field in frontmatter is used for the `OUTPUT_ROOT` directory name.
- Phase 5 violations are informational, not blocking — the implementation is considered complete.
- `implement-log.json` is only written when `--verbose` is used.