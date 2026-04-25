---
name: solid-coder
description: Root spec for the SOLID Coder plugin — a principle-driven code review, fix planning, and refactoring system.
type: spec
---

# SOLID Coder

A plugin that reviews Swift code against configurable principles (SOLID, SwiftUI best practices), generates cross-checked fix plans, and implements refactorings. Principles are data — each lives in `references/` with its own rule, metrics, fix instructions, and examples.

## Pipeline

The main flow is: **review -> synthesize fixes -> implement -> iterate**.

1. Input is normalized (files, branch diff, folder) into `review-input.json`
2. Principles are discovered and matched to input tags
3. Parallel per-principle reviews produce findings per file
4. Findings are validated and reorganized by file
5. Synthesizer reads ALL findings, cross-checks fixes against ALL principles, produces a unified plan per file
6. Code agent implements the plan
7. Iteration loop re-reviews modified files (up to N iterations)

## Skills

Each skill encapsulates one dedicated workflow — a single responsibility with defined inputs, outputs, and phases. Skills are split into two categories:

### User-Invocable (slash commands)

These are invoked directly by the user via slash commands:

| Skill | Usage | What it does |
|-------|-------|-------------|
 | `build-spec` | `/build-spec <prompt>` | Interview-driven spec builder — classifies prompt, resolves ambiguity, writes spec file |
| `implement` | `/implement <spec-file>` | Spec-to-code orchestrator — architects, validates, synthesizes, implements, and reviews a feature |
| `refactor` | `/refactor <target> [--iterations N] [--review-only]` | Full review/synthesize/implement/iterate loop. `--review-only` stops after synthesize (no code changes). |
| `code` | `/code <prompt or spec>` | Writes code with principle rules loaded as constraints |
| `review` | `/review <target>` | Thin wrapper: runs `/refactor --review-only` then emits aggregated MD + HTML report |
| `build-spec-from-code` | `/build-spec-from-code <path>` | Analyzes existing code, extracts functionalities as stories, produces rewrite spec with subtasks |

### Internal (used by workflows and agents)

These are triggered by other skills or agents — not directly by the user:

| Skill | What it does |
|-------|-------------|
| `plan` | Architecture decomposition — reads a spec, produces `arch.json` with components, protocols, wiring, and composition root |
| `apply-principle-review` | Single-principle review — reads rule.md, applies metrics, produces findings |
| `synthesize-fixes` | Holistic fix planner — sees ALL findings, cross-checks every fix against ALL principles, produces unified plan per file |
| `create-type` | Enforces naming conventions and file organization when creating new types |
| `prepare-review-input` | Normalizes input (branch, folder, files) into structured `review-input.json` |
| `validate-findings` | Filters findings to changed code only, reorganizes outputs by file |
| `find-spec` | Navigates spec hierarchy interactively, returns selected spec. Used by build-spec |
| `validate-spec` | Checks a spec for buildability — flags vague terms, undefined types, implicit contracts. Used by build-spec Phase 4 |
| `validate-decomposition` | Validates arch.json against SOLID principles — splits components, adds protocols, restructures hierarchies |
| `reconstruct-spec` | Reads arch.json ONLY (blind to original spec) and reconstructs what the architecture would deliver |
| `validate-completeness` | Compares reconstructed spec against original spec, diffs, adds missing components to arch.json |
| `validate-plan` | Validates arch.json against the codebase — finds reusable types, conflicts, annotates components with reuse status |
| `synthesize-implementation` | Reconciles arch.json + validation.json into ordered implementation plan of /code directives |
| `validate-implementation` | Post-code checkpoint — collects user screenshots and feedback, compares against design references, produces fix directives |

## Agents

Agent wrappers allow skills to run as subagents — enabling parallel execution within a parent workflow. A skill that needs to run concurrently (e.g., multiple principle reviews in parallel) is wrapped in an agent definition so it can be spawned as an isolated subagent.

| Agent | Role |
|-------|------|
| `code-agent` | SOLID-compliant coding agent — loads principle rules as constraints |
| `synthesize-fixes-agent` | Runs the holistic fix planner |
| `apply-principle-review-agent` | Runs a single-principle review |
| `plan-agent` | Architecture decomposition from a feature spec |
| `validate-decomposition-agent` | Validates arch.json against SOLID principles (model: sonnet) |
| `reconstruct-spec-agent` | Blindly reconstructs spec from arch.json only (model: sonnet) |
| `validate-completeness-agent` | Compares reconstructed vs original spec, adds missing components (model: sonnet) |
| `validate-plan-agent` | Validates arch.json against the codebase (model: sonnet) |
| `synthesize-implementation-agent` | Reconciles arch + validation into implementation plan (model: opus) |

## Spec Rules (`spec-driven-development/specs/`)

