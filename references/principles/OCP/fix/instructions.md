---
name: ocp-fix
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
  - SEVERE → refactoring (see refactoring.md)

#### Phase 2: Identify Suggestions

- [ ] **2.1 Analyze findings** — read metrics (sealed points, testable dependencies)
- [ ] **2.2 Propose suggestion** — what way to comply, what pattern to use
- [ ] **2.3 Create todo items** — concrete actionable steps to implement the fix:
  - [ ] **2.3.1 Validate protocol existence** - Check for existing protocols first before creating new ones
    - if exist use it 
    - if not create protocol (name + method signatures)
  - [ ] **2.3.2 Check existing type** - Check if existing type already provides the required methods
    - if already provides the exact method/property -> extension conformance
    - if the type can provide the method via a thin forwarding call to its own properties (e.g. chained calls like `obj.child.method()` can become `obj.method() { child.method() }`) -> extension conformance with a forwarding implementation. Prefer this over creating a wrapper struct — keep the conformance on the existing type
    - only if the type cannot reasonably conform (e.g. you don't own it, it's a system type with no meaningful identity, or forwarding would require external state) -> use adapter or bridge pattern, create extracted type (name + which variables/methods move)
    - **For sealed framework/system calls** (singletons, static methods) → inspect the returned type first (see `rule.md` Exceptions §4):
      - If the returned type can be instantiated or subclassed → extension conformance + inject the instance. No wrapper needed.
      - If the returned type is already a protocol → depend on the protocol directly.
      - Only if the API is truly static-only (enum, global function, cannot instantiate) → adapter wrapper qualifies as a Boundary Adapter and is exempt from OCP-1.
   - [ ] **2.3.3 Update original class**  new dependencies, removed variables, delegation changes
  - Each todo item should be a single, implementable action

#### Phase 3: Write suggested_fix

- [ ] **3.1 Write full code snippets** showing:
    - Protocol definition
    - Extracted type with init and moved methods
    - Modified original class with injected dependency
    - Before/after of bridging method(s)
- [ ] **3.2 Predict post-fix metrics** (sealed points, testable dependencies)


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
