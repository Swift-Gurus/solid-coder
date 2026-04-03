---
name: code
description: Write SOLID-compliant code with principle rules loaded as constraints. Takes a prompt, a spec file, or both.
argument-hint: [file|prompt]
allowed-tools: Read, Grep, Glob, Write, Edit, Skill
user-invocable: true
---

# Coding Skill

Write or modify code with SOLID principle rules loaded as active constraints. The rules define what constitutes a violation — this skill knows how to write code that doesn't violate.

## Input
- RULES_PATH: ${CLAUDE_PLUGIN_ROOT}/references
- MODE: $ARGUMENTS[0] — one of `refactor`, `implement`, or `code`
- Arguments per mode:
  - `refactor`: PLANS_DIR = $ARGUMENTS[1], OUTPUT_ROOT = $ARGUMENTS[2]
  - `implement`: PLAN_DIR = $ARGUMENTS[1] (directory containing chunk files: `01-plan.json`, `02-plan.json`, etc.)
  - `code`: PROMPT = $ARGUMENTS[1..] (spec file path, inline prompt, or both)

## Phase 1: Load Context

Read MODE and load context for that mode.

### Mode: refactor

- [ ] 1.1 Glob `{PLANS_DIR}/*.plan.json` to discover all plan files
- [ ] 1.2 Read each plan JSON — each has `file_path` + `actions[]`
- [ ] 1.3 For each plan: read `file_path` as the target source file
- [ ] 1.4 Iterate actions in order (respecting `depends_on`). For each action: use `todo_items` as implementation steps, `suggested_fix` as reference code, `resolves` for traceability

### Mode: implement

- [ ] 1.1 Glob `{PLAN_DIR}/*.json` and sort alphabetically to get chunk files in order (`01-plan.json`, `02-plan.json`, etc.)
- [ ] 1.2 Read the first chunk to extract `matched_tags[]` — store as TAGS for Phase 2 principle discovery
- [ ] 1.3 Note top-level `acceptance_criteria[]` for cross-cutting verification in Phase 4
- [ ] 1.4 Continue to Phase 2 to load rules before writing any code

After Phase 2, process each chunk sequentially in Phase 3:
- For each chunk file, read it, then for each plan item in the chunk:
  - **Design references**: if the item has `design_references[]` with `type: "file"`, Read the screenshot file now. Study layout, spacing, colors, element sizes, and composition before writing code. For `type: "inline"`, read the embedded content as layout/structure reference.
  - **Code**: use `directive` as the instruction, `action` + `file` as the target, `acceptance_criteria` as verification checklist
  - **Tests**: for `test_cases[]`, implement each test case exactly as described. Each entry has `type` (unit/ui/integration) and `description` with `given`/`when`/`expect`. Do not invent additional tests, do not skip any.

### Mode: code (default if omitted)

- [ ] 1.1 If PROMPT contains a path to a spec/markdown file → read it as requirements
- [ ] 1.2 Treat any remaining text as the prompt (what to build)
- [ ] 1.3 Continue to Phase 2 — do not start writing code until rules are loaded

## Phase 2: Discover & Load Rules

- [ ] 2.1 Use skill **solid-coder:discover-principles** with: `--refs-root {RULES_PATH}`
- [ ] 2.2 Filter principles by mode:

  **implement**:
  - [ ] 2.2.1 Use skill **solid-coder:discover-principles** with: `--refs-root {RULES_PATH} --matched-tags {TAGS as comma-separated}`
  - [ ] 2.2.2 Use `active_principles` from the output

  **refactor**:
  - [ ] 2.2.1 If `all_candidate_tags` is non-empty AND Phase 1 loaded source files → scan source files for imports and code patterns that match the candidate tags
  - [ ] 2.2.2 Use skill **solid-coder:discover-principles** with: `--refs-root {RULES_PATH} --matched-tags {scanned tags as comma-separated}`
  - [ ] 2.2.3 Use `active_principles` from the output

  **code**:
  - [ ] 2.2.1 Use all principles from step 2.1 (no filtering — code mode is drafting)
  
- [ ] 2.3 For each active principle, use skill **solid-coder:parse-frontmatter** with its rule.md path. Store the returned `files_to_load` array.
- [ ] 2.4 **Load rules** — For each active rule.md, use skill **solid-coder:load-reference** with the rule.md path.
- [ ] 2.5 **Load references** — For each active rule, use skill **solid-coder:load-reference** with each path from the `files_to_load` array (step 2.3).
- [ ] 2.6 **Load fix instructions** — For each active principle, use skill **solid-coder:load-reference** with `{principle_dir}/fix/instructions.md`. These contain fix patterns and strategies to follow when writing code.
- [ ] 2.7 Hold all loaded rules, references, fix instructions, and coding patterns in context — they apply to every line of code you write. Note: if a principle's `files_to_load` included `code/rule.md`, it was already loaded in step 2.5 — these contain coding patterns and guidelines for that domain.

## Phase 3: Write Code

Before writing any code, review all loaded rule.md metrics and fix/instructions.md patterns from Phase 2. These are active constraints — apply them proactively while writing, don't defer to the self-check. If any principle included a `code/rule.md`, treat each gotcha as a hard constraint.

### Steps

