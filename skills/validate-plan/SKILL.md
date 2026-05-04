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

## Phase -1: Check Mode

- [ ] -1.1 Read `arch.json` from ARCH_JSON_PATH. Check `mode` field. If missing, treat as `"default"`.
- [ ] -1.2 If `mode == "rewrite"`: skip Phases 0–4. Write `validation.json` to OUTPUT_PATH with every component from `arch.json` set to `status: "create"` and `matches: []`. Include `summary` with `create` = total component count, all others = 0. Jump to Phase 5 (Output) step 5.4 to write the file. Done.

## Phase 0: Prep — Generate Synonyms

- [ ] 0.1 Read `arch.json` from ARCH_JSON_PATH. Note `spec_summary` for context and `acceptance_criteria[]` for use in Phase 3.
- [ ] 0.2 For each component, extract keywords from `responsibility` (remove stop words: the, a, an, is, are, with, from, for, to, of, and, or, in, on, by, that, this, it). Generate 2–3 semantic synonyms per keyword (e.g. "fetch" → retrieve, load, pull; "store" → persist, save, cache).
- [ ] 0.3 Merge all keywords and synonyms into a single deduplicated lowercase list → TAGS.

## Phase 1: Codebase Search

- [ ] 1.1 Call `mcp__plugin_solid-coder_pipeline__search_codebase` with:
  - `sources_dir`: project sources directory
  - `plan_path`: ARCH_JSON_PATH — auto-extracts component names, interfaces, categories, and spec numbers
  - `tags`: TAGS from Phase 0 — semantic synonyms not captured by structural extraction
- [ ] 1.2 The result is a list of matching files with descriptions. If the output is large it is saved to a file — use the Read tool to load it.

## Phase 3: Match Analysis (LLM)

If the search returned no matches, skip to Phase 4 and classify everything as `create`.

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
  - Record each gap as a `differences[]` entry, an object `{category, text}`. `text` is concrete prose describing the specific gap. `category` is one of:

    | Category | Use when… |
    |---|---|
    | `scope-mismatch` | The existing code's module/visibility boundary makes it unreachable from the architect's component — the new component's location cannot import or call it without violating the dependency direction or visibility rules of the project. |
    | `coverage-gap` | Existing logic addresses the same behavior but is functionally narrower than the architect requires — missing cases, conditions, inputs, or branches, but the foundation is correct. |
    | `shape-mismatch` | Existing type's surface differs from the architect's expectation — declaration kind, supertype/conformance, signatures, return types, parameters, or member visibility. |
    | `responsibility-mismatch` | Existing type addresses a different behavioral problem, even if name or surface overlaps. |
    | `missing-entry` | Existing non-code artifact (manifest, config, doc index) is present but lacks specific rows/sections that need appending. |
    | `other` | Doesn't fit cleanly above. Synthesizer treats as `shape-mismatch`. Use sparingly — frequent `other` means the rubric needs new categories. |

  - Pick exactly one category per entry. If a single fact is genuinely both scope and coverage, split it into two entries.
  - **Disambiguation rules** for the most-confused pairs:
    - **scope-mismatch vs shape-mismatch.** Mental test: *"If I delete the new component and just try to reference the existing type from where the new component lives, can I?"* If NO → `scope-mismatch` (the type isn't reachable at all). If YES but the declaration's form needs to change (member visibility, signature, conformance, declaration kind) → `shape-mismatch`.
    - **shape-mismatch vs coverage-gap.** If the architect requires a declared element that doesn't exist on the existing API surface (missing method, missing protocol member, missing enum case used as a parameter) → `shape-mismatch`. If the existing element exists but handles a narrower set of inputs/conditions than required → `coverage-gap`.
    - **coverage-gap vs responsibility-mismatch.** Use Q3 (`gap_is_additive`) as the discriminator: additive gap (extending existing logic) → `coverage-gap`; corrective gap (requires rewriting existing logic) → `responsibility-mismatch`.
  - **`differences[]` is for gaps requiring action.** Observations about reusable patterns or context worth carrying forward go in this match's `notes`, NOT in `differences[]`.

- [ ] 3.5 Score the match by answering three questions, then deriving `match_confidence` mechanically. **Confidence is decoupled from reachability and shape — those facts go in `differences[].category` and drive routing, not scoring.**

  - [ ] 3.5.1 **Q1 — `responsibility_aligned`**: Does the existing type's purpose and the architect's component `responsibility` address the **same behavioral problem**?
    - Write each in one sentence (verb + object — what it does, not how) and compare.
    - Different scope, different surface, different visibility, different module — none of these make this false. Only a different *kind of work* does.
    - If hesitating, write both sentences in `notes` and pick the answer that matches.

  - [ ] 3.5.2 **Q2 — `implements_any_required_behavior`**: Does the existing code already implement at least one of the architect's required behaviors for this component?
    - Default check: TRUE iff `satisfied_criteria` is non-empty.
    - Override TRUE when the existing logic demonstrably covers part of the architect's responsibility but the criteria are spelled at a level the existing surface doesn't directly express (note this in `notes`).

  - [ ] 3.5.3 **Q3 — `gap_is_additive`**: Can the unsatisfied behaviors be reached by ADDING code on top of the existing implementation (new methods, new cases, new branches) without rewriting existing logic?
    - TRUE — the existing code is a foundation; the gap is extension.
    - FALSE — closing the gap requires rewriting the existing approach; the existing code is competing rather than foundational.
    - When `unsatisfied_criteria` is empty, set TRUE (no gap).
    - **Cross-check with categories**: Q3 must agree with the `differences[]` categories on this match. If any difference is `responsibility-mismatch`, Q3 must be FALSE. If every difference is `scope-mismatch`, `coverage-gap`, `shape-mismatch`, or `missing-entry`, Q3 must be TRUE. If they disagree, one of them is wrong — re-examine before scoring.

  - [ ] 3.5.4 Derive `match_confidence` by counting TRUE answers — do NOT vibe-check this:
    - **3 TRUE** → `high`
    - **2 TRUE** → `medium`
    - **0 or 1 TRUE** → `low`

  - [ ] 3.5.5 **Do NOT degrade confidence based on**:
    - **Reachability** — lives in `differences[].category=scope-mismatch`.
    - **Shape** — lives in `differences[].category=shape-mismatch`.
    - **Coverage gaps** — lives in `differences[].category=coverage-gap` and is already factored in via Q3 (additive vs corrective).
    - These facts go in `differences[]` where they are loud, structured, and routable. They must NOT silently lower confidence, or the synthesizer loses the "relevant logic, awkwardly placed" case that extraction is designed to handle.

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

- [ ] 5.1 Create structured output `validation.json` that corresponds to `${SKILL_DIR}/validation.schema.json`. Include `spec_number` from `arch.json` unchanged.
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
