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

## Phase 4: Scope & Cohesion

Runs **Phase C** from the loaded `<type>/review/instructions.md`. Skip this entire phase for `bug` (no scope checks defined) and `epic` (epics are inherently multi-responsibility).

- [ ] 4.1 **Applicability gate** — skip Phase 4 entirely if any of:
  - `type: epic` or `type: bug` (those types do not define Phase C).
  - The spec has `## Subtasks` AND no `## Technical Requirements` AND no own acceptance criteria (it's acting as an index — children carry the scope).

  If skipped, emit no Phase C findings and proceed to Phase 5.

- [ ] 4.2 **Compute output directory** — set `SCOPE_OUT = <project-root>/.solid_coder/validate-spec/<feature-slug>-<YYYYMMDDhhmmss>/scope/`. Create it (and any parents) before launching subagents.

- [ ] 4.3 **Launch THREE measurement Tasks in a SINGLE message (parallel):**

    Task 1 — heuristic LOC:
    - subagent_type: `solid-coder:predict-loc-heuristic-agent`
    - prompt:
      ```
      spec-path: <SPEC_FILE>
      output-dir: <SCOPE_OUT>
      ```

    Task 2 — skeleton LOC:
    - subagent_type: `solid-coder:predict-loc-skeleton-agent`
    - prompt:
      ```
      spec-path: <SPEC_FILE>
      output-dir: <SCOPE_OUT>
      ```

    Task 3 — cohesion clusters:
    - subagent_type: `solid-coder:cohesion-cluster-agent`
    - prompt:
      ```
      spec-path: <SPEC_FILE>
      output-dir: <SCOPE_OUT>
      ```

- [ ] 4.4 **Wait for all three to complete.** If any failed, stop and report the error. If 1–2 succeeded, you may continue with `partial: true` annotation on the eventual finding — but synthesis requires all three, so a single failure aborts Phase 4.

- [ ] 4.5 **Launch the synthesis Task** (sequential, after the three above complete):
    - subagent_type: `solid-coder:scope-synthesize-agent`
    - prompt:
      ```
      output-dir: <SCOPE_OUT>
      ```

- [ ] 4.6 **Read** `<SCOPE_OUT>/scope-assessment.json`. If `verdict == needs_split`, proceed to 4.7 to build a full split plan; otherwise skip to 4.8.

- [ ] 4.7 **Launch the propose-split Task** (sequential, only when split is recommended):
    - subagent_type: `solid-coder:propose-split-agent`
    - prompt:
      ```
      spec-path: <SPEC_FILE>
      output-dir: <SCOPE_OUT>
      ```
    - On completion, read `<SCOPE_OUT>/split-plan.json`. Use it as the body of the `split_recommendation` (or `oversized_cohesive`) finding emitted in 4.8.

- [ ] 4.8 **Translate** `scope-assessment.json` (and `split-plan.json` when present) into Phase C findings per the table in the loaded `<type>/review/instructions.md` § Phase C.3:

    | scope-assessment field | Emit finding (category, severity)                                            |
    |------------------------|------------------------------------------------------------------------------|
    | `size.severity` is `MINOR` or `SEVERE`        | `scope_oversized` at that severity                          |
    | `cohesion.severity` is `MINOR` or `SEVERE`    | `incohesive` at that severity                                |
    | `verdict == needs_split` AND `driver == size` | `oversized_cohesive` at SEVERE — body includes `split-plan.json` extraction candidates |
    | `verdict == needs_split` AND `driver == cohesion` | `split_recommendation` at SEVERE — body includes the full `split-plan.json` (parent residue + per-candidate plans + dependency order) |
    | `size.calibration_drift == true`              | `loc_calibration_drift` at MINOR                             |

## Phase 5: Report

- [ ] 5.1 Group findings by category (structural, user_story_quality, vague_term, undefined_type, intent_described, implicit_contract, unverified_api, ambiguous_scope, implementation_leaking, ac_architecture_disconnect, duplication, scope_oversized, incohesive, oversized_cohesive, split_recommendation, loc_calibration_drift).
- [ ] 5.2 For each finding, include:
  - `category`: which check caught it
  - `location`: the phrase or section in the spec
  - `question`: what needs to be answered to resolve it
  - For Phase C findings: `severity` (MINOR / SEVERE) and the per-input counts that produced the metric (read from `scope-assessment.json`).
- [ ] 5.3 Print summary:

  | Category | Count |
  |----------|-------|
  | ... | ... |

  **Verdict:**
  - `pass` — 0 findings across all phases.
  - `needs_clarification` — any Phase A or B finding, or any Phase C finding at SEVERE.
  - `advisory` — only Phase C findings at MINOR (spec is buildable but worth reviewing).

- [ ] 5.4 **Mode-dependent output:**
  - `--batch`: return all findings as structured output (no user interaction). The caller (build-spec) handles batching findings into a single AskUserQuestion.
  - `--interactive`: for each finding, ask the user to resolve it using AskUserQuestion. Return answers alongside findings. (Legacy mode — prefer `--batch` for fewer round-trips.)
  - No flag: report only, no user interaction.

## Constraints

- Do NOT modify the spec file — only read and report
- Do NOT invent requirements — only flag what's missing or vague in what's written
- Structural checks are based on spec type — don't require bug sections in a feature spec
- `--batch` mode returns findings without asking — the caller presents them to the user
- `--interactive` mode asks one-by-one (legacy, kept for backward compatibility)
