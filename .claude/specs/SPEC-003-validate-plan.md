---
number: SPEC-003
feature: validate-plan
status: draft
blocked-by: [SPEC-002]
blocking: [SPEC-001, SPEC-004]
---

# /validate-plan — Codebase Validation

## Description

As the `/implement` orchestrator, I need a sub-skill that takes the architect's decomposition and validates it against the existing codebase — finding reusable types, identifying conflicts, and annotating each component with its reuse status.

The validator does NOT redesign the architecture. It reports what exists, what fits, and what needs adjustment.

## Skill & Agent

- `user-invocable: true` (temporary — for standalone testing)
- `argument-hint: <spec-path> <arch-json-path> --output <validation-json-path>`
- `allowed-tools: Read, Grep, Glob, Bash, Write`
- Agent wrapper required — model: **sonnet**, wraps skill `validate-plan`
  - Agent `allowed-tools`: `Read, Grep, Glob, Bash, Write, Skill`

## Input: `arch.json` Schema Reference

The validator reads `arch.json` produced by `/plan` (SPEC-002). Each component has:

```json
{
  "components": [
    {
      "name": "ProductFetchService",
      "category": "network",
      "responsibility": "Fetches product data from REST API with pagination",
      "interfaces": ["ProductReading"],
      "dependencies": ["ProductReading", "CacheWriting"],
      "produces": ["Product", "[Product]"]
    }
  ],
  "wiring": [...],
  "composition_root": {...}
}
```

Fields used by the validator:
- `name` — type name search
- `category` — match against `solid-category`
- `responsibility` — semantic match against `solid-description`
- `interfaces` — protocol name search
- `dependencies` — check for existing protocol definitions

## Flow

```
Input: spec, arch.json, --output path
          │
          ▼
┌─────────────────────────────────────────┐
│ LLM: Phase 0 — Prep                    │
│   Read arch.json, for each component:  │
│   split responsibility → keywords,     │
│   add category, generate 3 synonyms    │
│   per keyword, merge + dedup →         │
│   write synonyms.json { synonyms: [] } │
└──────────┬──────────────────────────────┘
           │
           ▼
╔═════════════════════════════════════════╗
║ SCRIPT: search-codebase.py             ║
║ Phase 1+2: Search                      ║
║                                        ║
║ Input: --sources dir,                  ║
║        --synonyms <json-string>        ║
║                                        ║
║ Grep all files under --sources dir for ║
║ solid-category / solid-description.    ║
║ For each file with frontmatter:        ║
║   a. Split solid-description → words   ║
║   b. Check if any word OR              ║
║      solid-category matches synonyms   ║
║   c. If match → include file           ║
║                                        ║
║ Output: flat JSON list to stdout       ║
╚══════════╦══════════════════════════════╝
           │
           ▼
┌─────────────────────────────────────────┐
│ LLM: Phase 3 — Match Analysis          │
│ For each matched file from script:      │
│   a. Read the file                      │
│   b. Analyze: can this type fulfill     │
│      the architect's responsibility?    │
│   c. Check: does it need interface      │
│      adjustment? (generic interface,    │
│      new conformance, adapter, etc.)    │
│   d. Score match_confidence using       │
│      matched_terms[] from script        │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ LLM: Phase 4 — Classification          │
│   - create: zero matches or all low     │
│   - reuse: match fulfills responsibility│
│     AND interface — no changes needed   │
│   - adjust: match fulfills responsibility│
│     but needs interface changes         │
│   - conflict: overlapping responsibility│
│     but incompatible design             │
└──────────┬──────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│ LLM: Phase 5 — Detail                  │
│ For "adjust":                           │
│   - List concrete changes needed        │
│   - Grep call sites for breaking check  │
│ For "conflict":                         │
│   - Document why it conflicts           │
│   - Suggest alternatives                │
└──────────┬──────────────────────────────┘
           │
           ▼
Output: validation.json → written to --output path
```

## Requirements

### REQ-1: Codebase Search Script (Phase 1 + 2)

