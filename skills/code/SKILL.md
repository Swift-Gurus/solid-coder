---
name: code
description: Write SOLID-compliant code with principle rules loaded as constraints. Takes a prompt, a spec file, or both.
argument-hint: [file|prompt]
allowed-tools: Read, Grep, Glob, Write, Edit, Skill, Bash
user-invocable: true
---

# Coding Skill

Write or modify code with SOLID principle rules loaded as active constraints. The rules define what constitutes a violation — this skill knows how to write code that doesn't violate.

## Input
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

- [ ] 2.1 Determine matched tags by mode:

  **implement** mode: use TAGS from Phase 1.2
  
  **refactor** mode: run `! python3 ${CLAUDE_PLUGIN_ROOT}/mcp-server/gateway.py get_candidate_tags`, then scan source files for imports/patterns matching the candidate tags

  **code** mode (default): no tags (load all principles)

- [ ] 2.2 Use skill **solid-coder:load-reference** with: `--mode code` and `--matched-tags {tags}` (if any). The server resolves what to load based on the mode (see `mcp-server/modes.py`): rule.md + code/instructions.md + required_patterns. No fix instructions, no examples — focused coding context.

## Phase 3: Write Code
Apply every constraint from the Phase 2 summary to every line of code. Do NOT defer to the self-check — violations must be prevented, not detected after the fact.

### Steps

- [ ] 3.1 For each plan item (in dependency order), 
  - [ ] 3.1.1 - summarize your idea what you are going to implement based on `directive` and `acceptance_criteria`. Print it out
  - [ ] 3.1.2 - validate your idea using loaded rules, if it violates, redesign approach by repeating 3.1.1 and 3.1.2 until it doesn't violate
  - [ ] 3.1.3 - write code following your polished idea
  - [ ] 3.1.4 - validate your code using loaded rules, if it violates repeat from 3.1.1 by choosing different approach
  - [ ] 3.1.5 - summarize what was done, what violations where found, how they were resolved
- [ ] 3.2 For each plan item with `design_references`: re-read the design screenshots and verify your code matches the layout, spacing, colors, and element sizes before moving to the next item.

- [ ] 3.3 After creating or extracting any new type, static function, helpers, use skill **solid-coder:create-type** on the file(s) to enforce naming conventions, file organization, and `/** solid-... */` frontmatter. Pass `--spec {spec_number}` if `spec_number` is present in the loaded plan.

### Plan extension.
- stick as close to the plan as possible.
- always reuse what already exist, must use DRY principle instructions how to find.

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
- Group files representing the same domain under the same directory (files that has the same prefix, represent the same domain, functionality)

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
Do NOT spawn another agent. Do NOT produce intermediate artifacts. Fix problems in place.

## Phase 5: Build & Test

Use commands from CLAUDE.md instructions already in context. If no build/test commands are available in context, skip this phase and explicitly state why.

- [ ] 5.1 **Build your targets** — build the target(s) containing the files you created or modified. Wait for the result before proceeding.
  - Fix all compiler errors, compiler warnings, and linter errors/warnings. Fix the code, never modify lint rules or build configuration.
  - Rebuild until the target compiles clean.
- [ ] 5.2 **Build your test targets** — build the test target(s) for the tests you created or modified. Wait for the result before proceeding.
  - Fix all compiler errors, compiler warnings, and linter errors/warnings in test code.
  - Rebuild until the test target compiles clean.
- [ ] 5.3 **Run your unit tests** — 
  - [ ] 5.3.1 - run unit tests for the component you developed or modified. 
  - [ ] 5.3.2 - Wait for the result before proceeding. 
  - [ ] 5.3.3 - If broken, MUST fix following all loaded `rule.md` and `instruction.md`, re-run until green.
  - [ ] 5.3.4 - If green move to step 5.4
- [ ] 5.4 **Run full unit test suite** — 
  - [ ] 5.4.1 - run all unit tests. 
  - [ ] 5.4.2 - Wait for the result before proceeding. 
  - [ ] 5.4.3 - If broken, MUST fix following all loaded `rule.md` and `instruction.md`, re-run until green.
  - [ ] 5.4.4 - If green move to step 5.5
- [ ] 5.5 **Run your UI tests** — 
  - [ ] 5.5.1 - run UI tests for the component(s) you worked on. 
  - [ ] 5.5.2 - If no UI tests exist for your component → skip this step only, proceed to 5.6. 
  - [ ] 5.5.3 - Wait for the result before proceeding. 
  - [ ] 5.5.4 - If broken, MUST fix following all loaded `rule.md` and `instruction.md`, re-run until green.
  - [ ] 5.5.4 - If green move to step 5.6
- [ ] 5.6 **Run full UI test suite** — 
  - [ ] 5.6.1 - run the full UI test suite. 
  - [ ] 5.6.2 - If no UI test suite exists in the project → skip this step only, proceed to 5.7. 
  - [ ] 5.6.3 -  Wait for the result before proceeding. 
  - [ ] 5.6.4 - If broken, MUST fix following all loaded `rule.md` and `instruction.md`, re-run until green.
  - [ ] 5.6.4 - If green move to step 5.7
- [ ] 5.7 If any step was skipped, explicitly state which step and why.

## Phase 6: Output

- [ ] 6.1 List every file created or modified
- [ ] 6.2 Brief summary of what was done and key design decisions made

## Constraints
- Follow the spec — do not invent scope beyond what was asked
- The loaded `rule.md` and `instructions.md`  files are the source of truth for what constitutes a violation and how to write and fix code. MUST be followed. Do not invent additional rules
- Always search the project before creating new protocols, wrappers, or abstractions
- Do not produce intermediate plans, JSON artifacts, or structured outputs — write code directly
- Preserve existing public API unless the spec explicitly asks to change it
- Do NOT add code comments, inline comments, or mark comments (// MARK:, // TODO:, // FIXME:) — write self-documenting code instead
- Fix all compiler errors, compiler warnings, and linter errors/warnings — including pre-existing ones unrelated to your changes. "Pre-existing" is not a valid reason to leave a warning or error unfixed.
- NEVER run build or test commands as background tasks — always run in foreground and wait for completion before proceeding.
- NEVER run Phase 5 steps in parallel — always sequential, one step at a time.
- NEVER truncate output — no `head`, `tail`, `| head -N`, or line limits on any command, script, or file read. Always read the full content.
- NEVER use `cat`, `head`, `tail`, `less`, or any shell command to inspect source files — use the Read tool. Reading a file you just wrote via `cat` duplicates it in context through a separate channel and wastes tokens.
- **Write before building**: complete all plan items' Write/Edit operations for this chunk BEFORE running any build or test. Do not interleave write → build → fix → write → build. One build surfaces all errors at once; ten iterative builds produce ten rounds of redundant output and re-reads.
