---
number: SPEC-006
feature: validate-plan-data-models
status: draft
blocked-by: []
blocking: [SPEC-004]
---

# Bug: validate-plan ignores data_models[]

## Problem

`/validate-plan` only searches the codebase for `components[]` from `arch.json`. It completely ignores `data_models[]`. Since validate-plan's purpose is finding duplicates and classifying reuse status, data models should be its responsibility — not the synthesizer's.

Currently `arch.json` schema requires `data_models[]` (each with `name`, `category`, `fields[]`), but `validation.json` schema has no corresponding output for them.

## Expected Behavior

validate-plan should search the codebase for each data model in `arch.json`, classify it (`create`/`reuse`/`adjust`), and include data model validation results in `validation.json`.

## Required Changes

### 1. validation.schema.json

**Remove `best_match`** from both components and data_models. Instead, `matches[]` is sorted by `match_confidence` descending (high → medium → low). Consumers read `matches[0]` for the best match.

**Add `data_models` array** to the output schema:

```json
"data_models": {
  "type": "array",
  "items": {
    "type": "object",
    "required": ["name", "status", "matches"],
    "properties": {
      "name": { "type": "string" },
      "status": {
        "type": "string",
        "enum": ["create", "reuse", "adjust"]
      },
      "matches": {
        "type": "array",
        "description": "Sorted by match_confidence descending. Empty for 'create' status.",
        "items": {
          "type": "object",
          "required": ["file", "type_name", "existing_fields", "match_confidence", "field_delta", "notes"],
          "properties": {
            "file": { "type": "string" },
            "type_name": { "type": "string" },
            "existing_fields": {
              "type": "array",
              "items": { "type": "string" }
            },
            "match_confidence": {
              "type": "string",
              "enum": ["high", "medium", "low"]
            },
            "field_delta": {
              "type": "object",
              "required": ["missing", "extra", "type_mismatch"],
              "properties": {
                "missing": { "type": "array", "items": { "type": "string" } },
                "extra": { "type": "array", "items": { "type": "string" } },
                "type_mismatch": { "type": "array", "items": { "type": "string" } }
              }
            },
            "notes": { "type": "string" }
          }
        }
      }
    }
  }
}
```

No `conflict` status for data models — they're simple structs. Either they match, need field additions, or need creation.

**Update component schema**: Remove `best_match` from component items. Add `"description": "Sorted by match_confidence descending"` to component `matches[]`.

### 2. SKILL.md Changes

- **Phase 0**: Include data model names in synonym generation (they're simpler — just the type name and field names as keywords).
- **Phase 3**: When analyzing matched files, also check if any match a data model (struct with matching fields).
- **Phase 4**: Classify data models:
  - `reuse` — same name, all required fields present with compatible types
  - `adjust` — same name, missing fields or type mismatches (include `field_delta`). Optionality differences count as type_mismatch (e.g., `String` vs `String?`).
  - `create` — no match found
- **Phase 6**: Include `data_models[]` in output. `matches[]` sorted by `match_confidence` descending. Update validation check: every data model from `arch.json` has an entry.

### 3. Summary Update

Use nested structure for both components and data_models:
```json
"summary": {
  "components": {
    "create": 2,
    "reuse": 1,
    "adjust": 0,
    "conflict": 0
  },
  "data_models": {
    "create": 1,
    "reuse": 0,
    "adjust": 1
  }
}
```

### 4. Edge Cases

- **EC-DM-1**: Matched type is an `enum` or `class`, not a `struct` — classify as `adjust` with a note explaining the type kind mismatch.
- **EC-DM-2**: Multiple existing types match the same data model — list all in `matches[]`, sorted by confidence. Consumer reads `matches[0]`.
- **EC-DM-3**: Data model with zero fields (marker type) — classify as `create` since there's nothing to match on.
- **EC-DM-4**: Field type differences due to optionality (`String` vs `String?`) — report as `type_mismatch` in `field_delta`, classify as `adjust`.

### 5. Consumer Updates

**SPEC-004 (synthesize-implementation)**:
- REQ-1.5: Replace `best_match` index dereferencing with `matches[0]` (first element = best match since array is sorted by confidence).

## Definition of Done

- [ ] `validation.schema.json` includes `data_models[]` array
- [ ] `validation.schema.json` removes `best_match` from components (sorted `matches[]` replaces it)
- [ ] `validation.schema.json` uses nested `summary` structure
- [ ] `field_delta` properties (`missing`, `extra`, `type_mismatch`) are all required
- [ ] validate-plan searches codebase for data model types
- [ ] Each `arch.json` data model gets a `create`/`reuse`/`adjust` classification
- [ ] `adjust` includes `field_delta` (missing/extra/type_mismatch fields)
- [ ] `matches[]` sorted by `match_confidence` descending (both components and data_models)
- [ ] Summary counts use nested structure for components and data_models
- [ ] SKILL.md updated with data model phases and edge cases
- [ ] Module spec (`skills/validate-plan/.claude/CLAUDE.md`) updated
- [ ] SPEC-004 REQ-1.5 updated to use `matches[0]` instead of `best_match`
