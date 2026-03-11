---
name: code
description: Write SOLID-compliant code with principle rules loaded as constraints. Takes a prompt, a spec file, or both.
argument-hint: [file|prompt]
allowed-tools: Read, Grep, Glob, Write, Edit
---

# Coding Skill

Write or modify code with SOLID principle rules loaded as active constraints. The rules define what constitutes a violation — this skill knows how to write code that doesn't violate.

## Input
- RULES_PATH: ${CLAUDE_PLUGIN_ROOT}/references
- INPUT: $ARGUMENTS — what to do. Can be:
  - A path to a file (spec document, plan JSON, source file to modify)
  - An inline prompt describing what to build or change
  - A combination of both

## Phase 1: Load Context

- [ ] 1.1 Parse INPUT:
  - If it contains a path to a JSON file with `file` and `directive` fields → read it as a refactor plan, extract the target source file and directive, read the target source file
  - If it contains a path to a spec/markdown file → read it as requirements
  - Treat any remaining text as the prompt (what to build)
- [ ] 1.2 If a refactor plan, read the target source file and understand its structure
- [ ] 1.3 Collect import statements from any source files involved (needed for framework-tier activation)

## Phase 2: Load Rules

- [ ] 2.1 Glob for `{RULES_PATH}/*/rule.md`
- [ ] 2.2 For each rule.md, use skill **solid-coder:parse-frontmatter** `{rule.md path}`
  - `activation: always` → load it
  - `activation: imports: [...]` → load only if any listed import is detected from Phase 1.3
- [ ] 2.3 **Load rules** — For each active rule.md, use skill **solid-coder:load-reference** `{rule.md path}` — these are the constraints
- [ ] 2.4 **Load references** — For each active rule, use skill **solid-coder:load-reference** with all paths from `files_to_load` in its step 2.2 JSON output
- [ ] 2.5 Hold all loaded rules and references in context — they apply to every line of code you write

## Phase 3: Write Code

Follow the spec. While writing, rigorously satisfy every loaded rule. The rules define metrics and thresholds — write code that stays within COMPLIANT bands.

### 3.1 Dependency Resolution

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

### 3.2 Extraction

When splitting a type along responsibility boundaries:

- Each responsibility becomes its own type
- New types get protocol-typed dependencies injected via init
- No sealed variation points in extracted types — all external dependencies protocol-typed and injected
- The original type coordinates the extracted types (becomes a facade/coordinator if multiple remain)

### 3.3 File Organization

- Protocol + its base implementation → same file, named after the implementation
  - e.g. `ProductFetchService.swift` contains `protocol ProductFetching` + `final class ProductFetchService: ProductFetching`
- Additional conformers (decorators, adapters, alternatives) → separate file each, named after the conformer
- Small helpers (<10 lines, or private/fileprivate) → stay in the source file
- New files go in the same directory as the source file
- Copy necessary `import` statements to each new file

### 3.4 Protocol Design

- Every conformer must meaningfully implement every method. If a conformer would leave methods empty or crash (fatalError), the protocol is too wide — split it.
- Client code must not type-check against conformers (`is`, `as?`, `as!`). If it needs to, the abstraction is wrong — redesign it.

## Phase 4: Self-Check

After writing all code, verify your output against every loaded rule:

- [ ] 4.1 For every file you created or modified, run through each loaded `rule.md`'s metrics against your code
- [ ] 4.2 If any metric crosses a severity threshold into SEVERE, fix it inline
- [ ] 4.3 If a fix introduces logic governed by a principle you haven't loaded yet, load that `rule.md` and check again
- [ ] 4.4 Repeat until all loaded rules read COMPLIANT or MINOR on your output

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
