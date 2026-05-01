# predict-loc-heuristic — Spec

## Purpose

Produces a fast, deterministic LOC estimate for a spec using the AC + screen heuristic. Runs in parallel with `predict-loc-skeleton` so the synthesizer always has two independent size signals — the heuristic for cheap baseline, the skeleton for accuracy.

## Inputs / Outputs

| Direction | Type     | Format        | Source / Destination |
|-----------|----------|---------------|----------------------|
| Input     | Spec file | Markdown + YAML frontmatter | `$ARGUMENTS[0]` — absolute path |
| Input     | Output directory | Filesystem path | `$ARGUMENTS[1]` — must exist before invocation |
| Output    | Heuristic JSON | Structured | `{OUTPUT_DIR}/heuristic.json` matching `output.schema.json` |

## Connects To

| Direction | Module | Relationship |
|-----------|--------|-------------|
| Wrapped by | `predict-loc-heuristic-agent` | Haiku wrapper for parallel execution under Phase C |
| Upstream | `validate-spec` | Spawns this skill in Phase 4 (Scope & Cohesion) |
| Downstream | `scope-synthesize` | Reads `heuristic.json` to compute consensus LOC |

## Key Design Decisions

- **Script-backed, not LLM-backed** — counting ACs and screens is mechanical. A script gives deterministic output and zero per-invocation cost beyond Haiku invocation overhead. Promote to LLM judgment only if AC granularity becomes ambiguous.
- **AC = bullet under user story** — only counts `- ` bullets directly following a `### US-N:` heading, stopping at the next `##` or `###`. Avoids miscounting test cases (under `## Test Plan`) or DoD items.
- **Screen = mockup subsection or image** — counts `### ` headings under `## UI / Mockup` plus inline `![](...)` image references; takes the max. Falls back to 1 if the section exists but contains no structural markers.
- **Bands live in README** — formula and severity bands come from `spec-driven-development/specs/README.md § Scope Metrics`. The script must stay in sync if those bands change.

## Gotchas

- Don't count ACs that appear under non-story headings (e.g., test plan, DoD). The script is heading-aware.
- Empty spec files produce `predicted_loc: 0, severity: COMPLIANT`. That's correct behavior for a brand-new draft.
- The skeleton agent's output uses a different shape (`projected_loc` vs `predicted_loc`); don't conflate the two when reading them in synthesis.
