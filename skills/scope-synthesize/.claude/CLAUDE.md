# scope-synthesize — Spec

## Purpose

Deterministically merges the three Phase C measurement outputs (heuristic LOC, skeleton LOC, cohesion clusters) into a single `scope-assessment.json` containing the verdict, consensus size, and split candidates. The single artifact is the public contract for any downstream consumer of validate-spec scope results.

## Inputs / Outputs

| Direction | Type     | Format        | Source / Destination |
|-----------|----------|---------------|----------------------|
| Input     | heuristic.json | matches `predict-loc-heuristic/output.schema.json` | `{OUTPUT_DIR}/heuristic.json` |
| Input     | skeleton.json | matches `predict-loc-skeleton/output.schema.json` | `{OUTPUT_DIR}/skeleton.json` |
| Input     | cohesion.json | matches `cohesion-cluster/output.schema.json` | `{OUTPUT_DIR}/cohesion.json` |
| Output    | scope-assessment.json | matches `output.schema.json` (public contract) | `{OUTPUT_DIR}/scope-assessment.json` |

## Connects To

| Direction | Module | Relationship |
|-----------|--------|-------------|
| Wrapped by | `scope-synthesize-agent` | Haiku wrapper, script-invoker |
| Upstream | `predict-loc-heuristic` | Reads its output |
| Upstream | `predict-loc-skeleton` | Reads its output |
| Upstream | `cohesion-cluster` | Reads its output |
| Downstream | `validate-spec` | Phase 4 reads `scope-assessment.json` and turns it into Phase C findings |
| Downstream | (any future scope consumer) | Public contract; do not break the schema without coordination |

## Key Design Decisions

- **Pure script, no LLM** — the merge is comparison + banding + dictionary assembly. Every step is deterministic. Adding LLM judgment would introduce non-determinism for no benefit.
- **`max(heuristic, skeleton×mult)` consensus** — conservative. Either signal alone could mis-estimate; the higher number is the safer scope estimate.
- **Calibration drift threshold = 50%** — if the two LOC estimates disagree by more than half of the higher one, the formula or the multiplier is miscalibrated. Logged as `calibration_drift: true` so it's visible in reports.
- **Cohesion drives split decisions** — when both severities trip, cohesion wins because it tells you *where* to split, not just *that* you should.
- **`oversized_cohesive` is its own outcome** — a cohesive unit that's just large doesn't have a clean split. The verdict is `needs_split` with `driver: size`, but the split candidate is empty; the consumer (validate-spec) renders this as a different finding category for human review.
- **Estimated size bands per group** — `consensus_loc / group_count` rounded to bands {tiny < 50, small < 150, medium < 300, large ≥ 300}. Approximation; refined later if `predict-loc-skeleton` starts attributing LOC per AC.

## Gotchas

- The three input files must all exist before invocation. Validate-spec waits for the parallel subagents to complete before launching this one. Missing files cause script failure (exit 2).
- `scope-assessment.json` overwrites any previous run's output in the same directory — that's intentional.
- The schema for `scope-assessment.json` is the public contract; bumping it requires updating consumers (currently just validate-spec Phase 4).
- Cohesion `group_count: 0` (empty spec) maps to verdict `compliant` — there's nothing to assess.
