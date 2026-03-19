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

- [ ] 0.1 Read `arch.json` from ARCH_JSON_PATH. Use `spec_summary` for context. Note `acceptance_criteria[]` and `design_decisions[]` for use in Phase 3.
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
- [ ] 1.2 Parse the JSON output.

## Phase 1.5: Name-Based Search (LLM)

A language-agnostic fallback that catches legacy code without solid-frontmatter. Always runs regardless of Phase 1 results.

- [ ] 1.5.1 For each component in `arch.json`, collect search terms:
  - The component `name` (e.g., `ProductRepository`)
  - Key words from the component `name` split on camelCase/PascalCase boundaries (e.g., `Product`, `Repository`)
  - The synonym keywords from Phase 0
- [ ] 1.5.2 For each search term, use Grep to search filenames and file contents across the codebase. Use Glob to find files whose names contain the term.
- [ ] 1.5.3 Collect any files found that are NOT already in `matches[]` from Phase 1.
- [ ] 1.5.4 Merge new hits into `matches[]` with `matched_terms` set to the terms that matched. These go through the same Phase 3 analysis as frontmatter matches — no separate treatment.

## Phase 3: Match Analysis (LLM)

If `matches[]` is empty after both Phase 1 and Phase 1.5, skip to Phase 4 and classify everything as `create`.

Iterate over each matched file from the combined results. For each file, analyze it against all architect components.

**FOR** each file in `matches[]` from script output **DO**:

- [ ] 3.1 Read the file's source code.
- [ ] 3.2 Extract from the source code:
  - `type_name` (class/struct/enum/protocol declaration)
  - `existing_interfaces` — protocols the type conforms to
  - `existing_fields` — field declarations (for structs/classes with `solid-category: model`)
- [ ] 3.3 For each architect component that could relate to this file:
  - Compare the file's responsibility, interfaces, fields against the component's `responsibility`, `interfaces`, `dependencies`, `fields`.
  - Check `acceptance_criteria[]` from `arch.json` — for criteria related to this component, note which ones the existing code already satisfies and which it does not. Record in `satisfied_criteria[]` and `unsatisfied_criteria[]`.
  - Record specific `differences` — concrete mismatches the synthesizer needs to make decisions:
    - Field differences: `"field name: String? vs expected name: String"`, `"missing field email: String"`
    - Interface differences: `"missing protocol conformance to ProductReading"`, `"has extra conformance to Cacheable"`
    - Signature differences: `"method fetchAll() returns [Product] vs expected async throws -> [Product]"`, `"missing method fetchByCategory(_: String)"`
    - Responsibility differences: `"responsibility is caching, arch expects fetching"`
- [ ] 3.5 Score `match_confidence`:
  - `high` — same responsibility + compatible interface
  - `medium` — similar responsibility, interface needs work
  - `low` — overlapping keywords but different purpose
- [ ] 3.6 Record the match against the relevant component(s).

**END**

## Phase 4: Classification (LLM)

For each component, assign a status:

- [ ] 4.1 `create` — zero matches from Phase 3. No existing type relates to this component. Must be built from scratch.
- [ ] 4.2 `reuse` — match fulfills responsibility AND interface. No changes needed.
- [ ] 4.3 `adjust` — match can serve the component's purpose with modifications. This includes:
  - Interface changes (new method, extended protocol, additional conformance, generic parameter)
  - Adding a protocol conformance to an existing concrete type (e.g., arch wants an abstraction, existing type has the right data/behavior but no protocol)
  - Extending an existing type with new capabilities (e.g., adding a case to an enum, adding fields to a model)
  - The key test: the existing type's responsibility **overlaps** with the component's, and it's cheaper to adjust than to create new
- [ ] 4.4 `conflict` — match has same name or overlapping responsibility but incompatible design. Cannot reuse without major rework.

## Phase 5: Output

- [ ] 5.1 Create structured output `validation.json` that corresponds to `${SKILL_DIR}/validation.schema.json`
- [ ] 5.2 Sort `matches[]` by `match_confidence` descending (high → medium → low). Consumers read `matches[0]` for the best match.
- [ ] 5.3 Validate:
  - Every component from `arch.json` has an entry
  - `matches[]` is empty array for `create` status (4.1 guarantees no matches exist)
  - Summary counts match actual statuses
- [ ] 5.4 Write `validation.json` to OUTPUT_PATH.

## Edge Cases

- **EC-1**: Multiple types match a single component — list all in `matches[]`, sorted by `match_confidence` descending. Consumer reads `matches[0]`.
- **EC-2**: Architect proposes splitting a monolithic type — classify as `adjust` with note about extraction needed.

## Constraints

- Do NOT redesign the architecture — only report what exists and how it fits.
- Do NOT modify any codebase files — this is read-only analysis.
- Do NOT read file contents beyond frontmatter in the script — the LLM reads full files in Phase 3.
- Do NOT decide what actions to take — report what exists. The synthesizer decides actions.