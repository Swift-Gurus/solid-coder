# propose-split — Spec

## Purpose

Produces a full split blueprint when `scope-assessment.json` recommends splitting. Reads the original spec for context (TR text, Connects To rows, AC bodies) and partitions content across candidate subtasks. Output is a JSON plan, not Spec.md files — materialisation is downstream (build-spec or human).

## Inputs / Outputs

| Direction | Type     | Format        | Source / Destination |
|-----------|----------|---------------|----------------------|
| Input     | Spec file | Markdown + YAML frontmatter | `$ARGUMENTS[0]` |
| Input     | Scope assessment | JSON | `{OUTPUT_DIR}/scope-assessment.json` (must exist; produced by scope-synthesize) |
| Output    | Split plan | Structured | `{OUTPUT_DIR}/split-plan.json` matching `output.schema.json` |

## Connects To

| Direction | Module | Relationship |
|-----------|--------|-------------|
| Wrapped by | `propose-split-agent` | Sonnet wrapper — partitioning needs intent understanding |
| Upstream | `scope-synthesize` | Reads its `scope-assessment.json`; only proceeds when `verdict == needs_split` |
| Upstream | `validate-spec` | Phase 4.7 spawns this skill |
| Downstream | `validate-spec` Phase 4 reporting | Embeds the split plan in the `split_recommendation` finding body |
| Downstream | `build-spec` (future) | Could consume `split-plan.json` to materialise candidate Spec.md files |

## Key Design Decisions

- **Reads the spec, not just scope-assessment** — the synthesizer's structured data has cohesion groups + AC ids, but partitioning TR bullets, IO rows, and Connects To across candidates requires reading the actual prose. Without the spec context, the plan would be a stub that the user has to fill in by hand.
- **Two branches: cohesion-driven vs size-driven** — cohesion has clean seams (groups become subtasks); size-driven (oversized_cohesive) has no seam, so the plan suggests extraction candidates instead of full splits. Keeping these as separate phases avoids muddling the two cases.
- **No materialisation** — emits a plan, not files. Materialising risks coupling validate-spec to spec-generation, which should stay in build-spec's lane. The plan is a clean handoff.
- **AC text verbatim** — quote, don't paraphrase. The plan must be diff-reviewable against the parent. If an AC moved, a reviewer should see exactly the same words in the candidate.
- **Cycle detection in dependencies** — if the cohesion grouping produces a cyclic dependency between candidates (A needs B, B needs A), the split is architecturally invalid; fail loudly so the human reviews. Don't silently break the cycle.
- **Sonnet, not Opus** — partitioning is structured pattern-matching against well-defined sections. Sonnet handles it. Opus would be overkill for this tier of work.

## Gotchas

- The `verdict != "needs_split"` early-exit emits `{"applicable": false}` — downstream consumers must check `applicable` before reading the rest.
- TR bullets often describe cross-cutting mechanisms; the agent may need to split a single TR bullet into per-candidate fragments. Mark provenance so the partition is auditable.
- Parent residue (cohesion-driven case) is structurally what build-spec produces for an index feature. The plan should be drop-in compatible with that shape.
- Inter-subtask dependencies: only flag `blocked_by` when the data flow is real (output of A is input to B). Avoid speculative ordering "just because".
