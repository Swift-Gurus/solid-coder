# validate-decomposition — Architecture SOLID Validation

## Purpose

Validates an architecture decomposition (arch.json) against SOLID principles (SRP, OCP, ISP, LSP) at the architectural level — before any code is written or codebase is checked. Produces an adjusted arch.json with components split, protocols added, or hierarchies restructured as needed.

## Inputs / Outputs

| Direction | What | Format | Location |
|-----------|------|--------|----------|
| Input | Architecture decomposition | JSON (arch.schema.json) | `--arch-json` path |
| Input | Original spec | Markdown | `--spec` path |
| Output | Adjusted architecture | JSON (arch.schema.json) | `--output` path |

## Connects To

| Upstream | Relationship |
|----------|-------------|
| `skills/plan` | Produces the arch.json this skill validates |

| Downstream | Relationship |
|------------|-------------|
| `skills/validate-completeness` | Reads the adjusted arch.json |
| `skills/validate-plan` | Reads the final arch.json for codebase validation |

## Design Decisions

- **Architectural validation, not code validation** — checks component definitions (responsibility, interfaces, dependencies, wiring), not Swift code. SRP is about responsibility count, not method count.
- **Adjusts in place** — writes back to arch.json using the same schema. No separate findings format.
- **Preserves carry-forward fields** — acceptance_criteria, design_references, technical_requirements, test_plan are never modified.
- **No removal** — never removes components, only splits or adds. Removal is a completeness concern (validate-completeness handles that).