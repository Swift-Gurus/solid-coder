---
name: srp-fix
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
    - MINOR → no extraction, light touch only
    - MODERATE → extract one concern
    - SEVERE → full two-phase refactoring (see refactoring.md)

#### Phase 2: Identify Suggestions

- [ ] **2.1 Analyze findings** — read metrics (cohesion groups, verbs, stakeholders)
- [ ] **2.2 Propose suggestion** — which groups to extract, what to name them
- [ ] **2.3 Create todo items** — concrete actionable steps to implement the fix:
    - Create protocol (name + method signatures)
    - Create extracted type (name + which variables/methods move)
    - Update original class (new dependencies, removed variables, delegation changes)
    - Each todo item should be a single, implementable action

#### Phase 3: Write suggested_fix

- [ ] **3.1 Write full code snippets** showing:
    - Protocol definition
    - Extracted type with init and moved methods
    - Modified original class with injected dependency
    - Before/after of bridging method(s)
- [ ] **3.2 Predict post-fix metrics** (verbs, cohesion groups, stakeholders per type)

#### Phase 4: Generate Output

- [ ] **4.1 Produce JSON matching output schema**
    - [ ] 4.1.1 Fill `suggested_fix` with the full text + code snippets from Phase 3
    - [ ] 4.1.2 Fill `todo_items` with the actionable steps from Phase 2.3
    - [ ] 4.1.3 Fill `verification` with predicted metrics from Phase 3.2
    - [ ] 4.1.4 Fill `addresses` with finding IDs this suggestion resolves

#### Constraints
- Include full code snippets in suggested_fix (protocols, types, modified class)
- Todo items must be concrete and implementable (not vague)
- Preserve existing public API
- Match refactoring depth to severity (don't over-engineer MINOR violations)
