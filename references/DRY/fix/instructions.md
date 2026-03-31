---
name: dry-fix
type: fix
input_schema: PRINCIPLE_FOLDER_ABSOLUTE_PATH/review/output.schema.json
output_schema: output.schema.json
---

### Phase 0: Load Context

- [ ] **0.1 Read the review findings JSON** (provided as structured input_schema)
- [ ] **0.2 Read the source file** (provided as input)

#### Phase 1: Determine Fix Strategy

- [ ] **1.1 Read `scoring.final_severity` from findings**
    - SEVERE → full refactoring based on which metrics triggered

- [ ] **1.2 Identify which metrics triggered the severity**
    - DRY-1 (reuse miss) → Use Existing Type pattern
    - DRY-2 (inlined duplication) → Extract Shared Abstraction pattern
    - DRY-3 (missing abstraction) → Extract Reusable Abstraction pattern
    - Multiple → combine patterns as needed

#### Phase 2: Identify Suggestions

- [ ] **2.1 Analyze findings** — read metrics (reuse miss table with confidence/interface differences, duplication table, missing abstractions table)
- [ ] **2.2 Propose suggestion** — which types to reuse, which logic to extract, which patterns to separate
- [ ] **2.3 Create todo items** — concrete actionable steps to implement the fix:
    - [ ] For DRY-1: use the review's match analysis (existing type, confidence, interface differences) to determine the fix approach:
        - EXACT match (high confidence, no interface differences) → replace the new type with direct usage of the existing type, remove the redundant type
        - EXTENSIBLE match (high/medium confidence, resolvable differences) → read the existing type, determine what extension is needed:
            - Missing protocol conformance → add extension conformance on the existing type
            - Missing method → add method via extension or protocol default implementation
            - Signature mismatch → add adapter or overload
        - Update all call sites to use the existing type instead of the new one
        - Remove the redundant new type
    - [ ] For DRY-2: identify the shared logical sequence across locations, extract into a shared function or type, choose the appropriate abstraction level:
        - Same types → shared function or method
        - Different types, same algorithm → generic function or protocol with default implementation
        - Different types, same structure → protocol with associated types or generics
        - Replace all duplication sites with calls to the shared abstraction
    - [ ] For DRY-3: identify the generic pattern within the domain type (behavioral, creational, UI composition, or data flow), extract into a standalone reusable type or component, update the domain type to delegate to the extracted abstraction
    - Each todo item should be a single, implementable action

#### Phase 3: Write suggested_fix

- [ ] **3.1 Write full code snippets** showing:
    - For DRY-1: how to use the existing type (direct usage, extension, or configuration)
    - For DRY-2: the extracted shared abstraction (function, type, or protocol) and the modified call sites
    - For DRY-3: the extracted reusable abstraction and the modified domain type delegating to it
    - Before/after of the affected code
- [ ] **3.2 Predict post-fix metrics** (reuse misses, duplications, missing abstractions per type)

#### Phase 4: Generate Output

- [ ] **4.1 Produce JSON matching output schema**
    - [ ] 4.1.1 Fill `suggested_fix` with the full text + code snippets from Phase 3
    - [ ] 4.1.2 Fill `todo_items` with the actionable steps from Phase 2.3
    - [ ] 4.1.3 Fill `verification` with predicted metrics from Phase 3.2
    - [ ] 4.1.4 Fill `addresses` with finding IDs this suggestion resolves

#### Constraints
- Include full code snippets in suggested_fix (shared abstractions, modified types, before/after)
- Todo items must be concrete and implementable (not vague)
- Preserve existing public API — external callers should see the same interface
- All violations are SEVERE — apply full refactoring patterns
- When extracting shared abstractions, prefer the narrowest abstraction that covers all use sites
- Do not over-generalize — the shared abstraction should serve the known use cases, not hypothetical ones
