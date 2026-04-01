---
name: testing-fix
type: fix
input_schema: PRINCIPLE_FOLDER_ABSOLUTE_PATH/review/output.schema.json
output_schema: output.schema.json
---

### Phase 0: Load Context

- [ ] **0.1 Read the review findings JSON** (provided as structured input_schema)
- [ ] **0.2 Read the source file** (provided as input)

#### Phase 1: Determine Fix Strategy

- [ ] **1.1 Read `scoring.final_severity` from findings**
    - MINOR → naming fixes only (rename test methods for clarity)
    - SEVERE → full restructuring based on which metrics triggered

- [ ] **1.2 Identify which metrics triggered the severity**
    - TEST-1 (isolation) → Reset State + Break Dependencies pattern
    - TEST-2 (structure) → Split + Restructure pattern
    - TEST-3 (naming) → Rename pattern
    - TEST-4 (test doubles) → Replace Doubles pattern
    - TEST-5 (setup complexity) → Extract Factory/Builder pattern
    - Multiple → combine patterns as needed

#### Phase 2: Identify Suggestions

- [ ] **2.1 Analyze findings** — read metrics (isolation tables, structure analysis, naming assessment, test double inventory, setup complexity)
- [ ] **2.2 Propose suggestion** — which tests to restructure, which doubles to replace, which names to fix, whether to extract a factory
- [ ] **2.3 Create todo items** — concrete actionable steps to implement the fix:
    - [ ] For TEST-1 (isolation):
        - Convert `static var` to instance `var` — static state persists across tests
        - Add setUp/tearDown to reset all mutable instance state
        - Remove singleton access (`.shared`, `.default`) — replace with
          injected instance if SUT supports it, otherwise note as OCP issue
        - Break test interdependencies — each test sets up its own preconditions
          independently, no test reads state written by another test
    - [ ] For TEST-2 (structure):
        - Extract conditional branches into separate test methods (one per branch)
        - Reorder into clear Arrange-Act-Assert sections separated by blank lines
        - Remove phase comments (`// Arrange`, `// Act`, `// Assert`, etc.) —
          blank lines between phases are sufficient
        - Split multi-behavior tests — one test per scenario/behavior
        - Add assertions to tests that verify nothing
        - Replace loops with parameterized tests (@Testing) or individual test cases
        - Replace `try?` with throwing `try` — mark test method as `throws`
        - Replace sleep-based waiting with `async/await` test methods
          and `await fulfillment(of:timeout:)` — put expectations inside
          test doubles so they fulfill when called by the SUT
    - [ ] For TEST-3 (naming):
        - Rename to pattern: `test_<method>_<condition>_<expectedResult>` or equivalent convention
        - Ensure every name includes what is tested, under what condition, and what should happen
        - Standardize convention across the test class
    - [ ] For TEST-4 (test doubles):
        - Replace unnecessary mocks with real instances (value types, pure logic types)
        - Replace partial mocks (SUT subclass) with proper dependency injection
        - Replace brittle internal-call verification with state-based assertions
        - Replace circular mock assertions (set mock value, assert mock returns it)
          with assertions on SUT output/state
        - For facades/coordinators: use real service implementations with their
          boundaries mocked — don't mock the direct dependencies
    - [ ] For TEST-5 (setup complexity) — read `setup_complexity.dependency_count`:
        - **< 3 dependencies**: extract SUT construction to a `var sut` computed
          property or `setUp` method
        - **3+ dependencies**: create a dedicated SUT Factory type that:
            - Holds all mocks as stored properties with sensible defaults
            - Exposes `makeSUT()` → returns configured SUT
            - Tests access SUT via: `var sut: SUTType { factory.makeSUT() }`
        - **3+ dependencies AND different mock configurations per test**: add
          builder methods to the factory (e.g., `factory.withFailingNetwork()`,
          `factory.withEmptyCache()`) so each test declares only the condition
          it varies
    - Each todo item should be a single, implementable action

#### Phase 3: Write suggested_fix

- [ ] **3.1 Write full code snippets** showing:
    - For TEST-1: setUp/tearDown with fresh state, static vars converted to instance vars, independent test preconditions
    - For TEST-2: split test methods with clear AAA structure; expectations replacing sleep; throwing try replacing try?
    - For TEST-3: renamed test methods with descriptive names
    - For TEST-4: real instances replacing unnecessary mocks; state-based assertions replacing interaction verification; facade tests with real services and mocked boundaries
    - For TEST-5: factory type with mocks and makeSUT(); builder methods for varying conditions; computed sut property
    - Before/after of the affected test code
- [ ] **3.2 Predict post-fix metrics** (isolation violations, structure violations, naming violations, double violations, setup violations per test class)

#### Phase 4: Generate Output

- [ ] **4.1 Produce JSON matching output schema**
    - [ ] 4.1.1 Fill `suggested_fix` with the full text + code snippets from Phase 3
    - [ ] 4.1.2 Fill `todo_items` with the actionable steps from Phase 2.3
    - [ ] 4.1.3 Fill `verification` with predicted metrics from Phase 3.2
    - [ ] 4.1.4 Fill `addresses` with finding IDs this suggestion resolves

#### Constraints
- Include full code snippets in suggested_fix (test doubles, restructured tests, factories, before/after)
- Todo items must be concrete and implementable (not vague)
- Preserve test coverage — restructuring must not reduce what is verified
- Match fix depth to severity (MINOR → rename only, SEVERE → full restructure)
- When adding test doubles, prefer stubs over mocks — verify state over interactions
- When splitting tests, each new test must be independently runnable
- When creating factories, use `@discardableResult` on builder methods for chainability
