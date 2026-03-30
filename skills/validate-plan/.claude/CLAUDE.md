---
number: SPEC-003
feature: validate-plan
status: done
blocked-by: [SPEC-002]
blocking: [SPEC-001, SPEC-004]
---

# /validate-plan — Codebase Validation

## Purpose

Takes an architect's decomposition (`arch.json` from `/plan`) and validates it against the existing codebase. Finds reusable types, identifies conflicts, and annotates each component with its reuse status. Does NOT redesign the architecture — does NOT decide what actions to take.

## Inputs / Outputs

- **Input**: `arch.json` path, `--output` path (no spec needed — `arch.json` contains `spec_summary`)
- **Output**: `validation.json` — each component annotated with `create|reuse|adjust|conflict` status, matched files, and confidence scores. Schema: `skills/validate-plan/validation.schema.json`

## Pipeline

1. **Phase 0 (LLM)**: Read `arch.json` (uses `spec_summary` for context), generate synonym keywords from component responsibilities/categories
2. **Phase 1+2 (Script)**: `search-codebase.py` greps files for `solid-category`/`solid-description` frontmatter, matches against synonyms
3. **Phase 1.5 (LLM)**: Name-based fallback — greps filenames and file contents for component names and synonyms (language-agnostic). Catches legacy code without frontmatter. Always runs; merges new hits into `matches[]`.
4. **Phase 3 (LLM)**: Read matched files from both passes, extract existing interfaces and fields, analyze responsibility fit, score confidence
5. **Phase 4 (LLM)**: Classify each component as `create`, `reuse`, `adjust`, or `conflict`
6. **Phase 5 (LLM)**: Assemble and write `validation.json`

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

- **Rewrite mode bypass**: When `arch.json` has `mode: "rewrite"`, all search and analysis phases are skipped. Every component is classified as `create` with empty `matches[]`. This supports greenfield rebuilds where existing code is intentionally being replaced, not reused. The orchestrator doesn't need to know about rewrite mode — validate-plan handles it internally.
- **Script is component-agnostic**: Returns all files matching any synonym. The LLM maps files to components in Phase 3. This keeps the script simple and reusable.
- **Synonym generation is LLM-driven**: The LLM generates domain-aware synonyms (3 per keyword) rather than using a static thesaurus. Passed as JSON string directly — no temp file.
- **matched_terms[] per file**: Helps the LLM understand why a file was returned, informing confidence scoring.
- **No spec input needed**: `arch.json` already contains `spec_summary`, `acceptance_criteria[]`, and `design_references[]` — a separate spec file is redundant.
- **Acceptance criteria checking**: During Phase 3 match analysis, the validator checks which acceptance criteria the existing code already satisfies and which it doesn't. This is recorded per match as `satisfied_criteria[]` and `unsatisfied_criteria[]`, so the synthesizer knows what gaps remain.
- **No Sources/ glob**: The script handles empty/missing directories by returning zero matches. Just pass `.` as sources.
- **Report, don't decide**: The validator reports what exists (interfaces, fields, confidence). The synthesizer decides what actions to take (add method, change type, etc.).
- **`create` means truly nothing found**: `create` status is only assigned when zero matches exist from Phase 3. If any match exists (even low confidence), it should be classified as `adjust` or `conflict` — never `create`. This ensures `matches[]` is always empty for `create` and the synthesizer gets the full picture for other statuses.
- **`adjust` is broad**: Covers interface changes, protocol conformance additions, enum case extensions, field additions — any case where the existing type's responsibility overlaps and it's cheaper to modify than create new.
- **Data models are components**: Components with `category: "model"` have `existing_fields` populated in matches. The `solid-category: model` frontmatter is the differentiation signal.
- **Name-based fallback is language-agnostic**: Phase 1.5 uses Grep/Glob on component names and synonyms — no hardcoded language patterns (`class`, `struct`, etc.). This works for any language in the codebase. Always runs alongside the frontmatter search; results merge into the same `matches[]`.

## Gotchas

- The script (Phase 1) only finds files with `solid-category`/`solid-description` frontmatter. Phase 1.5 compensates by searching filenames and contents for component names — catching legacy code without frontmatter.
- `matches[]` is sorted by `match_confidence` descending — consumers take `matches[0]` for the best match.
- The validator is read-only — it never modifies codebase files.
- The validator does not prescribe actions — it reports what exists and classifies fit. The synthesizer decides remediation.