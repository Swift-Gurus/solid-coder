# Architecture

## System Design

solid-coder is a **multi-agent pipeline** where each stage has a dedicated agent with constrained tools, a specific model, and a focused skill. The orchestrator skills (`/review`, `/refactor`) compose these agents into full workflows.

## Activation System

Principles are activated based on **tags** in their `rule.md` frontmatter:

- **No tags** = always active (core principles like SRP, OCP, LSP, ISP)
- **Has tags** = conditionally active — only when the code matches at least one tag

```
┌─────────────────────────────────────────┐
│  framework    SwiftUI, TCA              │  tags: [swiftui], [tca] — conditional
├─────────────────────────────────────────┤
│  practice     DRY, Functions/Smells     │  No tags — always active
├─────────────────────────────────────────┤
│  core         SRP, OCP, LSP, ISP, DIP  │  No tags — always active
└─────────────────────────────────────────┘
```

**Discovery flow:**
1. Orchestrator runs `discover-principles` skill → gets all principles + `all_candidate_tags`
2. Candidate tags are passed to `prepare-review-input` agent
3. Agent matches tags against code (imports + usage patterns) → `matched_tags` in review-input.json
4. Orchestrator runs `discover-principles` again with `--review-input` → filtered `active_principles`

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
│ apply-principle-review-agent  │ sonnet  │ Review only (no fix)               │
│ validate-findings-agent      │ haiku   │ Filters findings to changed ranges │
│ synthesize-fixes-agent       │ opus    │ Cross-principle fix planning       │
│ code-agent                   │ opus    │ Writes SOLID-compliant code        │
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
- `tags`: (optional) List of tags for conditional activation. No tags = always active. Tags present = active only when code matches at least one tag.
- `required_patterns`: Design pattern references the principle needs (e.g., SRP needs `structural/facade`)
- `examples`: (optional) Paths to example files/folders, defaults to `Examples/` if the directory exists

Frontmatter is parsed by `parse-frontmatter` (script), which resolves all paths to absolute and produces a `files_to_load` array. Content is loaded by `load-reference` (script), which strips YAML frontmatter so agents never see it. Principle discovery and tag-based filtering is handled by `discover-principles` (script/skill).

## Data Flow

All intermediate data is JSON, schema-validated at each boundary:

```
                    ┌──────────────────────┐
                    │  discover-principles │    all_candidate_tags
                    │  (script)            │──────────────┐
                    └──────────────────────┘              │
                                                          ▼
                    ┌─────────────────────┐    candidate_tags passed
     User target    │  prepare-review-    │    review-input.json
   (branch/folder/  │  input-agent        │    (with matched_tags)
    file/changes)   └─────────────────────┘──────────────┐
                                                          ▼
                    ┌──────────────────────┐   ┌──────────────────┐
                    │  discover-principles │◄──│  review-input    │
                    │  --review-input      │   │  .json           │
                    │  (filter mode)       │   └──────────────────┘
                    └────────┬─────────────┘
                             │ active_principles
                             ▼
                    ┌─────────────────────┐
                    │  principle-review-   │
                    │  (fx)-agent  × N    │
                    │  (parallel)         │
                    └────────┬────────────┘
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
            (review only)                   │  (script, no agent) │
                    │                       └────────┬────────────┘
                    │                                │
                    │                        report.md + report.html
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
├── report.md
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
- Principle discovery must complete before prepare input (to get candidate tags)
- Prepare input must complete before filtering (to get matched tags)
- Filtering must complete before review starts (to get active principles)
- All reviews must complete before validation
- Validation must complete before synthesis
- Synthesis must complete before implementation