Shared spec rules defining the structure and validation used across `build-spec`, `build-spec-from-code`, and `validate-spec`. Each type folder mirrors the `references/principles/` pattern: `rule.md` defines the structure, `review/instructions.md` defines the validation rules.

| Folder | Files | Purpose |
|--------|-------|---------|
| `README.md` | | Common frontmatter fields, section rules, folder structure |
| `epic/` | `rule.md`, `review/instructions.md` | Large initiative broken into features/subtasks |
| `feature/` | `rule.md`, `review/instructions.md` | New capability or improvement |
| `subtask/` | `rule.md`, `review/instructions.md` | Scoped unit of work under a parent |
| `bug/` | `rule.md`, `review/instructions.md` | Two-phase: report (draft) + ready (fix planned) |

- `build-spec` / `build-spec-from-code` read `<type>/rule.md` to generate drafts.
- `validate-spec` reads `<type>/review/instructions.md` for structural + buildability checks.
- Interview flow (question batching, AskUserQuestion mechanics, round limits) lives in the `build-spec` skill — not in the per-type rules. Type-specific generation hints (e.g., "push for breadth on epics") live under "Story Depth" in `rule.md`.
- Do NOT duplicate structure in skill instructions — always reference the template files.

## Principles (`references/`)

Each principle folder contains: `rule.md` (metrics + severity bands), `fix/instructions.md` (fix patterns), `refactoring.md` (examples), `review/output.schema.json`, `fix/output.schema.json`, and `Examples/`.

| Principle | Scope |
|-----------|-------|
| `SRP` | Single Responsibility — cohesion groups, verb count |
| `OCP` | Open/Closed — sealed variation points, testability |
| `LSP` | Liskov Substitution — contract violations, type checks |
| `ISP` | Interface Segregation — fat protocols, unused conformances |
| `SwiftUI` | View best practices — body complexity, view purity, modifier chains, VM injection |

### Token Cost

Rule docs are injected into the context window on every pipeline run. Budget accordingly against the 200k context ceiling.

- **Per-principle × mode table** (how many tokens each principle costs in each mode): see @docs/token-cost-by-mode.md
- **Per-folder / per-file breakdown** (drill down into which files drive cost): see @docs/token-budget.md
  - Regenerate with: `python3 scripts/token-budget.py --out .claude/docs/token-budget.md`

**Mode load profiles** (what each pipeline mode includes from a principle folder):

| Mode | rule.md | code/instructions.md | fix/instructions.md | review/instructions.md | Examples | required_patterns |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| `code` (`/code`, `/implement` coding phase) | ✅ | ✅ | — | — | — | ✅ |
| `review` (`apply-principle-review`) | ✅ | — | — | ✅ | ✅ | ✅ |
| `planner` (`plan`) | ✅ | ✅ | ✅ | — | — | — |
| `synth-impl` (`synthesize-implementation`) | ✅ | ✅ | — | — | — | ✅ |
| `synth-fixes` (`synthesize-fixes`) | ✅ | ✅ | ✅ | — | — | ✅ |

Code-smells has no `review/` subfolder, so it is not active in review mode.

## Key Concepts

- **Principles are data** — adding a new principle means adding a folder to `references/` with the right file structure. No code changes needed.
- **Dynamic knowledge loading** — skills only load fix knowledge for principles that have findings.
- **Cross-principle verification** — the synthesizer checks every fix against every other active principle's metrics.
- **Single-attempt patching** — if a cross-check fails and the patch also fails, mark as `unresolved`. The iteration loop is the retry mechanism, not the synthesizer.
- **Unresolved findings** — not failures. They resurface as new findings in the next iteration's fresh review.
- **Iteration loop** — stateless across iterations. Each re-runs a fresh review on modified files; no state carried forward.

## Docs (`.claude/docs/`)

| File | What's in it |
|------|-------------|
| @docs/overview.md | High-level plugin overview |
| @docs/architecture.md | System architecture and data flow |
| @docs/flows.md | Detailed pipeline execution flows |
| @docs/decision-making.md | Design decisions and rationale |
| @docs/improvements-open.md | Unimplemented improvement suggestions — small/medium items |
| @docs/improvements-open-arch.md | Unimplemented improvement suggestions — large architectural items (S-26, S-32, S-33, S-42, S-43, S-44) |
| @docs/improvements-partial.md | Partially implemented improvements (12 items) |
| @docs/improvements-archive.md | Completed/resolved improvements (12 items) |
| @docs/create-type-notes.md | **Read before modifying `create-type`** — hardcoded dependencies on its vocabulary (e.g. `VALID_STACKS`) |
| @docs/token-cost-by-mode.md | Per-principle × pipeline-mode token cost table |
| @docs/token-budget.md | Auto-generated per-folder / per-file token breakdown of `references/principles/` (run `scripts/token-budget.py` to refresh) |
