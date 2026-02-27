---
name: lsp-fix
type: fix
rules: PRINCIPLE_FOLDER_ABSOLUTE_PATH/refactoring.md
input_schema: PRINCIPLE_FOLDER_ABSOLUTE_PATH/review/output.schema.json
output_schema: output.schema.json
---

### Phase 0: Load Context

- [ ] **0.1 Read the review findings JSON** (provided as structured input_schema)
- [ ] **0.2 Read the source file** (provided as input)

#### Phase 1: Determine Fix Strategy

- [ ] **1.1 Read `scoring.final_severity` from findings**
  - MINOR → no refactoring, watch item only
  - SEVERE → refactoring required (see refactoring.md)

#### Phase 2: Identify Suggestions

- [ ] **2.1 Analyze findings** — read metrics (type checks, contract violations, empty methods, fatal error methods)
- [ ] **2.2 Propose suggestion** — what pattern to apply based on violation type:
  - Type checking (LSP-1) → protocol extraction + generic constraints
  - Strengthened preconditions (LSP-2) → update base contract OR handle in subtype
  - Weakened postconditions (LSP-2) → honor base guarantees OR update base contract
  - Broken invariants (LSP-2) → route through validated setters
  - Empty methods (LSP-3) → interface redesign (split protocol so conformers only implement what they support)
  - Fatal error methods (LSP-3) → interface redesign (protocol composition)
  - Orphan exceptions → error hierarchy unification
- [ ] **2.3 Create todo items** — concrete actionable steps to implement the fix:
    - Create protocol (name + method signatures)
    - Add generic constraint replacing type check
    - Update base contract (if precondition needs to change)
    - Fix subtype to honor postconditions
    - Route state access through validated setters
    - Split interface into smaller protocols (for LSP-3)
    - Each todo item should be a single, implementable action

#### Phase 3: Write suggested_fix

- [ ] **3.1 Write full code snippets** showing:
    - Protocol definition (if extracting)
    - Generic constraint replacing type check
    - Modified base class (if updating contract)
    - Modified subtype honoring contracts
    - Split protocols (if fixing empty methods / refused bequest)
    - Before/after of key methods
- [ ] **3.2 Predict post-fix metrics** (type checks, contract violations, empty methods percentage per type)

#### Phase 4: Generate Output

- [ ] **4.1 Produce JSON matching output schema**
    - [ ] 4.1.1 Fill `suggested_fix` with full text + code snippets from Phase 3
    - [ ] 4.1.2 Fill `todo_items` with actionable steps from Phase 2.3
    - [ ] 4.1.3 Fill `verification` with predicted metrics from Phase 3.2
    - [ ] 4.1.4 Fill `addresses` with finding IDs this suggestion resolves

#### Constraints
- Include full code snippets in suggested_fix (protocols, types, modified class)
- Todo items must be concrete and implementable (not vague)
- Preserve existing public API
- Match refactoring depth to severity (don't over-engineer MINOR violations)
