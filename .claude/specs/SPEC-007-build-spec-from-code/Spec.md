---
number: SPEC-007
feature: build-spec-from-code
status: draft
blocked-by: []
blocking: []
---

# build-spec-from-code — Code-to-Spec Decomposer

## Description

User-invocable skill that reads one or more existing source files or folders, decomposes the code into a structured understanding (purpose, inputs, outputs, dependencies, connections to project modules), then interviews the user to confirm and refine before writing a spec file.

Useful for creating specs for existing, unspecced modules — or for capturing the "what and why" of a piece of code before refactoring or extending it.

## Input

- `$ARGUMENTS` — one or more file paths or folder paths (e.g., `skills/plan/SKILL.md`, `references/SRP/`).

## Output

A spec markdown file written to `{CURRENT_PROJECT}/.claude/specs/SPEC-NNN-<slug>.md` with the same structure produced by `build-spec`:
- YAML frontmatter: `number`, `feature`, `status: draft`, `blocked-by`, `blocking`
- Body: Description, Inputs/Outputs, Workflow phases, Connects To, Design Decisions, Definition of Done

## Workflow

### Phase 1: Read and Analyse Code

- [ ] 1.1 **Collect files** — for each argument:
  - If a file path: add directly to the read list
  - If a folder path: Glob `<folder>/**/*` and collect all text files (`.md`, `.swift`, `.json`, `.py`, `.yaml`)
- [ ] 1.2 **Read all files** — read each file in the collected list.
- [ ] 1.3 **Decompose** — from the code, extract:
  - **Purpose**: what does this module do? one-sentence summary
  - **Module type**: skill (user-invocable / internal), agent, principle, utility script
  - **Inputs**: arguments, file paths, JSON schemas consumed
  - **Outputs**: files written, JSON returned, side effects
  - **Internal phases**: major steps or phases in the workflow
  - **Tool usage**: which tools does the code use (Bash, Read, Glob, Grep, Write, Edit, etc.)
  - **External dependencies**: other skills/agents/principles referenced (look for `solid-coder:` references, script paths, imports)

### Phase 2: Discover Spec Context

- [ ] 2.1 **Find next spec number** — Glob `.claude/specs/*.md` and all `skills/*/.claude/CLAUDE.md` files. For each, use skill **solid-coder:parse-frontmatter** to read `number` field. Find the highest `SPEC-NNN` value; set `next_number = NNN + 1` (zero-padded to 3 digits).
- [ ] 2.2 **Catalogue existing modules** — Glob `skills/*/SKILL.md` and use skill **solid-coder:parse-frontmatter** to extract `name`, `description`, `user-invocable`. Glob `agents/*.md` and extract `name`, `description`. Use skill **solid-coder:discover-principles** with `--refs-root references/` to get principle names.
- [ ] 2.3 **Match connections** — from the external dependencies extracted in Phase 1.3, match against the module catalogue to produce a pre-selected connections list.

### Phase 3: Confirmation Interview

Ask the user focused questions to confirm or adjust the analysis:

1. **Feature name** — confirm or override the skill's inferred `feature` name (shown as a suggested value).
2. **Purpose** — confirm or override the inferred one-sentence purpose.
3. **Connections** — confirm the auto-matched connections list (multi-select from full catalogue; pre-selected from Phase 2.3). User can deselect or add.
4. **Dependency chain**:
   - `blocked-by`: which existing SPECs must be done before this? (multi-select from `existing_specs[]`)
   - `blocking`: which existing SPECs depend on this being done first? (multi-select from `existing_specs[]`)

### Phase 4: Generate Draft Spec

Using the code analysis + confirmed interview answers, generate a full spec:

- **Frontmatter**: `number`, `feature`, `status: draft`, `blocked-by`, `blocking`
- **Description**: derived from confirmed purpose + module type
- **Input / Output table**: from Phase 1.3 inputs/outputs
- **Workflow**: phased checklist reconstructed from Phase 1.3 internal phases, using `solid-coder:<skill>` references for delegated work
- **Connects To table**: from confirmed connections (Phase 3)
- **Design Decisions**: inferred from code patterns (e.g., script-based execution, parse-frontmatter delegation, agent wrapping)
- **Definition of Done**: verifiable checklist based on module type and outputs

### Phase 5: Review Loop (max 2 rounds)

- [ ] 5.1 Present the full draft spec to the user.
- [ ] 5.2 Ask: "Does this look correct? Any changes needed?" (yes / needs changes)
- [ ] 5.3 If "needs changes": ask the user to describe what to adjust, incorporate changes, re-present. Limit to 2 revision rounds.
- [ ] 5.4 If "yes" (or after 2 rounds): proceed to Phase 6.

### Phase 6: Write Spec File

- [ ] 6.1 Derive filename slug from `feature` value: lowercase, spaces → hyphens, strip special chars.
- [ ] 6.2 Write spec to `.claude/specs/SPEC-{next_number}-{slug}.md`.
- [ ] 6.3 Confirm to user: `Spec written: .claude/specs/SPEC-{next_number}-{slug}.md`

## Connects To

| Skill | Phase | Relationship |
|-------|-------|-------------|
| `solid-coder:parse-frontmatter` | 2 | Read frontmatter from existing specs + skill files for discovery |
| `solid-coder:discover-principles` | 2 | List available principles as connection candidates |

## Design Decisions

- **Analysis before interview** — reading code first allows the skill to pre-populate answers, reducing interview burden to confirmation rather than blank-slate recall.
- **Interview confirms, not dictates** — the skill infers as much as possible from code; the user only needs to correct what's wrong.
- **Reconstructed workflow from code** — the spec's workflow phases are reverse-engineered from the actual implementation. This captures real behavior rather than idealized intent.
- **Same output format as build-spec** — both skills produce identical spec structure so downstream tools (implement, validate) work uniformly.
- **Review loop capped at 2 rounds** — consistent with `build-spec`.
- **parse-frontmatter for all discovery** — consistent with project conventions, no hand-rolled YAML parsing.

## Gotchas

- If the provided path points to a folder with many files (e.g., an entire feature), the skill reads all text files. For very large folders, prioritize `SKILL.md`, `.claude/CLAUDE.md`, `scripts/`, and schema files — skip generated outputs and large data files.
- The skill does NOT modify any source files — it only writes the spec file.
- Do not infer `status: done` even if the code appears fully implemented. Status is set by the spec lifecycle process, not by code analysis.

## Definition of Done

- [ ] `skills/build-spec-from-code/SKILL.md` exists with `user-invocable: true`
- [ ] `skills/build-spec-from-code/.claude/CLAUDE.md` contains this spec (status: done)
- [ ] Registered in root `.claude/CLAUDE.md` user-invocable skills table
- [ ] Correctly reads files and folders, including recursive folder expansion
- [ ] Extracts purpose, inputs, outputs, phases, and connections from source code
- [ ] Correctly discovers next SPEC number
- [ ] Interview pre-populates answers from code analysis
- [ ] Produces spec with valid frontmatter and full body structure
- [ ] Written to `{CURRENT_PROJECT}/.claude/specs/SPEC-NNN-<slug>.md`