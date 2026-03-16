---
number: SPEC-003
feature: validate-plan
status: done
blocked-by: [SPEC-002]
blocking: [SPEC-001, SPEC-004]
---

# /validate-plan — Codebase Validation

## Purpose

Takes an architect's decomposition (`arch.json` from `/plan`) and validates it against the existing codebase. Finds reusable types, identifies conflicts, and annotates each component with its reuse status. Does NOT redesign the architecture.

## Inputs / Outputs

- **Input**: `arch.json` path, `--output` path (no spec needed — `arch.json` contains `spec_summary`)
- **Output**: `validation.json` — each component annotated with `create|reuse|adjust|conflict` status, matched files, confidence scores, and concrete adjustment actions

## Pipeline

1. **Phase 0 (LLM)**: Read `arch.json` (uses `spec_summary` for context), generate synonym keywords from component responsibilities/categories
2. **Phase 1+2 (Script)**: `search-codebase.py` greps files for `solid-category`/`solid-description` frontmatter, matches against synonyms
3. **Phase 3 (LLM)**: Read matched files, analyze responsibility fit and interface compatibility, score confidence
4. **Phase 4 (LLM)**: Classify each component as `create`, `reuse`, `adjust`, or `conflict`
5. **Phase 5 (LLM)**: Detail adjustments (concrete actions, breaking change checks) and conflicts (incompatibility reasons, alternatives)
6. **Phase 6 (LLM)**: Assemble and write `validation.json`

## Connections

- **Consumes**: `arch.json` from `/plan` (SPEC-002)
- **Produces**: `validation.json` consumed by `/synthesize-implementation` (SPEC-004)
- **Agent**: `validate-plan-agent` (model: sonnet)

## Script: `search-codebase.py`

- **Location**: `skills/validate-plan/scripts/search-codebase.py`
- **Input**: `--sources <dir>` (default `.`), `--synonyms <json-array-string>` (required)
- **Output**: JSON with `matches[]` ({path, matched_terms[]}) and `summary` ({total_files_scanned, files_with_frontmatter, files_matched})
- **Behavior**: Scans entire file for `solid-category`/`solid-description` in comment-prefixed lines. Supports multiple frontmatter blocks per file (e.g., one per type). Matches description words and category against synonyms with OR logic. Component-agnostic — returns flat file list.

## Design Decisions

- **Script is component-agnostic**: Returns all files matching any synonym. The LLM maps files to components in Phase 3. This keeps the script simple and reusable.
- **Synonym generation is LLM-driven**: The LLM generates domain-aware synonyms (3 per keyword) rather than using a static thesaurus. Passed as JSON string directly — no temp file.
- **matched_terms[] per file**: Helps the LLM understand why a file was returned, informing confidence scoring.
- **No spec input needed**: `arch.json` already contains `spec_summary` — a separate spec file is redundant.
- **No Sources/ glob**: The script handles empty/missing directories by returning zero matches. Just pass `.` as sources.

## Gotchas

- Requires `solid-category` and `solid-description` frontmatter in codebase files — files without these are invisible to the search.
- `best_match` is `null` when status is `create`, otherwise an index into `matches[]`.
- The validator is read-only — it never modifies codebase files.