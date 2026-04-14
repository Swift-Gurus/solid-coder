---
name: dry-code
type: code
---

# DRY Coding Instructions

Every new type, function, view, computed property, or inline expression is a potential duplication. Before writing and after writing it (always do two one before and one after), validate against the DRY metrics.

---

## Before Creating Any New Code

```
You are about to write a new code unit (type, function, view, helper, extension, computed property).
         │
         ▼
What responsibility does it serve? (what does it do, what problem does it solve?)
         │
         ▼
DRY-1: Does something in the codebase already do this?
    Run the search procedure (below) BEFORE writing.
         │
    EXACT or EXTENSIBLE match found → Do not create new code. Use fix approach below.
    No match found → Continue ▼
         │
         ▼
DRY-2: Are you about to write logic that exists elsewhere in a different form?
    Check: does another method in this module follow the same logical sequence?
    (same operations, same order, same branching — even with different variable names or types)
         │
    IDENTICAL or STRUCTURAL match exists → Do not duplicate. Use fix approach below.
    No duplication → Continue ▼
         │
         ▼
DRY-3: Is the pattern you're writing domain-specific or generic?
    Generic patterns: retry, queue, cache, observe, poll, builder logic,
    recurring view structures, transform pipelines, validation chains.
         │
    Generic + could be needed elsewhere → Extract as standalone abstraction. Use fix approach below.
    Domain-specific → Continue ▼
         │
         ▼
Does it fall into an exception? (see rule.md Exceptions)
    YES → Note it. Not a violation.
    NO  → Continue ▼
         │
         ▼
Validate reuse misses + duplications + missing abstractions against severity bands in rule.md:
    COMPLIANT → Proceed.
    SEVERE    → Do not write it this way. Use fix approach below.
```

## Search Procedure (DRY-1)

Before creating any new code unit, run both search phases:

### Phase A: Frontmatter search (script)

1. **Generate search terms** — take the name and responsibility of what you're about to create, split into keywords, generate 3 synonyms per keyword (domain-aware). Collect into a JSON array.
2. **Run search script:**
   ```
   python3 ${CLAUDE_PLUGIN_ROOT}/skills/validate-plan/scripts/search-codebase.py \
     --sources <sources-dir> \
     --synonyms '<json-array-string>'
   ```
3. Parse JSON output — collect `matches[]` with `matched_terms[]` per file.

### Phase B: Name-based search (Grep/Glob fallback)

Always runs regardless of Phase A results. Catches code without `solid-` frontmatter:

1. Collect search terms: the name, camelCase-split keywords, synonyms from Phase A
2. Search for extensions on types you're using (`extension <TypeName>`) — convenience wrappers are commonly missed
3. Search shared/common directories and design system modules for equivalent components
4. Use Grep to search file contents and Glob to search filenames across the codebase
5. Merge new hits with Phase A results (skip duplicates)

### Classify matches

For each matched file — read it, compare responsibility and interfaces:

- **EXACT** — same responsibility, compatible interface
- **EXTENSIBLE** — similar responsibility, needs extension or configuration
- **PARTIAL** — overlapping keywords but genuinely different purpose (not a reuse miss)

## When SEVERE — Resolve

Use the loaded fix instructions to resolve the duplication.

## Exceptions — Not Violations

These are defined in rule.md. Do not expand this list.
