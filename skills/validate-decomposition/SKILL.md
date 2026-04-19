---
name: validate-decomposition
description: Validates architecture decomposition against SOLID principles. Adjusts arch.json if violations found.
argument-hint: <arch-json-path> --spec <spec-path> --output <output-path>
allowed-tools: Read, Grep, Glob, Bash, Write
user-invocable: false
---

# Validate Decomposition

Validates an architecture decomposition (arch.json) against SOLID principles. Reads each component's responsibility, interfaces, dependencies, and wiring — checks for SRP, OCP, ISP, and LSP violations at the architectural level. Adjusts arch.json if violations are found.

## Input

- ARCH_PATH: $ARGUMENTS[0] — path to arch.json
- SPEC_PATH: value after `--spec` flag — path to original spec file (for context)
- OUTPUT_PATH: value after `--output` flag — path to write adjusted arch.json
- GATEWAY: ${CLAUDE_PLUGIN_ROOT}/mcp-server/gateway.py

## Phase 1: Load Context

- [ ] 1.1 Read arch.json from ARCH_PATH. Extract `components[]`, `wiring[]`, `composition_root`.
- [ ] 1.2 Read spec file from SPEC_PATH for context (what is being built).
- [ ] 1.3 Use skill **solid-coder:load-reference** with: `--mode planner` (loads rule statements + code_rules + patterns, with review-only content stripped)

## Phase 2: Validate Each Component

For EACH component in `components[]`:

- [ ] 2.1 **SRP check:**
  - Does `responsibility` describe a single verb/action?
  - Does the combination of `interfaces` + `dependencies` imply multiple cohesion groups?
    (e.g., a component that exposes a data-fetching protocol AND a formatting protocol uses disjoint concerns)
  - Validate against SRP severity bands in loaded rules.
  - SEVERE → flag for split.

- [ ] 2.2 **OCP check:**
  - Is every entry in `dependencies` a protocol name (not a concrete type)?
  - Check `wiring[]` — does any wiring entry use a concrete type in `to`?
  - Validate against OCP severity bands in loaded rules.
  - SEVERE → flag: add protocol interface.

- [ ] 2.3 **ISP check:**
  - For each protocol in `interfaces`, check how many consumers use it (scan `wiring[]` and `dependencies` of other components).
  - If a protocol is consumed by multiple components but some only need a subset of its methods → flag for split into role interfaces.
  - Validate against ISP severity bands in loaded rules.
  - SEVERE → flag: split protocol.

- [ ] 2.4 **LSP check:**
  - For each protocol in `interfaces`, consider the intended conformers.
  - Would any conformer need to leave methods empty or throw fatalError?
  - Would consumers need to type-check (`as?`, `is`) against specific conformers?
  - SEVERE → flag: redesign protocol hierarchy.

## Phase 3: Adjust

For each flagged component:

- [ ] 3.1 **SRP split** — split into separate components, each with a single responsibility. Update `wiring[]` to reflect the new dependency graph. The original component becomes a facade/coordinator if needed.
- [ ] 3.2 **OCP fix** — add protocol interfaces for concrete dependencies. Update `wiring[]`.
- [ ] 3.3 **ISP split** — split wide protocols into role interfaces. Update components that expose/consume them.
- [ ] 3.4 **LSP redesign** — restructure protocol hierarchy so all conformers can implement all methods meaningfully.

## Phase 4: Output

- [ ] 4.1 Assemble adjusted arch.json — same schema as input (`skills/plan/arch.schema.json`). Preserve all fields not modified (spec_summary, spec_number, mode, acceptance_criteria, design_references, technical_requirements, test_plan).
- [ ] 4.2 Validate adjusted arch.json:
  `! python3 {GATEWAY} validate_architecture --arch-path {OUTPUT_PATH}`
- [ ] 4.3 Write to OUTPUT_PATH.
- [ ] 4.4 Log adjustments: for each change, note what was flagged, which principle, and what was done.

## Constraints

- Do NOT change the spec or what is being built — only adjust HOW it's decomposed.
- Do NOT remove components — only split, add protocols, or restructure.
- Preserve `acceptance_criteria`, `design_references`, `technical_requirements`, `test_plan` unchanged.
- Output must conform to `skills/plan/arch.schema.json`.
- If no violations found → write arch.json unchanged.
