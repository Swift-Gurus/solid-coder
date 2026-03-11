# Architecture

## System Design

solid-coder is a **multi-agent pipeline** where each stage has a dedicated agent with constrained tools, a specific model, and a focused skill. The orchestrator skills (`/review`, `/refactor`) compose these agents into full workflows.

## Tier System

Principles are organized into tiers that determine activation and cross-checking behavior:

```
┌─────────────────────────────────────────┐
│  framework    SwiftUI, TCA              │  Activated only when imports detected
├─────────────────────────────────────────┤
│  practice     DRY, Functions/Smells     │  Always active
├─────────────────────────────────────────┤
│  core         SRP, OCP, LSP, ISP, DIP  │  Always active
└─────────────────────────────────────────┘
```

**Cross-checking is directional (upward only):**
- Core checks everything (its own tier + practice + framework)
- Practice checks itself + framework
- Framework fixes are checked by core and practice, but framework does not check core

This prevents a SwiftUI-specific fix from introducing an SRP violation.

## Agent Architecture

### Agent Definitions

Each agent is a YAML frontmatter markdown file in `agents/` specifying:
- **Model**: `opus` for reasoning-heavy work, `sonnet` for mid-tier analysis, `haiku` for mechanical tasks
- **Max turns**: Caps agentic loops (100 for implementation agents)
- **Allowed tools**: Restricts what the agent can do
- **Skills**: Which internal skills the agent can invoke

### Agent Roster

```
┌──────────────────────────────┬─────────┬────────────────────────────────────┐
│ Agent                        │ Model   │ Role                               │
├──────────────────────────────┼─────────┼────────────────────────────────────┤
│ prepare-review-input-agent   │ haiku   │ Normalizes input into JSON         │
│ principle-review-agent       │ sonnet  │ Review only (no fix)               │
│ principle-review-fx-agent    │ opus    │ Review + fix suggestion            │
│ validate-findings-agent      │ haiku   │ Filters findings to changed ranges │
│ synthesize-fixes-agent       │ opus    │ Cross-principle fix planning       │
│ refactor-implement-agent     │ opus    │ Implements code changes from plan  │
│ code-agent                   │ opus    │ Writes SOLID-compliant code        │
│ generate-report-agent        │ haiku   │ Produces HTML report               │
└──────────────────────────────┴─────────┴────────────────────────────────────┘
```

**Model assignment rationale:**
- **Opus** for agents that must reason about code semantics (review, synthesis, implementation)
- **Sonnet** for agents doing mid-tier analysis work (review without fix generation)
- **Haiku** for agents doing mechanical/structural work (input prep, validation, report generation)

## Knowledge Base Structure

Each principle in `references/` follows a consistent structure:

```
references/{PRINCIPLE}/
├── rule.md                   Metrics, severity bands, exceptions, activation
├── review/
│   ├── instructions.md       Phased detection checklist
│   └── output.schema.json    JSON schema for review output
├── fix/
│   ├── instructions.md       Fix strategy selection rules
│   └── output.schema.json    JSON schema for fix output
├── refactoring.md            Patterns with before/after Swift code
└── Examples/                 Compliant + violation Swift files
```

The `rule.md` YAML frontmatter controls:
- `activation`: `always` (core/practice) or conditional (framework — based on detected imports)
- `tier`: `core`, `practice`, or `framework`
- `required_patterns`: Design pattern references the principle needs (e.g., SRP needs `structural/facade`)

## Data Flow

All intermediate data is JSON, schema-validated at each boundary:

```
                    ┌─────────────────────┐
     User target    │  prepare-review-    │    review-input.json
   (branch/folder/  │  input-agent        │──────────────┐
    file/changes)   └─────────────────────┘              │
                                                          ▼
                    ┌─────────────────────┐    ┌──────────────────┐
                    │  principle-review-   │◄───│  Principle       │
                    │  (fx)-agent  × N    │    │  Discovery       │
                    │  (parallel)         │    │  (glob + filter) │
                    └────────┬────────────┘    └──────────────────┘
                             │
                    review-output.json + fix.json (per principle)
                             │
                             ▼
                    ┌─────────────────────┐
                    │  validate-findings  │    by-file/*.output.json
                    │  -agent             │──────────────┐
                    └─────────────────────┘              │
                             ▲                           ▼
                    ┌────────┘              ┌─────────────────────┐
                    │                       │  generate-report    │
            (review only)                   │  -agent             │
                    │                       └────────┬────────────┘
                    │                                │
                    │                         report.html
                    │
            (refactor continues)
                    │
                    ▼
           ┌─────────────────────┐
           │  synthesize-fixes   │    synthesized/*.plan.json
           │  -agent             │──────────────┐
           └─────────────────────┘              │
                                                 ▼
           ┌─────────────────────┐
           │  refactor-implement │    Modified source files
           │  -agent  × N       │    + refactor-log.json
           │  (parallel)        │
           └────────┬────────────┘
                    │
                    ▼
            Iteration Loop
           (re-review changed files, max N iterations)
```

## Output Directory Structure

Each review/refactor run produces an isolated output directory:

```
{PROJECT}/.solid_coder/review-{timestamp}/
├── prepare/
│   └── review-input.json
├── rules/
│   ├── SRP/
│   │   ├── review-output.json
│   │   └── fix.json
│   ├── OCP/
│   │   ├── review-output.json
│   │   └── fix.json
│   └── LSP/
│       ├── review-output.json
│       └── fix.json
├── by-file/
│   ├── SomeFile.swift.output.json
│   └── AnotherFile.swift.output.json
├── synthesized/           (refactor only)
│   ├── SomeFile.swift.plan.json
│   └── AnotherFile.swift.plan.json
├── report.html
└── refactor-log.json      (refactor only)
```

## JSON Schemas

Five schemas enforce data contracts between pipeline stages:

| Schema | Location | Purpose |
|--------|----------|---------|
| `prepare-review-input/output.schema.json` | Input stage | Files, changed ranges, units |
| `{PRINCIPLE}/review/output.schema.json` | Review stage | Metrics, scoring, findings |
| `{PRINCIPLE}/fix/output.schema.json` | Fix stage | Suggestions with verification |
| `validate-findings/file-output.schema.json` | Validation stage | Findings reorganized by file |
| `synthesize-fixes/plan.schema.json` | Synthesis stage | Ordered actions with cross-check results |

## Design Patterns Used in the Plugin Itself

| Pattern | Where | Why |
|---------|-------|-----|
| **Pipeline** | Review/refactor orchestrators | Each stage transforms data for the next |
| **Strategy** | Principle-specific agents | Same interface (review → findings), different rules per principle |
| **Facade** | Orchestrator skills | Hide multi-agent complexity behind `/review` and `/refactor` |
| **Template Method** | `apply-principle-review` skill | Same review algorithm, parameterized by principle-specific instructions |
| **Observer** | Iteration loop | Re-reviews react to changes from implementation |

## Parallelism Model

The system maximizes parallelism at two points:

1. **Principle review**: All active principles are reviewed simultaneously (N agents in one message)
2. **Refactor implementation**: All file-level plans are implemented simultaneously (M agents in one message)

Sequential dependencies are honored:
- Prepare input must complete before review starts
- All reviews must complete before validation
- Validation must complete before synthesis
- Synthesis must complete before implementation