- [ ] 3.1 For each plan item (in dependency order), write code following `directive` and `acceptance_criteria`. Apply the constraints below to every line of code.
- [ ] 3.2 For each plan item with `design_references`: re-read the design screenshots and verify your code matches the layout, spacing, colors, and element sizes before moving to the next item.
- [ ] 3.3 After creating or extracting any new type, use skill **solid-coder:create-type** on the file(s) to enforce naming conventions, file organization, and `/** solid-... */` frontmatter.

### Constraints (apply to all code written above)

#### Dependency Resolution

When your code needs to use a concrete dependency, follow this decision tree:

```
Encounter concrete dependency (.shared, .default, static call, direct instantiation) →

1. Search project source for the type declaration (Grep/Glob)

2. Type found in project source?
   → YES: Does it already have a protocol?
     → YES: Use the existing protocol. Inject the instance via init.
     → NO:  Can you instantiate or subclass it? (not enum-static-only, not global func)
       → YES: Write extension conformance to a new protocol. Inject the instance via init.
       → NO:  Boundary adapter — wrap in a struct behind a protocol.
   → NO (external SDK / system framework):
     Can you instantiate or subclass it?
       → YES: Write extension conformance to a new protocol. Inject the instance via init.
       → NO:  Boundary adapter — wrap in a struct behind a protocol.

3. Type not found anywhere (not in project, not in SDK) → helper exception, don't wrap.
```

IMPORTANT: Always search before creating. Do not create new protocols or wrappers without first checking if one already exists in the project.

#### Extraction

When splitting a type along responsibility boundaries:

- Each responsibility becomes its own type
- New types get protocol-typed dependencies injected via init
- No sealed variation points in extracted types — all external dependencies protocol-typed and injected
- The original type coordinates the extracted types (becomes a facade/coordinator if multiple remain)

#### File Organization

- Protocol + one implementation → same file, named after the implementation
  - e.g. `ProductFetchService.swift` contains `protocol ProductFetching` + `final class ProductFetchService: ProductFetching`
  - Additional conformers (decorators, adapters, alternatives) → separate file each, named after the conformer
- Small helpers (<10 lines, or private/fileprivate) → stay in the source file
- New files go in the same directory as the source file
- Copy necessary `import` statements to each new file

#### Protocol Design

- Every conformer must meaningfully implement every method. If a conformer would leave methods empty or crash (fatalError), the protocol is too wide — split it.
- Client code must not type-check against conformers (`is`, `as?`, `as!`). If it needs to, the abstraction is wrong — redesign it.

## Phase 4: Self-Check

After writing all code, verify your output against every loaded rule:

- [ ] 4.1 For every file you created or modified, run through each loaded `rule.md`'s metrics against your code
- [ ] 4.2 If any metric crosses a severity threshold into SEVERE, fix it inline
- [ ] 4.3 If a fix introduces logic governed by a principle you haven't loaded yet, load that `rule.md` and check again
- [ ] 4.4 Repeat until all loaded rules read COMPLIANT or MINOR on your output
- [ ] 4.5 **Design reference compliance** — for each plan item that had `design_references`, verify the implemented code matches the provided designs. For `type: "file"` references, read the file (screenshots, mockups, schemas). For `type: "inline"` references, use the embedded content (mermaid diagrams, ASCII mockups). Check layout structure, component hierarchy, spacing, naming, and behavior match the design. If any mismatch is found, fix it inline.
  - [ ] 4.5.1 Verify paddings are matched 
  - [ ] 4.5.2 Verity colors are matched
  - [ ] 4.5.3 Verify positions of elements and their sized are matched
  - [ ] 4.5.4 Verify composition of elements is matched
  - [ ] 4.5.5 Verify no text or element is clipped or overflows its container
  - [ ] 4.5.6 Verify all elements visible in the design are present in the implementation — nothing is missing
- [ ] 4.6 **Per-item acceptance criteria** — for each plan item that had `acceptance_criteria`, verify the implemented code satisfies every criterion. If any is not met, fix it inline.
- [ ] 4.7 **Cross-cutting acceptance criteria** — if the implementation plan had top-level `acceptance_criteria[]`, verify each one is satisfied across the full set of files created/modified. If any is not met, fix it inline.
- [ ] 4.8 **Build & test** (conditional) — if build, test or ui test instructions were loaded into context (e.g., from a project's CLAUDE.md or the spec), run them. Do NOT search for build systems, guess commands, or attempt to run any build/test tool on your own. If no instructions are in context, skip this step entirely.
    1. Run unit tests for the component you developed. If broken -> fix it using all the loaded rules
    2. Run full unit test suite to validate nothing's broken. If broken -> fix it using all the loaded rules
    3. If you worked on UI
       3.1. run UI tests for your logic only. If broken -> fix it using loaded rules
       3.2. run full UI tests suit. If broken -> fix it using loaded rules

Do NOT spawn another agent. Do NOT produce intermediate artifacts. Fix problems in place.

## Phase 5: Output

- [ ] 5.1 List every file created or modified
- [ ] 5.2 Brief summary of what was done and key design decisions made

## Constraints
- Follow the spec — do not invent scope beyond what was asked
- The loaded `rule.md` files are the source of truth for what constitutes a violation. Do not invent additional rules
- Always search the project before creating new protocols, wrappers, or abstractions
- Do not produce intermediate plans, JSON artifacts, or structured outputs — write code directly
- Preserve existing public API unless the spec explicitly asks to change it
- Do not add unnecessary error handling, comments, or abstractions beyond what the spec and rules require
