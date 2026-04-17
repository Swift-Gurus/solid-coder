# validate-completeness — Spec Coverage Validation

## Purpose

Validates that an architecture decomposition (arch.json) covers all requirements from the original spec. Uses a "reconstruct and diff" approach: describes what the architecture would deliver, compares against the spec, and adds components for any gaps.

## Inputs / Outputs

| Direction | What | Format | Location |
|-----------|------|--------|----------|
| Input | Adjusted architecture | JSON (arch.schema.json) | `--arch-json` path |
| Input | Original spec | Markdown | `--spec` path |
| Output | Final architecture | JSON (arch.schema.json) | `--output` path |

## Connects To

| Upstream | Relationship |
|----------|-------------|
| `skills/validate-decomposition` | Produces the adjusted arch.json this skill reads |

| Downstream | Relationship |
|------------|-------------|
| `skills/validate-plan` | Reads the final arch.json for codebase validation |
| `skills/synthesize-implementation` | Reads the final arch.json for implementation planning |

## Design Decisions

- **Reconstruct, don't checklist** — instead of checking "does component X cover story Y?", the agent reconstructs what the arch delivers and diffs. This catches gaps that a direct mapping would miss (e.g., a story that needs two components working together, neither of which individually "covers" it).
- **Only adds, never removes** — existing components were validated by decomposition. This skill only fills gaps.
- **Requirement numbering** — every spec requirement gets a REQ-N ID for traceability in the coverage table. This makes gaps explicit and auditable.
- **Coverage table is the artifact** — even if no gaps found, the table documents that everything was checked.
