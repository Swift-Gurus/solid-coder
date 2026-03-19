---
name: validate-spec
description: Validates a spec for buildability — flags vague terms, undefined types, missing signatures, implicit contracts, and unresolved design decisions.
argument-hint: <spec-file-path>
allowed-tools: Read, Grep, Glob, AskUserQuestion
user-invocable: true
---

# validate-spec — Spec Buildability Validator

Validates that a spec is concrete enough for a developer to implement without looking anything up or making unspecified design decisions.

## Input

- SPEC_FILE: `$ARGUMENTS[0]` — path to a spec file (markdown with YAML frontmatter)

## Phase 1: Load Spec

- [ ] 1.1 Read the spec file
- [ ] 1.2 Parse frontmatter (number, feature, type, status, blocked-by, blocking, parent)
- [ ] 1.3 If `parent` is set, read the parent spec for context

## Phase 2: Structural Checks

Verify the spec has all required sections for its type:

- [ ] 2.1 **All types**: Description, Diagrams, Definition of Done
- [ ] 2.2 **feature / subtask**: Input / Output, User Stories, Connects To
- [ ] 2.3 **epic**: User Stories, Features list (subtask breakdown)
- [ ] 2.4 **bug**: Steps to Reproduce, Expected vs Actual, Affected Component
- [ ] 2.5 **Technical Requirements** (conditional): `## Technical Requirements` section must be present for `subtask` specs. For `feature` specs, required only if description or user stories mention business logic, integration, APIs, or external systems. Not required for `epic` or `bug`.
- [ ] 2.6 **UI / Mockup** (conditional): if description or any user story mentions screens, views, components, or user interaction — `## UI / Mockup` section must be present and must not contain only a `<!-- TODO -->` placeholder
- [ ] 2.7 **Diagrams completeness**: `## Diagrams` section must contain at least a connection diagram and a flow diagram. If the spec mentions async operations, callbacks, delegates, notifications, network calls, or multiple distinct actors — a sequence diagram must also be present.
- [ ] 2.8 Report missing sections as `structural` gaps

## Phase 3: Buildability Scan

**If `type = epic`**: apply epic-specific checks only (Phase 3-Epic). Skip Phase 3-Standard.

**Otherwise**: apply Phase 3-Standard.

### Phase 3-Epic (epics only)

- [ ] E.1 **Vague scope** — the epic's purpose should be concrete enough that a developer can tell whether a given task is in or out of scope:
  - Flag phrases like "improve the system", "better UX", "various improvements", "general refactor"
  - For each: what specifically is being changed and why?

- [ ] E.2 **Undefined subtasks** — features listed in the subtask breakdown that are named but not scoped:
  - A subtask is undefined if its name alone doesn't communicate what needs to be built
  - For each: what does this subtask deliver?

- [ ] E.3 **Missing success criteria** — the Definition of Done should state what "done" means for the epic as a whole, not just that subtasks are complete:
  - Flag if DoD only says "all subtasks merged" or similar — what observable outcome does the epic achieve?

- [ ] E.4 **Ambiguous ownership** — behaviors or components that span multiple subtasks without a clear owner:
  - Shared state, shared protocols, or cross-cutting concerns mentioned in the epic but not assigned to a subtask
  - For each: which subtask owns this?

### Phase 3-Standard (feature / bug / subtask)

- [ ] 3.0 **User story quality** (feature / subtask only):
  - Each story must follow `As a [user/system], I want [goal] so that [reason]` format
  - Each acceptance criterion must be independently verifiable — flag: "works correctly", "handles edge cases", "behaves as expected", or any criterion that requires interpretation
  - Flag stories with no acceptance criteria
  - Flag acceptance criteria that describe implementation rather than observable behavior

- [ ] 3.1 **Vague terms** — words that hide decisions:
  - "appropriate", "safe default", "suitable", "proper", "as needed", "handle errors", "relevant", "etc."
  - For each: what specific value, behavior, or choice is meant?

- [ ] 3.2 **Undefined types** — types, protocols, or models referenced but never defined:
  - No fields listed, no signature given, no link to an existing definition
  - For each: what are the fields/methods/conformances?

- [ ] 3.3 **Intent-described operations** — workflow steps that describe what should happen but not how:
  - "instantiate with config", "parse the response", "validate input", "set up the connection"
  - For each: what is the concrete initializer, method, or API call?

- [ ] 3.4 **Implicit consumer contracts** — outputs produced but no specification of:
  - Who holds the instance and what's its lifetime (owned, shared, transient)?
  - How is it passed to consumers (init injection, environment, closure, return value)?
  - For each: who consumes this, via what mechanism?

- [ ] 3.5 **Unverified external APIs** — references to third-party libraries or system frameworks where:
  - Method signatures are described by intent rather than actual API
  - Version or availability constraints are not mentioned
  - For each: what is the actual method signature?

- [ ] 3.6 **Ambiguous scope boundaries** — places where it's unclear what this spec owns vs what another spec/module owns:
  - Shared types referenced but not assigned to a module
  - Behaviors that could live in this feature or an adjacent one
  - For each: who owns this?

## Phase 4: Report

- [ ] 4.1 Group findings by category (structural, vague_term, undefined_type, intent_described, implicit_contract, unverified_api, ambiguous_scope)
- [ ] 4.2 For each finding, include:
  - `category`: which check caught it
  - `location`: the phrase or section in the spec
  - `question`: what needs to be answered to resolve it
- [ ] 4.3 Print summary:

  | Category | Count |
  |----------|-------|
  | ... | ... |

  **Verdict:** `pass` (0 findings) or `needs_clarification` (>0 findings)

- [ ] 4.4 If called with `--interactive` or by another skill: for each finding, ask the user to resolve it using AskUserQuestion. Return answers alongside findings.

## Constraints

- Do NOT modify the spec file — only read and report
- Do NOT invent requirements — only flag what's missing or vague in what's written
- Structural checks are based on spec type — don't require bug sections in a feature spec
- When used by `build-spec` Phase 4, pass `--interactive` to enable the question loop
