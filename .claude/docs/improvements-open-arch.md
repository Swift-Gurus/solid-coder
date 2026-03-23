# Open Improvement Suggestions — Architecture & New Features

Large architectural suggestions split from `improvements-open.md` to reduce context size.

---

## S-26: AST-based metric extraction — split counting from judgment

**Impact**: Critical | **Effort**: High | **Category**: Architecture / reliability

### Problem

The review agents currently do two jobs in one:
1. **Count** structural facts (methods, dependencies, type casts, cohesion groups)
2. **Judge** those facts against principle rules (is this a facade? is this exception legitimate?)

LLMs are unreliable at counting. Run the same review twice, get different numbers. The entire severity system rests on accurate counts — if verb count is wrong, severity is wrong, fix suggestions are wrong.

### Solution: Tree-sitter as the counting layer

[Tree-sitter](https://tree-sitter.github.io/) is a language-agnostic incremental parser used by GitHub, Neovim, and Zed. It has grammars for 100+ languages — same API, same query syntax, swap grammar files per language.

```
Current:  Code → [LLM counts + judges] → findings
Proposed: Code → [tree-sitter counts] → metrics.json → [LLM judges] → findings
```

The LLM's job shrinks from "analyze everything" to "interpret these numbers against the rules." That's where LLMs are actually strong — reasoning about data, not generating data.

### What tree-sitter extracts per principle

**SRP metrics (deterministic):**

| Metric | Tree-sitter query | Output |
|--------|------------------|--------|
| Method count | `(function_declaration name: (simple_identifier))` | `methods: ["save", "load", "validate", "format"]` |
| Property list | `(property_declaration)` | `properties: ["db", "cache", "formatter"]` |
| Property access per method | Track `(simple_identifier)` refs inside each function body | `cohesion_matrix: {"save": ["db"], "format": ["formatter"]}` |
| Dependency types | `(type_identifier)` in property/init params | `dependencies: [{"name": "Database", "is_protocol": false}]` |

**OCP metrics (deterministic):**

| Metric | Tree-sitter query | Output |
|--------|------------------|--------|
| Dependency list | Init parameters + property types | `deps: [{"name": "URLSession", "kind": "concrete"}]` |
| Static/singleton access | `(member_access_expression)` matching `.shared`, `.default` | `static_access: [".shared on line 42"]` |
| Direct construction | `(call_expression)` matching `TypeName(` | `constructions: ["Database() on line 15"]` |

**LSP metrics (deterministic):**

| Metric | Tree-sitter query | Output |
|--------|------------------|--------|
| Type cast count | `(as_expression)`, `(is_expression)` | `casts: [{"expr": "as? Dog", "line": 23}]` |
| Protocol method count | Functions inside `(protocol_declaration)` | `protocol_methods: 5` |
| Empty method bodies | Functions with `{}` or `fatalError` only | `empty_methods: ["draw()", "resize()"]` |
| Guard/precondition count | `(guard_statement)` per function | `preconditions: {"withdraw": 2}` |

### Language scaling via grammar swap

Tree-sitter grammars are separate packages. Same Python script, different grammar:

```python
import tree_sitter_swift as ts_swift
import tree_sitter_kotlin as ts_kotlin
import tree_sitter_java as ts_java

GRAMMARS = {
    ".swift": ts_swift.language(),
    ".kt": ts_kotlin.language(),
    ".java": ts_java.language(),
}

def extract_metrics(file_path: str) -> dict:
    ext = Path(file_path).suffix
    language = GRAMMARS[ext]
    parser = Parser(language)
    tree = parser.parse(Path(file_path).read_bytes())
    # Same extraction logic, different grammar
    return run_queries(tree, language)
```

**Kotlin equivalents:**

| Swift concept | Kotlin equivalent | Tree-sitter node |
|---------------|-------------------|-----------------|
| `class` | `class` | `(class_declaration)` |
| `protocol` | `interface` | `(interface_declaration)` |
| `struct` | `data class` | `(class_declaration)` with `(modifiers (data))` |
| `as?` | `as?` | `(as_expression)` |
| `.shared` | `companion object` / `object` | `(companion_object)` / `(object_declaration)` |
| `init` | constructor | `(constructor_declaration)` |

The SOLID principles are language-agnostic. The metrics map directly. Only the AST node names change.

### Architecture integration

```
┌─────────────────────────────────────────┐
│ Prepare Phase (existing)                │
│  prepare-changes.py → review-input.json │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│ NEW: Metric Extraction Phase            │
│  extract-metrics.py → metrics.json      │
│  (tree-sitter, deterministic, fast)     │
│  Per unit: methods, props, deps, casts  │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│ Review Phase (simplified)               │
│  Agent receives metrics.json + rule.md  │
│  Job: judge numbers, detect exceptions  │
│  No counting needed → faster, cheaper   │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│ Validate → Synthesize → Implement       │
│  (existing pipeline, unchanged)         │
└─────────────────────────────────────────┘
```

**Where it fits in the orchestrators:**

In `review/SKILL.md` and `refactor/SKILL.md`, add between Phase 1 (Prepare) and Phase 3 (Review):

```
## Phase 2.5: Extract Metrics (after prepare, before review)
- [ ] 2.5.1 For each file in review-input.json:
  - Run: python3 {SKILL_ROOT}/scripts/extract-metrics.py <file_path> <output_path>
  - Produces: {OUTPUT_ROOT}/{ITERATION}/metrics/{filename}.metrics.json
- [ ] 2.5.2 Pass metrics.json path to each review agent alongside review-input.json
```

The review agent's prompt changes from:
```
Analyze this code and count verbs, cohesion groups, stakeholders...
```
To:
```
Here are pre-computed metrics for this unit:
- Methods: ["save", "load", "validate", "format"] (4 verbs)
- Cohesion groups: [["save","load"] using {db}, ["validate","format"] using {formatter}] (2 groups)
- Dependencies: [Database (concrete), Formatter (concrete)] (2 sealed points)

Apply SRP rule.md severity bands to these numbers.
Is this a facade? (check: are all deps protocol-typed? are all methods pure delegation?)
```

### Honest split: what tree-sitter handles vs what stays LLM

Tree-sitter handles structural/syntactic extraction. It **cannot** do semantic analysis. SRP's core metrics (verb counting = "what responsibilities does this class have?", cohesion groups, stakeholders) are irreducibly semantic — only an LLM can judge them. Tree-sitter's value for SRP is providing better input data (method list, property-method access matrix), not replacing the LLM.

OCP and LSP metrics are mostly structural and benefit the most.

| Task | Tree-sitter? | LLM? | Notes |
|------|:------------:|:-----:|-------|
| Method names/count | **Yes** | No | Syntactic |
| Property names/types | **Yes** | No | Syntactic |
| Which properties each method accesses | **Yes** | No | AST scope tracking |
| Dependency list + concrete vs protocol | **Yes** | No | Type declaration lookup |
| `.shared`/`.default`/static access | **Yes** | No | Pattern matching |
| `as?`/`is`/`as!` count | **Yes** | No | Node matching |
| Empty method bodies / `fatalError` | **Yes** | No | Body analysis |
| Protocol method count | **Yes** | No | Syntactic |
| Init parameter types | **Yes** | No | Syntactic |
| Verb count (responsibilities) | No | **Yes** | Irreducibly semantic |
| Cohesion group identification | No | **Yes** | Needs semantic clustering (tree-sitter provides raw matrix) |
| Stakeholder count | No | **Yes** | Business context |
| "Is this a facade?" | No | **Yes** | Judgment call |
| Severity scoring | No | **Yes** | But now from deterministic inputs |

**Best ROI**: OCP metrics (sealed points, testability) and LSP metrics (type casts, empty methods) — almost fully deterministic. SRP gets better input data but still needs LLM for the hard parts.

### Benefits

1. **Deterministic counts** → same code = same numbers = reproducible severity
2. **Cheaper reviews** → agent receives data instead of doing extraction. Sonnet can handle "judge these numbers" (S-02 becomes viable)
3. **Benchmarkable** → run extract-metrics on Examples/ files, verify counts match expected values. First real ground truth.
4. **Language-agnostic** → add Kotlin by adding `tree-sitter-kotlin` grammar. Same principle rules, same extraction script, different AST nodes
5. **Faster** → tree-sitter parses in milliseconds. No agent needed for extraction.
6. **Cross-principle verification grounds in data** → synthesis can re-run extract-metrics on proposed code to VERIFY counts changed as expected (addresses the "checking its own homework" problem)

### Implementation plan

1. **`scripts/extract-metrics.py`** — Core extraction script
   - Input: file path + language
   - Output: `metrics.json` with per-unit structural data
   - Dependencies: `tree-sitter`, `tree-sitter-swift` (add to requirements.txt)

2. **`scripts/queries/`** — Per-language query files
   - `swift.scm` — Tree-sitter queries for Swift AST
   - `kotlin.scm` — Tree-sitter queries for Kotlin AST
   - Extensible: add `java.scm`, `typescript.scm` etc.

3. **Update review instructions** — Each principle's `review/instructions.md` changes from "count X" to "read the pre-computed X from metrics.json"

4. **Update prepare-review-input** — Add metrics extraction as post-step, or run from orchestrator inline via Bash (no agent needed — it's a script)

5. **Update review output schemas** — Metrics section now references the deterministic source, review agent adds judgment layer on top

6. **Benchmark suite** — Run extract-metrics on all Examples/ files, store expected output as golden files, add to test suite

### Dependencies

```
# Add to requirements.txt
tree-sitter>=0.23.0
tree-sitter-swift>=0.6.0
tree-sitter-kotlin>=0.3.0  # when Kotlin support added
```

### Relationship to other suggestions

- **Enables S-02**: With pre-computed metrics, Sonnet can handle reviews (just judgment, no counting)
- **Enables S-05**: Post-synthesis verification becomes deterministic — run extract-metrics on proposed code
- **Grounds S-09**: Oscillation detection can compare deterministic metric snapshots between iterations
- **Enables benchmarking**: First path to measuring system accuracy (ground truth from AST vs LLM output)

---

## S-32: DRY principle — full `references/DRY/` implementation

**Impact**: High | **Effort**: High | **Category**: Review quality

**Status**: Pending

No `references/DRY/` directory exists. The DRY principle needs the same full structure as SRP/OCP/LSP/ISP: rule.md, review/, fix/, refactoring.md, Examples/.

### DRY Metrics (for `rule.md`)

Follow the same quantitative pattern as other principles:

- **DRY-1: Structural duplication** — Identical or near-identical view hierarchies with the same layout primitives and spacing values appearing in more than one non-Shared file.
- **DRY-2: Semantic duplication** — Two or more components in `Shared/` with `use-when` similarity > 0.85 (measured by registry script). Should be one configurable component.
- **DRY-3: Inline shared logic** — Business logic or layout recipes in feature files instead of `Shared/` — a missing abstraction.

### Severity bands

| Condition | Severity |
|---|---|
| 0 duplicates detected | COMPLIANT |
| Similar component exists but not generic enough for new case | MINOR |
| Structural/semantic duplicate exists and was not reused | SEVERE |
| New component created without running DRY check | SEVERE |

### Exceptions (NOT violations)

- Feature-specific one-off views with no reuse potential
- Views similar but serving fundamentally different interaction models
- Components under 5 lines (too small to abstract)

### SwiftUI-specific fix hierarchy

| Problem | Solution |
|---|---|
| Repeated types/logic | Protocols + generics |
| Repeated layout structure | `@ViewBuilder` containers |
| Repeated styling/spacing | `ViewModifier` + `View` extensions |

### Files to create

1. `references/DRY/rule.md` — metrics + severity bands + exceptions
2. `references/DRY/review/instructions.md` — how the review agent applies DRY metrics
3. `references/DRY/review/output.schema.json` — follow existing schema pattern
4. `references/DRY/fix/instructions.md` — generalization strategies (ViewBuilder, ViewModifier, protocols)
5. `references/DRY/fix/output.schema.json` — follow existing schema pattern
6. `references/DRY/refactoring.md` — before/after Swift examples
7. `references/DRY/Examples/generic-list-compliant.swift`
8. `references/DRY/Examples/generic-list-violation.swift`

### Open questions

1. Should `registry.py --validate` fail on ANY missing frontmatter, or only files above a size threshold?
2. What similarity threshold triggers SEVERE vs MINOR? (Suggested: 0.85 SEVERE, 0.70 MINOR)
3. Should DRY review also scan feature files for inline duplication (DRY-3), or only check `Shared/`?

### Relationship to other suggestions

- Depends on S-33 (registry script) for DRY-2 semantic duplication detection
- S-34 (code skill modification) depends on this
- ISP (S-11) and DRY share detection logic (protocol splitting vs component splitting)

---

## S-33: Component discovery script (`scripts/find-component.py`) and validation (`scripts/registry.py`)

**Impact**: High | **Effort**: Medium | **Category**: Tooling

**Status**: Pending

No `scripts/` directory exists in the project. Two scripts are needed:

### Script 1: `scripts/find-component.py` — grep-based discovery (fast, no full scan)

Accepts keywords, greps `solid-tags` and `solid-use-when` across `Sources/`, returns matching **file paths only**. Does NOT read file contents or parse frontmatter — that's the calling agent's job.

```bash
python scripts/find-component.py "row icon toggle settings"
# 1. Splits input into keywords
# 2. Greps solid-tags: and solid-use-when: for each keyword
# 3. Ranks files by keyword hit count
# 4. Returns file paths (top N matches)
```

**Output:** JSON array of file paths, ranked by relevance:
```json
[
  "Sources/Shared/Components/GenericRow.swift",
  "Sources/Features/Settings/SettingsToggleRow.swift"
]
```

**The calling agent/skill then:**
1. Reads the matched files' frontmatter (`solid-use-when`, `solid-do-not-use-when`)
2. Checks if the intent matches what it's about to create
3. If match → reads the code to validate it satisfies the need
4. If no match or not sufficient → creates new type with frontmatter

### Script 2: `scripts/registry.py --validate` — validation only (CI/pre-commit)

```bash
python scripts/registry.py --validate
# Fails if: any Sources/ .swift file with a type declaration is missing solid- frontmatter
# Fails if: similarity score > 0.85 between any two solid-use-when fields
# Fails if: required fields are empty
```

### Frontmatter format (in Swift files)

All keys use `solid-` prefix to avoid false matches from regular comments/DocC. Multiple blocks per file supported — one per type declaration. Parser strips `// ` prefix → valid YAML block.

```swift
// ---
// solid-name: GenericRow
// solid-category: layout/row
// solid-tags: [row, icon, leading, hstack, swiftui, shared]
// solid-use-when: any row with leading icon and flexible content
// solid-do-not-use-when: grids, sectioned lists, trailing actions (use ActionRow)
// solid-props: icon: String?, leading: @ViewBuilder, trailing: @ViewBuilder?
// solid-added: 2026-01-15
// ---
struct GenericRow<Content: View>: View { ... }
```

Required fields: `solid-name`, `solid-category`, `solid-tags`, `solid-use-when`, `solid-do-not-use-when`, `solid-props` (Views and services only), `solid-added`

### Categories

- `layout/row` — HStack-based row components
- `layout/container` — wrapping/shell components
- `modifier` — ViewModifier extensions
- `service/protocol` — protocol definitions
- `service/implementation` — concrete implementations
- `service/mock` — test doubles
- `utility` — pure functions, formatters, helpers

### Synonym groups (built into `find-component.py`)

- row: cell, item, tile, entry, listRow
- icon: symbol, image, leading, badge
- container: wrapper, shell, frame, card
- loading: spinner, skeleton, placeholder, shimmer
- list: collection, feed, grid, stack

### Verified status (2026-03-12)

**Not implemented.** No top-level `scripts/` directory exists. Scripts live within individual skills (`skills/*/scripts/`). Existing `parse-frontmatter.py` parses YAML frontmatter from markdown files. `discover-principles.py` discovers principles by globbing `*/rule.md`. Neither handles Swift file frontmatter.

**Plan:** Create `scripts/find-component.py` that: (1) accepts keywords, (2) greps `solid-tags` and `solid-use-when` across `Sources/**/*.swift`, (3) ranks by hit count, (4) returns file paths only — no content reading. Create `scripts/registry.py --validate` for CI/pre-commit: checks all types have frontmatter, flags similar `solid-use-when` fields.

---

## S-42: Full automation loop — spec → code → test → commit → PR

**Impact**: High | **Effort**: High | **Category**: Pipeline automation

### Problem

Today each step is manual: pick a spec, run `/implement`, review, commit, create PR. For a project with many ready specs (e.g., an epic broken into 10+ subtasks), this is tedious and could be fully automated.

### Proposed solution

1. **`next-ready-spec` script** — a new subcommand in `build-spec-query.py` (or standalone) that finds the next implementable spec:
   - Scans all specs with `status: ready`
   - Filters to those whose `blocked-by` dependencies all have `status: done`
   - Returns the first match (by spec number, or topological order)
   - Returns empty/exit 1 if nothing is ready

2. **Automation orchestrator** — a loop skill or hook that:
   - Calls `next-ready-spec` to pick the next spec
   - Runs `/implement <spec>`
   - Runs tests (project-specific test command)
   - If tests pass: updates spec status to `done`, commits, creates PR
   - If tests fail: marks spec as `needs-attention`, moves on
   - Loops until no ready specs remain

3. **Spec status lifecycle integration** — after successful implementation + tests:
   - `update-status SPEC-NNN done` (triggers parent propagation)
   - Commit with conventional message referencing the spec number
   - PR with spec summary as description

### Design decisions (2026-03-20)

**Fresh context per subtask is mandatory.** Each `/implement` run must have zero context from previous subtasks. LLM context accumulates and degrades quality — subtask 5 shouldn't be influenced by subtask 1's code review findings.

**Cannot be a skill.** `/implement` is an orchestrator that spawns its own subagents (plan-agent, validate-plan-agent, etc.). Skills can't nest Task calls inside Task calls. A skill calling `/implement` inline would accumulate context. Hooks can't clear context either.

**Must be an external shell script.** A script that invokes `claude` CLI per subtask — each invocation is a completely fresh session. The script handles the loop, branching, status updates. Claude handles implementation.

**Stacked branches.** Each subtask branches from the previous subtask's branch, forming a chain. Later subtasks have access to code from earlier ones.

**Retry once then fail.** On first failure: `git reset --hard`, retry with fresh `claude` session. On second failure: stop the loop entirely. No skip-and-continue — partial implementations risk inconsistent state.

### Open blockers

1. **Completion detection** — no reliable way to know if `/implement` succeeded from the shell script. `claude` CLI exit code doesn't reflect whether the skill's internal phases succeeded. Options under consideration:
   - Parse `implement-log.json` after each run (fragile — timestamp in path)
   - Have `/implement` write a sentinel file on success (e.g., `.solid_coder/implement-{spec}/.success`)
   - Have `/implement` update spec status to `done` on success (then `next-ready` naturally skips it)
   - Use `claude --output-format json` if available to get structured result

   None are clean yet. This is the primary blocker.

2. **`next-ready-spec` subcommand** — `build-spec-query.py` needs a new subcommand that finds the next implementable subtask (status: ready, all blocked-by done)

3. **Spec status update from `/implement`** — currently `/implement` doesn't update spec status. Adding this would solve both completion detection and `next-ready` filtering.

### Dependencies

- `build-spec-query.py` needs `next-ready-spec` subcommand
- Completion detection mechanism (see open blockers)
- `/implement` should update spec status on success
- Test runner must be project-configurable (not every project uses `swift test`)
- PR creation needs `gh` CLI or similar

### Notes

This enables a Claude Code session to autonomously implement an entire epic: break it down with `/build-spec`, then loop through all subtasks with the automation orchestrator. Human reviews PRs, not individual code changes.

---

## S-43: Rewrite mode for `/implement` pipeline — greenfield bypass in validate-plan

**Impact**: High | **Effort**: Low | **Category**: Pipeline enhancement

**Status**: Not implemented — design decided

### Problem

When rewriting an existing component from scratch (e.g., decomposing a monolithic `IAPManager`), the `/implement` pipeline's validate-plan phase finds the very types being rewritten and classifies them as `reuse` or `adjust`. The synthesizer then emits `modify` directives when the intent is to build from scratch with a clean architecture.

### Decision: Handle in validate-plan, not the orchestrator

The implement orchestrator still calls validate-plan normally. validate-plan itself detects `mode: rewrite` and short-circuits: skip all search phases (Phase 0 synonym generation, Phase 1+2 script search, Phase 1.5 name-based search, Phase 3 match analysis), classify all components as `create` with empty `matches[]`, and output a valid `validation.json`. The orchestrator doesn't need to know about rewrite mode.

### Signal mechanism

`mode: rewrite` in spec YAML frontmatter:

```yaml
---
number: SPEC-042
mode: rewrite
---
```

The `build-spec-from-code` skill (S-44) auto-populates this field. The mode flows through: spec → arch.json (plan agent preserves frontmatter fields) → validate-plan reads it.

### Why skip validation entirely (not exclude/filter)

Considered alternatives:
1. **Exclusion list** — validate-plan ignores specific rewrite-target files but searches everything else. Rejected: in a rewrite, the new architecture has its own interfaces. Integration with the old world is a separate concern.
2. **New `replace` status** — validate-plan finds existing code but classifies as `replace` instead of `reuse`. Rejected: unnecessary complexity. The rewrite is a clean break.
3. **Skip Phase 2 in orchestrator** — orchestrator skips validate-plan entirely and generates stub validation.json. Rejected: leaks mode awareness into the orchestrator. Cleaner for validate-plan to handle it internally.

### Rewrite produces subtasks for integration

The key insight: `build-spec-from-code` (S-44) doesn't just produce a rewrite spec — it produces subtasks:

```
existing code → build-spec-from-code → spec with subtasks:
  ├── SPEC-NNN-1: rebuild component (mode: rewrite, skip validation)
  ├── SPEC-NNN-2: bridge old interface → new interface
  └── SPEC-NNN-3: migrate consumers (optional)
```

Subtask 1 runs `/implement` with `mode: rewrite` — pure greenfield. Subtask 2 runs `/implement` normally — validation finds the old types AND the newly created types, wires them via bridge/adapter pattern. This separates "build the new thing" from "integrate with the old thing."

### Implementation plan

1. **Spec frontmatter**: Add `mode` field (values: `default`, `rewrite`). Optional — absence means `default`.
2. **plan agent**: Preserve `mode` from spec frontmatter into `arch.json` (pass-through, no special behavior).
3. **validate-plan SKILL.md**: Add Phase -1 (before Phase 0): read `mode` from `arch.json`. If `mode == "rewrite"`, skip to Phase 5 and emit all-`create` validation.json.
4. **validate-plan CLAUDE.md**: Document rewrite mode behavior.
5. **No changes** to: implement orchestrator, synthesize-implementation, code agent, refactor.

### Relationship to other suggestions

- **Depends on S-44** (`build-spec-from-code`) — the skill that produces rewrite specs with subtasks
- **S-42** (full automation loop) could chain rewrite subtasks automatically

---

## S-44: `build-spec-from-code` skill — analyze existing code and produce rewrite spec

**Impact**: High | **Effort**: High | **Category**: New skill

**Status**: Not implemented — design pending

### Problem

Before rewriting a component, someone needs to analyze the existing code, understand its responsibilities, interfaces, consumers, and pain points, then produce a spec describing the desired new architecture. Today this is manual.

### Proposed skill

`/build-spec-from-code <target>` — analyzes existing code and produces a rewrite spec through user interview.

### Flow

1. **Analyze**: Read the target code. Extract types, responsibilities, interfaces, dependencies, consumers.
2. **Interview**: Ask the user what to change, what to keep, what the pain points are, what the desired architecture looks like.
3. **Produce spec**: Write a spec with `mode: rewrite` in frontmatter describing the desired new architecture.
4. **Generate subtasks**:
   - Subtask 1: Rebuild component (`mode: rewrite`) — pure greenfield implementation
   - Subtask 2: Bridge old interface → new interface (normal mode) — adapter/bridge wiring
   - Subtask 3: Migrate consumers (optional, normal mode) — update call sites

### Key design decisions

- The spec describes the **desired** architecture, not "fix the current code." It's forward-looking.
- Integration with the old world is explicitly separated into its own subtask. The rewrite itself is a clean break.
- The user interview resolves ambiguity about what to keep vs what to redesign — same pattern as `/build-spec`.
- The plan agent doesn't need rewrite-specific behavior — it decomposes whatever the spec describes.

### Open questions

- Should the analysis phase run existing `/review` to surface SOLID violations as input to the interview?
- How deep should consumer analysis go? (direct callers only, or transitive?)
- Should the bridge subtask always be generated, or only when the old interface has external consumers?