---
name: isp-fix
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
  - MINOR → no splitting, light touch only (document intent, consider future split)
  - SEVERE → protocol splitting refactoring (see refactoring.md)

#### Phase 2: Identify Suggestions

- [ ] **2.1 Analyze findings** — read metrics (protocol width, conformer coverage, cohesion groups)
- [ ] **2.2 Determine split strategy** based on cohesion groups:
  - If 2+ cohesion groups → split along group boundaries
  - If single group but width > 8 → split by read/write or by concern
  - If low coverage on specific conformers → extract unused methods into separate protocol
- [ ] **2.3 Create todo items** — concrete actionable steps to implement the fix:
  - [ ] **2.3.1 Check existing protocols** — look for existing narrow protocols that cover the needed methods before creating new ones
  - [ ] **2.3.2 Define new protocols** — name + method signatures for each split protocol
  - [ ] **2.3.3 Create composition protocol** — if consumers need the full interface, provide `protocol FullProtocol: NarrowA, NarrowB {}`. **Use `protocol` not `typealias`** — a typealias cannot be conformed to directly (`class Decorator: MyTypealias` does not compile), which breaks the decorator pattern and any wrapper that needs to conform to the combined type.
  - [ ] **2.3.4 Update conformers** — change conformance declarations to only the protocols they meaningfully implement
  - [ ] **2.3.5 Update consumers** — change parameter/property types from wide protocol to the narrowest protocol that satisfies their usage
  - Each todo item should be a single, implementable action

#### Phase 3: Write suggested_fix

- [ ] **3.1 Write full code snippets** showing:
  - New narrow protocol definitions
  - Composition protocol (if needed)
  - Updated conformer declarations
  - Updated consumer signatures
  - Before/after of key types
- [ ] **3.2 Predict post-fix metrics** (protocol width per new protocol, conformer coverage per new protocol)

#### Phase 4: Generate Output

- [ ] **4.1 Produce JSON matching output schema**
  - [ ] 4.1.1 Fill `suggested_fix` with full text + code snippets from Phase 3
  - [ ] 4.1.2 Fill `todo_items` with actionable steps from Phase 2.3
  - [ ] 4.1.3 Fill `verification` with predicted metrics from Phase 3.2
  - [ ] 4.1.4 Fill `addresses` with finding IDs this suggestion resolves

#### Constraints
- Include full code snippets in suggested_fix (protocols, conformers, consumers)
- Todo items must be concrete and implementable (not vague)
- Preserve existing public API — use composition protocol to avoid breaking callers
- Match refactoring depth to severity (don't split MINOR protocols)
- Prefer composition protocol (`protocol P: A, B {}`) over typealias (`typealias P = A & B`) — typealiases cannot be conformed to, breaking decorators
- Prefer composition over inheritance for combining narrow protocols
