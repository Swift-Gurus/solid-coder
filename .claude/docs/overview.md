# solid-coder — Project Overview

## What Is It

**solid-coder** is a Claude Code plugin that reviews, refactors, and writes Swift code using SOLID principles as enforceable, metric-driven rules. It is not a linter or a set of guidelines — it is a multi-agent pipeline that detects violations, plans cross-principle-safe fixes, and implements them.

**Author:** Alex Crowe
**Version:** 1.0.0

## Core Idea

Each SOLID principle is encoded as:

- **Quantitative metrics** (verb counts, cohesion groups, sealed points, type checks, etc.)
- **Severity bands** (COMPLIANT / MINOR / SEVERE) derived from those metrics
- **Exceptions** (facades, helpers, boundary adapters, NoOp objects) that override severity
- **Fix patterns** (extract, inject, adapt, split) tied to specific violation types

Agents don't guess whether code is "good." They measure, classify, and act.

## User-Facing Skills (Entry Points)

| Skill | Command | What It Does |
|-------|---------|--------------|
| **Review** | `/review` | Read-only analysis. Produces an HTML report with findings and fix suggestions per file. |
| **Refactor** | `/refactor` | Full pipeline: review + holistic fix planning + code modification + iterative re-review. |
| **Code** | `/code` | Writes or modifies Swift code with all active rules loaded as constraints. Self-checks after writing. |

## Project Layout

```
solid-coder/
├── .claude-plugin/           Plugin registration (plugin.json)
├── agents/                   Subagent definitions (YAML frontmatter + instructions)
├── references/               SOLID knowledge base
│   ├── ARCHITECTURE.md       System design document
│   ├── SRP/                  Single Responsibility Principle
│   ├── OCP/                  Open/Closed Principle
│   ├── LSP/                  Liskov Substitution Principle
│   ├── ISP/                  Interface Segregation Principle
│   └── design_patterns/      Shared pattern references (strategy, adapter, decorator, facade)
├── skills/                   Skill definitions + scripts
│   ├── review/               Orchestrator: review pipeline
│   ├── refactor/             Orchestrator: refactor pipeline
│   ├── code/                 SOLID-aware code writer
│   ├── apply-principle-review/   Per-principle review runner
│   ├── prepare-review-input/     Input normalizer + diff parser
│   ├── validate-findings/        Finding filter + reorganizer
│   ├── synthesize-fixes/         Cross-principle fix planner
│   ├── generate-report/          HTML report generator
│   ├── parse-frontmatter/        YAML frontmatter parser → JSON with resolved paths
│   ├── load-reference/           Reference loader with frontmatter stripping
│   └── discover-principles/      Principle discovery + tag-based filtering
└── requirements.txt          Python deps (pytest, jsonschema)
```

## Principles Currently Implemented

| Principle | Tier | Status |
|-----------|------|--------|
| SRP (Single Responsibility) | core | Active |
| OCP (Open/Closed) | core | Active |
| LSP (Liskov Substitution) | core | Active |
| ISP (Interface Segregation) | core | Active |
| DIP (Dependency Inversion) | core | Planned |
| DRY | practice | Planned |
| Functions/Smells | practice | Planned |
| SwiftUI | framework | Planned |
| TCA | framework | Planned |

## Technology Stack

- **Orchestration:** Claude Code skills + subagents (YAML-defined)
- **Models:** Opus (for review, synthesis, implementation), Sonnet (for review without fix), Haiku (for input prep, validation, report generation)
- **Scripts:** Python 3 (diff parsing, finding validation, report generation)
- **Target Language:** Swift
- **Output:** JSON findings/plans + self-contained HTML reports
