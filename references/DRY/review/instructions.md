---
name: dry-review
type: review
rules: PRINCIPLE_FOLDER_ABSOLUTE_PATH/rule.md
output_schema: output.schema.json
---

### Phase 0: Load Examples for context.
- [ ] **0.1 Read all examples** — Glob `PRINCIPLE_FOLDER_ABSOLUTE_PATH/Examples/*` and read every file found

#### Phase 1: Detection (DRY-1, DRY-2, and DRY-3 run independently and in parallel if possible)

- [ ] **1.1 DRY-1: Detect Reuse Misses**
    - [ ] 1.1.1 Inventory all new or modified code units at every granularity — types, functions (any access level), views, view builders, computed properties, extensions, inline expressions. For each, identify its responsibility — what does it do?

      | Code Unit | Kind | Responsibility |
      |-----------|------|---------------|
      |           |      |               |

    - [ ] 1.1.2 Generate synonym keywords for each code unit's responsibility (3 synonyms per keyword, domain-aware)

      | Code Unit | Keywords | Synonyms |
      |-----------|----------|----------|
      |           |          |          |

    - [ ] 1.1.3 **Frontmatter search (script)** — run the search script to find files with `solid-` frontmatter matching the synonyms:
        ```
        python3 ${CLAUDE_PLUGIN_ROOT}/skills/validate-plan/scripts/search-codebase.py \
          --sources <sources-dir> \
          --synonyms '<json-array-string>'
        ```
        Parse the JSON output — collect `matches[]` with `matched_terms[]` per file.

    - [ ] 1.1.4 **Name-based search (LLM fallback)** — always runs regardless of 1.1.3 results. Catches code without frontmatter:
        - For each code unit, collect search terms: name, camelCase-split keywords, synonyms from 1.1.2
        - Search for extensions on types being used (`extension <TypeName>`) — convenience wrappers are commonly missed
        - Search shared/common directories and design system modules for equivalent components, views, or layouts
        - Use Grep to search file contents and Glob to search filenames across the codebase
        - Merge new hits into matches (skip files already found in 1.1.3)

    - [ ] 1.1.5 **Analyze matches** — for each matched file:
        - Read the file's source code
        - Extract: type name, protocols, method signatures, properties, static members, extensions, view body structure
        - Compare against the code unit's responsibility and interfaces:
            - Responsibility fit: does the existing code serve the same purpose?
            - Interface coverage: does it expose what the new code needs?
            - Can it be used directly, configured, or extended to fit?
        - Score match confidence:
            - high — same responsibility + compatible interface
            - medium — similar responsibility, needs extension or configuration
            - low — overlapping keywords but different purpose

      | New Code Unit | Existing Code | Confidence | Responsibility Fit | Interface Differences | Classification |
      |---------------|--------------|------------|-------------------|----------------------|---------------|
      |               |              |            |                   |                      |               |

    - [ ] 1.1.6 Count EXACT (high confidence, no interface differences) and EXTENSIBLE (high/medium confidence, interface differences resolvable via extension) matches that were not reused
      Reuse misses: ___

- [ ] **1.2 DRY-2: Detect Inlined Duplication**
    - [ ] 1.2.1 For each function or method in the unit, identify its logical sequence

      | Method | Logical Sequence |
      |--------|-----------------|
      |        |                 |

    - [ ] 1.2.2 Search other units in the same module/target for methods with the same logical sequence
    - [ ] 1.2.3 Classify each match:

      | Method A | Location A | Method B | Location B | Classification | Reasoning |
      |----------|-----------|----------|-----------|---------------|-----------|
      |          |           |          |           |               |           |

    - [ ] 1.2.4 Count IDENTICAL and STRUCTURAL matches
      Inlined duplications: ___

- [ ] **1.3 DRY-3: Detect Missing Abstractions**
    - [ ] 1.3.1 Identify the domain of each type under review

      | Type | Domain |
      |------|--------|
      |      |        |

    - [ ] 1.3.2 For each type, identify generic behavioral patterns that are not domain-specific

      | Type | Pattern | Domain-Specific? | Reuse Potential |
      |------|---------|-----------------|-----------------|
      |      |         |                 |                 |

    - [ ] 1.3.3 Count patterns with reuse potential that are not extracted
      Missing abstractions: ___

#### Phase 2: Filter Out Exceptions

- [ ] **2.1 Cross-check exceptions** — mark exceptions

  | Type/Method | Exception Reason |
  |-------------|-----------------|
  |             |                 |

- [ ] **2.2 Exclude exceptions** — exclude exceptions from analysis

#### Phase 3: Scoring

- [ ] **3.1 Determine severity**
    - [ ] 3.1.1 Reuse misses: ___, severity: ___
    - [ ] 3.1.2 Inlined duplications: ___, severity: ___
    - [ ] 3.1.3 Missing abstractions: ___, severity: ___
    - [ ] 3.1.4 Adjust severity considering exceptions.
    - [ ] 3.1.5 Final severity: ___

#### Phase 4: Output

- [ ] **4.1 Report Violations**
    - [ ] 4.1.1 Show reuse miss table with existing types that should have been used
    - [ ] 4.1.2 Show inlined duplication table with matched methods and locations
    - [ ] 4.1.3 Show missing abstractions table with identified patterns
    - [ ] 4.1.4 Show cross-reference table with found exceptions
