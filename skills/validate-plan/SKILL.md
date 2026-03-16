---
name: validate-plan
description: Validates an architecture plan against the existing codebase — finds reusable types, identifies conflicts, and annotates each component with its reuse status.
argument-hint: <arch-json-path> --output <validation-json-path>
allowed-tools: Read, Grep, Glob, Bash, Write
user-invocable: true
---

# Codebase Validation

Takes an architect's decomposition (`arch.json`) and validates it against the existing codebase — finding reusable types, identifying conflicts, and annotating each component with its reuse status. Does NOT redesign the architecture.

## Input

- ARCH_JSON_PATH: $ARGUMENTS[0] — filepath to `arch.json` produced by `/plan`. Contains `spec_summary` for context.
- OUTPUT_PATH: value after `--output` flag — filepath where `validation.json` will be written.

## Phase 0: Prep — Generate Synonyms

- [ ] 0.1 Read `arch.json` from ARCH_JSON_PATH. Use `spec_summary` for context.
- [ ] 0.2 For each component in `arch.json`:
  - Split `responsibility` into keywords (remove stop words: the, a, an, is, are, with, from, for, to, of, and, or, in, on, by, that, this, it)
  - Add `category`
  - Generate 3 synonyms per keyword (semantic alternatives)
- [ ] 0.3 Merge all keywords and synonyms across all components into a single flat list.
- [ ] 0.4 Deduplicate and lowercase the list.
- [ ] 0.5 Store as a JSON array string for passing to the script.

## Phase 1+2: Codebase Search (Script)

- [ ] 1.1 Run the search script (pass `.` as sources — the script handles empty/missing dirs gracefully):
  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/skills/validate-plan/scripts/search-codebase.py \
    --sources <sources-dir> \
    --synonyms '<json-array-string>'
  ```
- [ ] 1.2 Parse the JSON output. If `files_matched` is 0, skip to Phase 4 and classify everything as `create`.

## Phase 3: Match Analysis (LLM)

Iterate over each matched file from the script output. For each file, analyze it against all architect components.

**FOR** each file in `matches[]` from script output **DO**:

- [ ] 3.1 Read the file's source code.
- [ ] 3.2 Extract `type_name` from the source code (class/struct/enum/protocol declaration).
- [ ] 3.3 For each architect component that could relate to this file:
  - Compare the file's methods, properties, and protocols against the component's `responsibility`, `interfaces`, and `dependencies`.
- [ ] 3.4 Analyze interface compatibility:
  - Does the type already conform to the needed protocols?
  - Could it conform with minor additions (new method, generic parameter)?
  - Does it need an adapter or wrapper?
  - Would it need a new protocol?
- [ ] 3.5 Score `match_confidence`:
  - `high` — same responsibility + compatible interface
  - `medium` — similar responsibility, interface needs work
  - `low` — overlapping keywords but different purpose
- [ ] 3.6 Record the match against the relevant component(s).

**END**

## Phase 4: Classification (LLM)

For each component, assign a status:

- [ ] 4.1 `create` — zero matches from script, or all matches scored `low`. Must be built from scratch.
- [ ] 4.2 `reuse` — match fulfills responsibility AND interface. No changes needed.
- [ ] 4.3 `adjust` — match fulfills responsibility but needs interface changes (new method, extended protocol, additional conformance, generic parameter).
- [ ] 4.4 `conflict` — match has same name or overlapping responsibility but incompatible design. Cannot reuse without major rework.

## Phase 5: Detail (LLM)

- [ ] 5.1 For `adjust` components:
  - List each change as a concrete action (e.g., "add method `fetchByCategory(_:)` to protocol `ProductReading`").
  - Grep for all call sites of the affected protocol/type to check for breaking changes.
  - If adjustment breaks existing consumers, set `"breaking": true` with affected files listed.
- [ ] 5.2 For `conflict` components:
  - Document what exists and why it's incompatible.
  - Suggest alternatives (rename, new type, adapter pattern).

## Phase 6: Output

- [ ] 6.1 Assemble `validation.json` with this structure:
  ```json
  {
    "components": [
      {
        "name": "ComponentName",
        "status": "create|reuse|adjust|conflict",
        "matches": [
          {
            "file": "path/to/file.swift",
            "type_name": "ExistingTypeName",
            "existing_interfaces": ["ProtocolA"],
            "match_confidence": "high|medium|low",
            "adjustments": [
              {
                "action": "add_method|add_conformance|add_protocol|wrap_adapter|extend_generic",
                "target": "TargetTypeOrProtocol",
                "detail": "concrete description of the change",
                "breaking": false,
                "affected_files": []
              }
            ],
            "notes": "Why this match was identified"
          }
        ],
        "best_match": 0
      }
    ],
    "summary": {
      "create": 0,
      "reuse": 0,
      "adjust": 0,
      "conflict": 0
    }
  }
  ```
- [ ] 6.2 Validate:
  - Every component from `arch.json` has an entry
  - `best_match` is `null` when `status` is `create`, otherwise an index into `matches[]`
  - `matches[]` is empty array for `create` status
  - Summary counts match actual statuses
- [ ] 6.3 Write `validation.json` to OUTPUT_PATH.

## Edge Cases

- **EC-1**: Multiple types match a single component — list all in `matches[]`, rank by `match_confidence`, set `best_match` to highest confidence.
- **EC-2**: Architect proposes splitting a monolithic type — classify as `adjust` with note about extraction needed.

## Constraints

- Do NOT redesign the architecture — only report what exists and how it fits.
- Do NOT modify any codebase files — this is read-only analysis.
- Do NOT read file contents beyond frontmatter in the script — the LLM reads full files in Phase 3.
- Keep `adjustments[].detail` concrete and actionable — the synthesizer (SPEC-004) uses these directly.
