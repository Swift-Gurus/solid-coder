# cohesion-cluster — Spec

## Purpose

Detects architectural seams in a spec by extracting structured signals from each AC and clustering them. Each resulting group is a candidate subtask boundary if a split is recommended. Runs in parallel with `predict-loc-heuristic` and `predict-loc-skeleton` under Phase C.

## Inputs / Outputs

| Direction | Type     | Format        | Source / Destination |
|-----------|----------|---------------|----------------------|
| Input     | Spec file | Markdown + YAML frontmatter | `$ARGUMENTS[0]` |
| Input     | Output directory | Filesystem path | `$ARGUMENTS[1]` |
| Output    | Cohesion JSON | Structured | `{OUTPUT_DIR}/cohesion.json` matching `output.schema.json` |

## Connects To

| Direction | Module | Relationship |
|-----------|--------|-------------|
| Wrapped by | `cohesion-cluster-agent` | Sonnet wrapper for parallel execution under Phase C |
| Upstream | `validate-spec` | Spawns this skill in Phase 4 (Scope & Cohesion) |
| Downstream | `scope-synthesize` | Reads `cohesion.json` to produce split candidates and verdict |

## Key Design Decisions

- **4-signal extraction** — data type, screen, external integration, lifecycle phase. Lifecycle is the discriminator that pulls construction concerns away from runtime concerns; without it, factory ACs cluster with the things they construct.
- **2-signal cluster rule** — sharing only one kind (e.g. same library name) folds everything together. Sharing two (e.g. same data type AND same lifecycle phase) is the threshold that produces splits matching real architectural seams. Calibrated against SPEC-041 and SPEC-045.
- **Group labels are LLM-generated** — the cluster has the most context to name the seam ("decorator runtime" vs "built-in policies"). Labels are advisory; humans rename when materialising subtasks.
- **Sonnet, not Haiku** — signal extraction needs intent understanding. The 4-signal taxonomy is structured, but applying it to natural-language ACs requires judgment about what "the same data type" means in context.
- **Deliberately strict** — better to miss a borderline split than to flag a cohesive spec as needing one. Severity SEVERE means group_count ≥ 3, which is a strong signal.

## Gotchas

- AC ids must be stable (`US-{n}.{m}` based on bullet position) so downstream split-recommendation can reference them.
- Don't conflate "external integration" with "data type" — `AsyncSequence` is an integration even though it's also a generic type. Integration is the *thing being wired up*; data type is the payload.
- Empty user stories or stories with no ACs produce zero groups — `group_count: 0` is valid and maps to COMPLIANT (nothing to cluster).
- The lifecycle taxonomy is closed: pick from {construction, subscribe, observation, cancel, mutation, teardown}. If an AC doesn't fit, it's `subscribe` (the catch-all runtime phase).
