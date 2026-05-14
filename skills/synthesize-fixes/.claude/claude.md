---
name: synthesize-fixes-spec
description: Spec for the holistic fix planner skill — context, connections, design decisions, and gotchas.
type: spec
---

# Synthesize Fixes — Spec

## Purpose

Takes ALL review findings across ALL principles for a set of files and produces a unified, cross-checked fix plan per file. This is the only skill that sees the full picture — individual principle reviewers and fixers operate in isolation.

## Inputs / Outputs

| Direction | What | Format | Location |
|-----------|------|--------|----------|
| Input | Per-file review outputs | JSON (principle-specific schemas) | `{OUTPUT_ROOT}/by-file/*.output.json` |
| Input | Source files | Swift | Path from each output JSON's `file` field |
| Input | Principle fix knowledge | Markdown | `references/{PRINCIPLE}/fix/{METRIC_ID}.md` (per-metric files) |
| Output | Per-file fix plans | JSON (`plan.schema.json`) | `{OUTPUT_ROOT}/synthesized/{filename}.plan.json` |

## Connects To

| Upstream | Relationship |
|----------|-------------|
| `skills/run-code-review` | Produces the `by-file/*.output.json` files this skill consumes |
| `references/{PRINCIPLE}/fix/` | Per-metric fix files (`OCP-1.md`, `LSP-3.md`, etc.) — one file per metric ID |
| `mcp__plugin_solid-coder_docs__load_fix_instructions_for_findings` | Used in Phase 3.2 to batch-load all needed fix strategies for a file |
| `mcp__plugin_solid-coder_docs__load_fix_for_violation` | Used in Phase 4.3 for on-demand cross-check patch loading |

| Downstream | Relationship |
|------------|-------------|
| `skills/code` (via code-agent) | Consumes `plan.json` to implement the actual code changes |
| `skills/refactor` Phase 8 | Iteration loop — if changes introduce new issues, the full review/synthesize/implement cycle re-runs on modified files |

## Key Design Decisions

- **Per-metric on-demand loading** — fix knowledge is loaded per `(principle, metric_id)` pair via `load_fix_instructions_for_findings` (batch, Phase 3.2) and `load_fix_for_violation` (single, Phase 4.3). Only the strategies for violated metrics are loaded — not full fix/instructions.md files. Reduces context by ~75% vs bulk loading.
- **Principle ordering** — Phase 3 deduplicates first, then processes smallest-to-largest blast radius: DRY -> Functions -> UI -> OCP -> LSP -> ISP -> SRP. DRY runs first so all subsequent principles operate on deduplicated code.
- **Single-principle drafting, cross-principle verification** — Phase 3 drafts focus on one principle at a time. Phase 4 cross-checks against all others. This separation prevents conflated fixes.
- **Inline cross-check guidance** — Phases 4.2 and 4.3 include per-principle quick-reference checklists (SRP, OCP, LSP, ISP, SwiftUI) so the agent doesn't have to derive what to check from rule.md alone. These are summaries, not replacements — rule.md is still loaded and applied.
- **Single-attempt patching** — if a cross-check or post-merge validation fails and the patch also fails, mark as `unresolved`. No recursive fix loops. The iteration loop (refactor Phase 8) is the retry mechanism.
- **Unresolved is not failure** — unresolved findings resurface as new findings in the next iteration's fresh review. The iteration loop (refactor Phase 8) is the safety net, not this skill.
- **Phase 6 scoped to merged actions only** — Phase 5 merges can introduce violations that didn't exist in individually-verified drafts. Phase 6 re-validates only those merged actions, not all actions.
- **Completeness invariant** — every finding must appear in exactly one action's `resolves[]` or in `unresolved[]`. No finding can be silently dropped.

## Gotchas

- **Don't invent findings** — only address findings from review outputs. The synthesizer fixes, it doesn't review.
- **Fix knowledge loaded in Phase 3.2, not Phase 2** — The batch tool loads all needed metric fix files for a file at once. Phase 4.3 calls `load_fix_for_violation` for cross-check failures where the failing principle's metric wasn't in the original finding set.
- **Cross-iteration state is not passed forward** — subsequent iterations run a fresh review on modified files. `unresolved[]` from plan.json is informational within the iteration; it's not fed as input to the next one.
- **Public API preservation** — fixes must not change the external interface of source files.
- **OCP vs SUI-4 overlap** — both can flag a concrete ViewModel dependency. OCP flags sealed points generically; SUI-4 flags SwiftUI-specific VM injection. The synthesizer's cross-check (Phase 4) handles deduplication — don't treat this as a conflict.

## Schema

Output plan schema: `plan.schema.json` in this skill's directory. Key fields per action: `suggestion_id`, `principle`, `resolves[]`, `suggested_fix`, `todo_items[]`, `depends_on[]`, `cross_check_results[]`, `note`. Top-level also has `unresolved[]` and `conflicts_detected[]`.