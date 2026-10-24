---
name: reconstruct-spec
description: "Blindly reconstructs what an architecture or implementation would deliver as a spec document. Two modes: arch (reads arch.json) or code (reads source files)."
argument-hint: <source-path> --mode <arch|code> --output <reconstructed-spec-path>
allowed-tools: Read, Write, Glob, Grep
user-invocable: false
---

# Reconstruct Spec

Reads an architecture (arch.json) or implementation (source files) and produces a reconstructed spec describing what it would deliver. Does NOT read the original spec — the reconstruction must be blind to avoid confirmation bias.

## Input

- SOURCE_PATH: $ARGUMENTS[0] — path to arch.json (mode=arch) OR directory/file list of implemented code (mode=code)
- MODE: value after `--mode` flag — `arch` or `code`. Default: `arch`
- OUTPUT_PATH: value after `--output` flag — path to write reconstructed-spec.md

## Phase 1: Read Source

### Mode: arch
- [ ] 1.1 Read arch.json from SOURCE_PATH.
- [ ] 1.2 Extract: `spec_summary`, `components[]`, `wiring[]`, `composition_root`.
- [ ] 1.3 Do NOT read any other files. Do NOT read the original spec. Your only input is arch.json.

### Mode: code
- [ ] 1.1 SOURCE_PATH is a directory or comma-separated file list. Glob/Read all source files.
- [ ] 1.2 For each file, read the **actual code logic** — not names, not comments, not descriptions. Specifically:
  - **For production code**: read method bodies — what does the code actually do? What APIs does it call? What data does it transform? What errors does it throw? What conditions does it check?
  - **For test code**: read the **assertion bodies** — what is actually being verified? Ignore test method names and comments — they may lie. Focus on:
    - What is the system under test? Real type or stub/mock?
    - What does the assertion check? Is it a meaningful condition or a tautology (e.g., `x || !x`)?
    - What inputs are provided? Real or synthetic?
    - What is NOT asserted that the test name implies?
  - **For protocols**: what methods are required? What do conformers actually implement?
  - **For dependencies**: are they injected as protocols or used as concrete types? Are singletons/statics accessed?
- [ ] 1.3 Do NOT read the original spec or arch.json. Your only input is the source code.
- [ ] 1.4 **Ignore all metadata**: comments, docstrings, `solid-*` frontmatter, `// MARK:`, `/// description` — these are claims, not behavior. Only read executable code.
- [ ] 1.5 Do NOT trust names — a test method's name may describe what it intends to test, but the body may do something entirely different. Describe what the code DOES, not what it's NAMED.

## Phase 2: Reconstruct Description

### Mode: arch
- [ ] 2.1 From `spec_summary` and the overall set of components, write a description of the feature in plain language. No implementation details — describe WHAT the feature does for the user, not HOW it's built.

### Mode: code
- [ ] 2.1 From the types and their relationships, write a description of what this code does for the user. No implementation details — describe capabilities, not classes.

## Phase 3: Reconstruct User Stories

For EACH component (or group of related components), describe the user-facing capability:

- [ ] 3.1 What can the user DO because these components exist?
  Write as: `As a [user/system], I want [goal] so that [reason]`
  - Do NOT use interface names, protocol names, or type names
  - Do NOT mention implementation patterns (injection, protocols, factories)
  - Describe the CAPABILITY, not the COMPONENT
  - Example: "As a user, I want to see my cart total update when I change quantities so that I know the current price" — NOT "As a user, I want CartViewModel to recalculate total"

- [ ] 3.2 For each story, derive acceptance criteria from what the code **actually does** (not what names suggest):
  - What inputs does the code actually accept and validate?
  - What outputs does the code actually produce?
  - What error paths does the code actually handle? (read the catch/throw/guard blocks)
  - What edge cases does the code actually cover? (read the conditional logic)

## Phase 4: Reconstruct Technical Requirements

- [ ] 4.1 List specific technical gotchas and constraints that the architecture implies:
  - Data structures and their fields (from model components)
  - API contracts and data formats (from service components)
  - Concurrency model (from stack tags: structured-concurrency, combine, etc.)
  - Platform constraints (from stack tags: swiftui, uikit, etc.)
  - Do NOT list generic SOLID patterns — only list requirements specific to this feature

## Phase 5: Reconstruct Test Plan

### Mode: arch
- [ ] 5.1 **Unit tests** — for each component with testable behavior, describe what should be tested:
  - Given (precondition) / When (action) / Expect (outcome)
  - Focus on behavior, not implementation
- [ ] 5.2 **UI tests** — for each view/screen component, describe user interaction tests:
  - What the user does / What the user should see

### Mode: code
- [ ] 5.1 **For each test file**, read every test method body and describe what it **actually verifies**:
  - What is the SUT? (real type or stub?)
  - What is set up? (real data, fixtures, or stubs?)
  - What action is performed?
  - What is asserted? Read the `#expect`/`XCTAssert` lines — what condition is checked?
  - Is the assertion meaningful? An assertion is vacuous if it's always true regardless of the SUT's behavior — any tautology, redundant condition, or assertion that doesn't constrain the result to a specific expected value
  - Write as Given/When/Then from the actual code, NOT from the test name
- [ ] 5.2 Flag tests that have **no meaningful assertions** — if a test method performs an action but doesn't constrain the outcome to a specific expected value, note it as "test exists but verifies nothing"
- [ ] 5.3 Flag tests that **claim integration but use stubs** — if the test name or description says "real" or "integration" but the code injects a stub/mock for the component under test, note it as "uses stub despite claiming real"

## Phase 6: Reconstruct Diagrams

- [ ] 6.1 **Flow diagram** — describe the data/control flow through the feature from the user's perspective
- [ ] 6.2 **Sequence diagram** — describe the key interactions between components for main operations
- [ ] 6.3 **Connection diagram** — describe what connects to what (dependencies, consumers, external systems)

## Phase 7: Write Reconstructed Spec

- [ ] 7.1 Write a markdown document to OUTPUT_PATH with:

```markdown
# Reconstructed Spec

## Description
{from Phase 2 — plain language, no implementation details}

## User Stories
{from Phase 3 — "As a... I want... so that..." with acceptance criteria}

## Technical Requirements
{from Phase 4 — specific gotchas, data structures, API contracts}

## Test Plan
### Unit Tests
{from Phase 5.1}
### UI Tests
{from Phase 5.2}

## Diagrams
### Flow
{from Phase 6.1}
### Sequence
{from Phase 6.2}
### Connections
{from Phase 6.3}
```

## Constraints

- Do NOT read the original spec or any file other than arch.json.
- Do NOT use implementation vocabulary (protocol names, type names, injection patterns) in user stories or description. Technical requirements section is the only place implementation can leak.
- Do NOT invent capabilities that aren't supported by the components — only describe what the architecture actually provides.
- Be honest about limitations — if the architecture has no error handling component, don't describe error handling.
- The reconstructed spec describes WHAT IS, not WHAT SHOULD BE.
