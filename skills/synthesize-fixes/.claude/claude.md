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
| Input | Principle fix knowledge | Markdown | `{RULES_PATH}/{PRINCIPLE}/rule.md`, `fix/instructions.md` |
| Output | Per-file fix plans | JSON (`plan.schema.json`) | `{OUTPUT_ROOT}/synthesized/{filename}.plan.json` |

## Connects To

| Upstream | Relationship |
|----------|-------------|
| `skills/run-code-review` | Produces the `by-file/*.output.json` files this skill consumes |
| `references/{PRINCIPLE}/` | Each principle folder provides `rule.md` (metrics), `fix/instructions.md` (fix patterns) |
| `mcp__plugin_solid-coder_docs__load_rules` | Used in Phase 2 to load rule definitions and fix instructions |

| Downstream | Relationship |
|------------|-------------|
| `skills/code` (via code-agent) | Consumes `plan.json` to implement the actual code changes |
| `skills/refactor` Phase 8 | Iteration loop — if changes introduce new issues, the full review/synthesize/implement cycle re-runs on modified files |

## Key Design Decisions

- **Dynamic knowledge loading** — only loads fix knowledge for principles that have findings. Keeps context bounded as principles scale. Don't preload everything.
- **Principle ordering** — Phase 3 deduplicates first, then processes smallest-to-largest blast radius: DRY -> Functions -> UI -> OCP -> LSP -> ISP -> SRP. DRY runs first so all subsequent principles operate on deduplicated code.
- **Single-principle drafting, cross-principle verification** — Phase 3 drafts focus on one principle at a time. Phase 4 cross-checks against all others. This separation prevents conflated fixes.
- **Inline cross-check guidance** — Phases 4.2 and 4.3 include per-principle quick-reference checklists (SRP, OCP, LSP, ISP, SwiftUI) so the agent doesn't have to derive what to check from rule.md alone. These are summaries, not replacements — rule.md is still loaded and applied.
- **Single-attempt patching** — if a cross-check or post-merge validation fails and the patch also fails, mark as `unresolved`. No recursive fix loops. The iteration loop (refactor Phase 8) is the retry mechanism.
- **Unresolved is not failure** — unresolved findings resurface as new findings in the next iteration's fresh review. The iteration loop (refactor Phase 8) is the safety net, not this skill.
- **Phase 6 scoped to merged actions only** — Phase 5 merges can introduce violations that didn't exist in individually-verified drafts. Phase 6 re-validates only those merged actions, not all actions.
- **Completeness invariant** — every finding must appear in exactly one action's `resolves[]` or in `unresolved[]`. No finding can be silently dropped.

## Gotchas

- **Don't invent findings** — only address findings from review outputs. The synthesizer fixes, it doesn't review.
- **Principle knowledge comes from Phase 2 lookup only** — Phases 3-6 all reuse the same loaded knowledge. No separate recipe files, no re-loading.
- **Cross-iteration state is not passed forward** — subsequent iterations run a fresh review on modified files. `unresolved[]` from plan.json is informational within the iteration; it's not fed as input to the next one.
- **Public API preservation** — fixes must not change the external interface of source files.
- **OCP vs SUI-4 overlap** — both can flag a concrete ViewModel dependency. OCP flags sealed points generically; SUI-4 flags SwiftUI-specific VM injection. The synthesizer's cross-check (Phase 4) handles deduplication — don't treat this as a conflict.

## Schema

Output plan schema: `plan.schema.json` in this skill's directory. Key fields per action: `suggestion_id`, `principle`, `resolves[]`, `suggested_fix`, `todo_items[]`, `depends_on[]`, `cross_check_results[]`, `note`. Top-level also has `unresolved[]` and `conflicts_detected[]`.