The LLM reads `arch.json`, splits each component's `responsibility` into keywords plus `category`, generates 3 synonyms per keyword, and merges everything into a flat deduplicated word list (Phase 0). This list is passed as a JSON string to the script. The script handles the grep (Phases 1+2). The LLM processes the script's results in Phases 3–5.

**Location:** `skills/validate-plan/scripts/search-codebase.py`

**Input:**
- `--sources <path>` — directory path to search root. Defaults to the project root directory (`.`). The script recursively greps all files under this directory.
- `--synonyms <json-string>` — **required**. A JSON string with a flat synonym word list generated by the LLM. Script fails (exit 1) if not provided.

**Synonyms format (JSON string):**
```json
["fetch", "load", "get", "retrieve", "product", "item", "goods", "network", "save", "persist", "store", "list", "collection", "display", "show", "present"]
```
The LLM generates this before calling the script. Algorithm: for each component in `arch.json`, split `responsibility` into keywords, add `category`, generate 3 synonyms per keyword, merge all into a single flat deduplicated list.

**What it does:**
1. `grep -r` all files under `--sources` for lines containing `solid-category:` or `solid-description:`
2. For each file with solid-frontmatter found:
   a. Extract the `solid-category` value
   b. Extract the `solid-description` value and split it into individual words
   c. Check if any extracted word (from description or category) appears in the synonyms list
   d. If at least one synonym matches → include the file
3. Collect matches as `{path, matched_terms[]}` — flat list, no component grouping. Type name extraction is done by the LLM in Phase 3.
4. Deduplicate by file path

**Output (stdout):** JSON object:
```json
{
  "matches": [
    {
      "path": "Sources/Network/ProductFetchService.swift",
      "matched_terms": ["fetch", "network"]
    },
    {
      "path": "Sources/Network/ItemLoader.swift",
      "matched_terms": ["load", "product"]
    }
  ],
  "summary": {
    "total_files_scanned": 42,
    "files_with_frontmatter": 30,
    "files_matched": 2
  }
}
```

**Exit codes:** `0` — success, `1` — error (synonyms not provided, sources path not found, invalid JSON)

**Design notes:**
- The script is component-agnostic — it returns all files whose frontmatter matches any synonym. The LLM maps files to architect components in Phase 3.
- The `matched_terms[]` per match helps the LLM understand *why* a file was returned, informing confidence scoring.
- The script does NOT read file contents beyond frontmatter lines. The LLM reads full files in Phase 3.

### REQ-2: Match Analysis (Phase 3) — LLM

The LLM receives a flat list of matched files from the script. For each architect component, the LLM identifies which matched files are relevant by comparing the file's content against the component's responsibility, interfaces, and dependencies.

For each component with relevant matches:

- REQ-2.1: Read each matched file's source code.
- REQ-2.2: Analyze whether the existing type can fulfill the architect's described responsibility — compare methods, properties, and protocols against what the component needs.
- REQ-2.3: Check interface compatibility:
  - Does the type already conform to the needed protocols?
  - Could it conform with minor additions (new method, generic parameter)?
  - Does it need an adapter or wrapper to fit?
  - Would it need a new protocol to abstract its capabilities?
- REQ-2.4: Score `match_confidence`: `high` (same responsibility + compatible interface), `medium` (similar responsibility, interface needs work), `low` (overlapping keywords but different purpose). Use `matched_terms[]` from the script output to inform confidence.

### REQ-3: Classification (Phase 4) — LLM

- REQ-3.1: `create` — zero matches from script, or all matches scored `low`. Component must be built from scratch.
- REQ-3.2: `reuse` — match fulfills responsibility AND interface. No changes needed.
- REQ-3.3: `adjust` — match fulfills responsibility but needs interface changes (new method, extended protocol, additional conformance, generic parameter).
- REQ-3.4: `conflict` — match has same name or overlapping responsibility but incompatible design. Cannot be reused without major rework.

### REQ-4: Adjustment & Conflict Detail (Phase 5) — LLM

- REQ-4.1: For `adjust` components, list each change as a concrete action: "add method `fetchByCategory(_:)` to protocol `ProductReading`".
- REQ-4.2: Check if the adjustment breaks existing consumers — grep for all call sites of the affected protocol/type.
- REQ-4.3: If adjustment breaks consumers, note `"breaking": true` with affected files listed.
- REQ-4.4: For `conflict` components, document: what exists, why it's incompatible, and suggest alternatives (rename, new type, adapter pattern).

