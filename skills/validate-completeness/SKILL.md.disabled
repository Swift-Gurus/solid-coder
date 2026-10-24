---
name: validate-completeness
description: "Phase 1.7b: Compares reconstructed spec against original spec, flags gaps, adds missing components to arch.json."
argument-hint: <arch-json-path> --spec <spec-path> --reconstructed <reconstructed-spec-path> --output <output-path>
allowed-tools: Read, Grep, Glob, Bash, Write
user-invocable: false
---

# Validate Completeness (Compare)

Reads a reconstructed spec (what the architecture would deliver) and the original spec (what was asked for). Diffs them. Adds components to arch.json for any gaps.

## Input

- ARCH_PATH: $ARGUMENTS[0] — path to arch.json
- SPEC_PATH: value after `--spec` flag — path to original spec file
- RECONSTRUCTED_PATH: value after `--reconstructed` flag — path to reconstructed-spec.md (from reconstruct-spec agent)
- OUTPUT_PATH: value after `--output` flag — path to write adjusted arch.json

## Phase 1: Normalize Original Spec

- [ ] 1.1 Read the **original spec** from SPEC_PATH.
- [ ] 1.2 Extract every verifiable requirement and normalize each into a **Given/When/Then triple**:
  - From each acceptance criterion → G/W/T
  - From each Definition of Done item → G/W/T (Given: implementation complete, When: checking, Then: condition holds)
  - From each test plan entry → already in G/W/T format, use directly
  - From each technical requirement → G/W/T (Given: system context, When: relevant operation, Then: constraint satisfied)
  Number each: REQ-1, REQ-2, ...

  Example:
  ```
  AC: "When the probe returns empty, the config root defaults to ~/.claude/"
  REQ-7: Given probe returns empty | When config root is resolved | Then result is ~/.claude/
  ```

## Phase 2: Normalize Reconstructed Spec

- [ ] 2.1 Read the **reconstructed spec** from RECONSTRUCTED_PATH.
- [ ] 2.2 Extract every verifiable capability and normalize into the same **Given/When/Then triple** format.
  Number each: REC-1, REC-2, ...

## Phase 3: Match

Match requirements by **semantic equivalence of the G/W/T structure**, not by wording. Two triples match when:
- The **trigger** is the same (When: same action or condition)
- The **precondition** is compatible (Given: same or more specific setup)
- The **outcome** is the same (Then: same observable result)

Different words for the same concept are a match (e.g., "config root" = "data root", "typed error" = "error with explanation", "probe returns empty" = "probe returns empty string").

- [ ] 3.1 For EACH REQ, find the best matching REC:
  - **COVERED** — a REC triple matches on trigger + precondition + outcome
  - **PARTIAL** — a REC triple matches on trigger but outcome differs or is incomplete
  - **GAP** — no REC triple has a matching trigger

- [ ] 3.2 Produce a coverage table:

  | Req ID | Given / When / Then | Status | Matched REC | Gap Description |
  |--------|---------------------|--------|-------------|-----------------|

## Phase 3: Fill Gaps

For EACH requirement marked GAP or PARTIAL:

- [ ] 3.1 Read arch.json from ARCH_PATH.
- [ ] 3.2 Determine what component is needed:
  - Missing service, view, model, test target, or protocol?
- [ ] 3.3 Define the new component following arch.json conventions (name, category, stack, responsibility, interfaces, dependencies, produces, fields).
- [ ] 3.4 Add wiring entries if the new component depends on existing components.

## Phase 4: Output

- [ ] 4.1 **Always write coverage report** — write `coverage.json` as a sibling of OUTPUT_PATH:
  ```json
  {
    "coverage": [
      {"req_id": "REQ-1", "given_when_then": "...", "status": "COVERED", "matched_rec": "REC-3", "gap": null},
      {"req_id": "REQ-7", "given_when_then": "...", "status": "GAP", "matched_rec": null, "gap": "No component handles..."}
    ],
    "summary": {"total": 17, "covered": 15, "partial": 1, "gaps": 1}
  }
  ```
- [ ] 4.2 If OUTPUT_PATH ends in `.json` (arch.json) → add new components and wiring, preserve all other fields, write adjusted arch.json to OUTPUT_PATH.
- [ ] 4.3 If no gaps found → write arch.json unchanged.
- [ ] 4.4 Log: coverage table + each gap found + component added (if any).

## Constraints

- Do NOT modify existing components — only add new ones.
- Do NOT read arch.json before reading both specs (avoid bias from seeing the architecture first).
- When OUTPUT_PATH is arch.json, output must conform to `skills/plan/arch.schema.json`.
- Every requirement must appear in the coverage table — nothing silently dropped.
