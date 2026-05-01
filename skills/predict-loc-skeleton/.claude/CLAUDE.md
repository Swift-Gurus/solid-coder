# predict-loc-skeleton — Spec

## Purpose

Produces an accuracy-grade LOC estimate by drafting declaration-only skeleton code in the project's language and counting it. Runs in parallel with `predict-loc-heuristic`. The two estimates feed `scope-synthesize`, which takes the higher and flags calibration drift when they disagree by more than 50%.

The skeleton is also a side-channel buildability check — types or methods the agent cannot sketch get listed under `unsketched`, surfacing under-specification that the regular Phase B scan might miss.

## Inputs / Outputs

| Direction | Type     | Format        | Source / Destination |
|-----------|----------|---------------|----------------------|
| Input     | Spec file | Markdown + YAML frontmatter | `$ARGUMENTS[0]` |
| Input     | Output directory | Filesystem path | `$ARGUMENTS[1]` |
| Output    | Skeleton files | Source code (decl only) | `{OUTPUT_DIR}/skeleton/*.{swift,kt,ts,py}` |
| Output    | Skeleton JSON | Structured | `{OUTPUT_DIR}/skeleton.json` matching `output.schema.json` |

## Connects To

| Direction | Module | Relationship |
|-----------|--------|-------------|
| Wrapped by | `predict-loc-skeleton-agent` | Sonnet wrapper for parallel execution under Phase C |
| Upstream | `validate-spec` | Spawns this skill in Phase 4 (Scope & Cohesion) |
| Downstream | `scope-synthesize` | Reads `skeleton.json` to compute consensus LOC and calibration drift |

## Key Design Decisions

- **Behavioural sketch, not declaration-only** — placeholder bodies hid the actual signal: a retry loop and a getter would count the same. Real logic in the bodies captures per-method complexity. The multiplier covers minor production overhead (extensions, conformance scaffolding, accessor synthesis), not missing logic — so it's small (Swift 1.15, Kotlin/TS 1.10, Python 1.20).
- **Naive impl, no hardening** — the agent doesn't add error handling, defensive checks, or optimisations the ACs don't require. Production code typically adds those, hence the >1 multiplier — but the gap is small enough that the skeleton's per-spec LOC accuracy beats the heuristic.
- **Sonnet, not Haiku** — drafting real logic requires understanding the spec's intent (which types are implied vs which are external dependencies) and producing correct syntax. Haiku is too brittle for this.
- **Project language detection, default Swift** — uses the dominant source extension under the project root. Swift wins by default because that's the codebase's primary target. Other languages get correct multipliers without touching the orchestrator.
- **Unsketched is a buildability signal** — if a type or behavior is mentioned in the spec but the agent can't determine its shape, it lands in `unsketched`. That's a hint to the human reviewer that the spec is missing something concrete (and the regular Phase B should also flag it).
- **Multipliers are calibration knobs** — hardcoded for now. Promote to a config file if/when calibration data shows they need per-spec or per-team tuning.

## Gotchas

- Don't include test code in the skeleton — tests scale mechanically with ACs and are excluded from the production-LOC metric.
- The skeleton lives under `{OUTPUT_DIR}/skeleton/`, alongside the JSON. It's a debugging artifact; don't depend on its existence after a run completes (callers may clean it up).
- Multi-file sketches: when a protocol has multiple conformers, sketch each in its own file. The line count aggregates.
- If the project is greenfield (no existing source), language detection falls back to Swift. Override is via spec frontmatter (future), not currently implemented.