### REQ-5: Output Schema

- REQ-5.1: `validation.json` structure — this is consumed by `/synthesize-implementation` (SPEC-004):

  ```json
  {
    "components": [
      {
        "name": "ProductFetchService",
        "status": "adjust",
        "matches": [
          {
            "file": "Sources/Network/ProductFetchService.swift",
            "type_name": "ProductFetchService",
            "existing_interfaces": ["ProductReading"],
            "match_confidence": "high",
            "adjustments": [
              {
                "action": "add_method",
                "target": "ProductReading",
                "detail": "add fetchByCategory(_: String) async throws -> [Product]",
                "breaking": false
              }
            ],
            "notes": "Existing service handles fetching but lacks category filtering"
          },
          {
            "file": "Sources/Network/ItemLoader.swift",
            "type_name": "ItemLoader",
            "existing_interfaces": [],
            "match_confidence": "medium",
            "adjustments": [],
            "notes": "Loads items but different domain — lower confidence"
          }
        ],
        "best_match": 0
      },
      {
        "name": "ProductListViewModel",
        "status": "create",
        "matches": [],
        "best_match": null
      }
    ],
    "summary": {
      "create": 3,
      "reuse": 1,
      "adjust": 2,
      "conflict": 0
    }
  }
  ```

  **Schema notes:**
  - `matches[]` — all codebase files that matched this component, ranked by confidence. Empty array for `create` status.
  - `best_match` — index into `matches[]` for the recommended match. `null` when `status` is `create`. The synthesizer (SPEC-004) may override this choice.
  - `type_name` — extracted by the LLM in Phase 3 (not by the script).

- REQ-5.2: SPEC-004 (synthesize-implementation) reads these fields:
  - `status` → determines action type (create/modify/skip)
  - `matches[best_match].file` → target file for modify actions
  - `matches[best_match].adjustments` → specific changes for modify directives
  - `matches[].match_confidence` → picking best match when multiple exist
  - `matches[best_match].notes` → included in plan item notes

### Edge Cases

- EC-1: Multiple existing types match a single architect component — list all matches, rank by `match_confidence`, let synthesizer decide.
- EC-2: Architect proposes splitting what is currently one monolithic type — classify as `adjust` with note about extraction.

## Definition of Done

- [ ] Skill exists at `skills/validate-plan/SKILL.md` with `user-invocable: true` (temporary)
- [ ] Module spec exists at `skills/validate-plan/.claude/CLAUDE.md`
- [ ] Agent wrapper exists at `agents/validate-plan-agent.md` (model: sonnet)
- [ ] Script exists at `skills/validate-plan/scripts/search-codebase.py`
- [ ] Script accepts `--sources <dir> --synonyms <json-string>`, outputs JSON to stdout
- [ ] Script output schema is defined (flat list of `{path, matched_terms[]}`)
- [ ] Script: greps all files under sources dir for solid-frontmatter, matches description words and category against synonyms with OR logic, returns flat file list
- [ ] LLM generates synonyms as JSON string passed directly to script (no temp file)
- [ ] Skill accepts `spec` + `arch.json` path + `--output` path as input
- [ ] Skill Phase 3 (LLM): reads matched files, analyzes responsibility fit and interface compatibility, scores match_confidence
- [ ] Skill Phase 4 (LLM): classifies each component as `create`, `reuse`, `adjust`, or `conflict`
- [ ] Skill Phase 5 (LLM): for `adjust` — lists concrete changes, greps call sites for breaking check. For `conflict` — documents incompatibility, suggests alternatives.
- [ ] Produces `validation.json` matching the output schema (REQ-5.1)
- [ ] Output consumable by SPEC-004 synthesizer (REQ-5.2 fields)
- [ ] Expects solid-frontmatter in codebase files (solid-category, solid-description)
- [ ] Registered in root `.claude/CLAUDE.md` internal skills table
- [ ] Testable standalone: `/validate-plan spec.md arch.json --output ./validation.json`
