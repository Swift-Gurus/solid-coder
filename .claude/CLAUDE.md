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
| `refactor` | `/refactor <target> [--iterations N]` | Full review/synthesize/implement/iterate loop |
| `code` | `/code <prompt or spec>` | Writes code with principle rules loaded as constraints |
| `review` | `/review <target>` | Fans out parallel per-principle reviews across all matched principles |

### Internal (used by workflows and agents)

These are triggered by other skills or agents — not directly by the user:

| Skill | What it does |
|-------|-------------|
| `plan` | Architecture decomposition — reads a spec, produces `arch.json` with components, protocols, wiring, and composition root |
| `apply-principle-review` | Single-principle review — reads rule.md, applies metrics, produces findings |
| `synthesize-fixes` | Holistic fix planner — sees ALL findings, cross-checks every fix against ALL principles, produces unified plan per file |
| `fix-suggest` | Per-principle fix suggestion from findings |
| `create-type` | Enforces naming conventions and file organization when creating new types |
| `prepare-review-input` | Normalizes input (branch, folder, files) into structured `review-input.json` |
| `discover-principles` | Discovers principles from `references/` and filters by input tags |
| `validate-findings` | Filters findings to changed code only, reorganizes outputs by file |
| `generate-report` | Produces HTML report from validated findings and suggestions |
| `parse-frontmatter` | Parses YAML frontmatter from markdown files. Utility |
| `validate-plan` | Validates arch.json against the codebase — finds reusable types, conflicts, annotates components with reuse status |
| `load-reference` | Loads reference files with frontmatter stripped. Utility |

## Agents

Agent wrappers allow skills to run as subagents — enabling parallel execution within a parent workflow. A skill that needs to run concurrently (e.g., multiple principle reviews in parallel) is wrapped in an agent definition so it can be spawned as an isolated subagent.

| Agent | Role |
|-------|------|
| `code-agent` | SOLID-compliant coding agent — loads principle rules as constraints |
| `synthesize-fixes-agent` | Runs the holistic fix planner |
| `principle-review-agent` | Runs a single-principle review |
| `principle-review-fx-agent` | Runs a single-principle review + fix suggestion |
| `plan-agent` | Architecture decomposition from a feature spec |
| `refactor-implement-agent` | Implements a fix plan on a single file |
| `validate-plan-agent` | Validates arch.json against the codebase (model: sonnet) |

## Principles (`references/`)

Each principle folder contains: `rule.md` (metrics + severity bands), `fix/instructions.md` (fix patterns), `refactoring.md` (examples), `review/output.schema.json`, `fix/output.schema.json`, and `Examples/`.

| Principle | Scope |
|-----------|-------|
| `SRP` | Single Responsibility — cohesion groups, verb count |
| `OCP` | Open/Closed — sealed variation points, testability |
| `LSP` | Liskov Substitution — contract violations, type checks |
| `ISP` | Interface Segregation — fat protocols, unused conformances |
| `SwiftUI` | View best practices — body complexity, view purity, modifier chains, VM injection |

## Key Concepts

- **Principles are data** — adding a new principle means adding a folder to `references/` with the right file structure. No code changes needed.
- **Dynamic knowledge loading** — skills only load fix knowledge for principles that have findings.
- **Cross-principle verification** — the synthesizer checks every fix against every other active principle's metrics.
- **Single-attempt patching** — if a cross-check fails and the patch also fails, mark as `unresolved`. The iteration loop is the retry mechanism, not the synthesizer.
- **Unresolved findings** — not failures. They resurface as new findings in the next iteration's fresh review.
- **Iteration loop** — stateless across iterations. Each re-runs a fresh review on modified files; no state carried forward.
