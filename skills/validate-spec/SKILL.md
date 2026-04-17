---
name: validate-spec
description: >-
  Detailed workflow for validating a spec is ready to build — covers buildability rules, required sections, story quality,
  AC-architecture alignment, and what makes a spec concrete vs vague.
  TRIGGER when: checking if a spec is ready for implementation, after editing a spec's content, or when build-spec reaches its buildability gate.
argument-hint: <spec-file-path>
allowed-tools: Read, Grep, Glob, AskUserQuestion
user-invocable: true
context: fork
model: sonnet
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

- [ ] 2.1 **Load the validation rules for this type** — Read `${CLAUDE_PLUGIN_ROOT}/spec-driven-development/specs/<type>/review/instructions.md` matching the spec's frontmatter `type` (`epic/`, `feature/`, `subtask/`, or `bug/`). Also read `specs/<type>/rule.md` for the structural contract and `specs/README.md` for common fields.
- [ ] 2.2 **Run Phase A (structural checks)** from the loaded `review/instructions.md`:
  - Verify frontmatter fields
  - Verify required sections (in order)
  - Verify conditional sections per rule.md
  - Verify diagrams completeness when diagrams are required
  - Verify forbidden sections are absent
- [ ] 2.3 **Bug status-aware check** — The bug validation rules apply status-aware structural checks automatically (draft = Phase 1 only, ready+ = Phase 1 + Phase 2 including regression test). Follow the status branches in `bug/review/instructions.md`.
- [ ] 2.4 Report missing/incorrect sections as `structural` gaps. Cite the rule file and section name in the finding.

## Phase 3: Buildability Scan

Run **Phase B** from the `<type>/review/instructions.md` loaded in Phase 2.1.

- **Epic** — Phase B contains epic-specific checks: vague scope, undefined subtasks, missing success criteria, ambiguous ownership, duplication, framework prescription. See `epic/review/instructions.md`.
- **Feature / Subtask** — Phase B contains the Standard buildability scan: user story quality, vague terms, undefined types, intent-described operations, implicit consumer contracts, unverified external APIs, ambiguous scope boundaries, implementation leaking, AC-architecture disconnects. See `feature/review/instructions.md` (subtasks reference the feature rules directly).
- **Bug** — Phase B is **skipped entirely**. Bugs are reproduction-driven, not requirement-driven. Only Phase A structural checks from Phase 2 apply. See `bug/review/instructions.md`.

Execute every check listed under "Phase B" in the loaded file. Do not invent checks beyond what the file defines. Do not merge or skip.

## Phase 4: Report

- [ ] 4.1 Group findings by category (structural, user_story_quality, vague_term, undefined_type, intent_described, implicit_contract, unverified_api, ambiguous_scope, implementation_leaking, ac_architecture_disconnect, duplication)
- [ ] 4.2 For each finding, include:
  - `category`: which check caught it
  - `location`: the phrase or section in the spec
  - `question`: what needs to be answered to resolve it
- [ ] 4.3 Print summary:

  | Category | Count |
  |----------|-------|
  | ... | ... |

  **Verdict:** `pass` (0 findings) or `needs_clarification` (>0 findings)

- [ ] 4.4 **Mode-dependent output:**
  - `--batch`: return all findings as structured output (no user interaction). The caller (build-spec) handles batching findings into a single AskUserQuestion.
  - `--interactive`: for each finding, ask the user to resolve it using AskUserQuestion. Return answers alongside findings. (Legacy mode — prefer `--batch` for fewer round-trips.)
  - No flag: report only, no user interaction.

## Constraints

- Do NOT modify the spec file — only read and report
- Do NOT invent requirements — only flag what's missing or vague in what's written
- Structural checks are based on spec type — don't require bug sections in a feature spec
- `--batch` mode returns findings without asking — the caller presents them to the user
- `--interactive` mode asks one-by-one (legacy, kept for backward compatibility)
