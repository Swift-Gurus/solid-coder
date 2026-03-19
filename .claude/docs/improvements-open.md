# Open Improvement Suggestions

Suggestions that have not been implemented, need investigation, need POC validation, or are planned for the future.

---

## S-05: Add post-synthesis verification script

**Impact**: Medium | **Effort**: Medium | **Category**: Reliability

**Status**: Deferred — scalability concern, iterative re-review is preferred

Phase 4 of synthesize-fixes asks the LLM to simulate other principles' metrics on proposed code. This is the weakest point — the LLM is likely to rubber-stamp its own output with `"passed": true`.

### Why deferred

Per-principle verification scripts don't scale. Each new rule (DIP, DRY, etc.) requires its own script with custom proxy checks (grep patterns, count heuristics) that are brittle and produce false positives/negatives. Maintenance burden grows linearly with rule count.

The iterative re-review approach (S-04) is the scalable alternative — after implementation, the same review agents re-check the changed files against all principles. This is principle-agnostic and reuses existing infrastructure rather than adding parallel validation scripts.

---

## S-09: Detect oscillation in iteration loop

**Impact**: Medium | **Effort**: Low | **Category**: Reliability

**Status**: Not implemented — low practical risk

If iteration 1 fixes issue A but introduces issue B, and iteration 2 fixes B but reintroduces A-like patterns, the loop oscillates without converging. In practice, the pipeline follows patterns properly and oscillation hasn't been observed. The real risk is when a fix modifies a caller site, which then gets re-reviewed in the next iteration and flagged for unrelated violations — this is more of a scoping problem (S-04) than oscillation.

**Suggestion**: In Phase 8 (Iteration Loop), before re-reviewing:

1. Compare finding IDs from iteration N vs iteration N-1. If >50% overlap → flag oscillation
2. Diff the source files against their pre-iteration-1 state. If net change is small (<10 lines divergence from original) → the iterations are undoing each other
3. If oscillation detected → stop, report both iterations' findings, let the developer decide

Also: log per-iteration finding IDs in the refactor-log.json so oscillation is visible in the output.

---

## S-10: Add output cleanup mechanism

**Impact**: Low | **Effort**: Low | **Category**: Maintenance

`.solid_coder/` grows with every run. Timestamped directories accumulate without bounds.

**Suggestion**: Options (pick one or combine):

- **SessionStart hook**: On plugin load, delete runs older than 7 days
- **Prune at start of run**: Before creating a new output directory, delete all but the last 3 runs
- **`/clean` skill**: Manual cleanup command that lists runs with sizes and deletes selected ones
- **`.gitignore`**: At minimum, ensure `.solid_coder/` is gitignored (check if it is)

### Verified status (2026-03-12)

**Not implemented.** No cleanup step exists in either orchestrator. The project `.gitignore` does NOT include `.solid_coder/` or `.solid-coder-*`, so output directories would be tracked by git in user projects.

**Plan:**
1. Document that users should add `.solid_coder/` to `.gitignore`
2. Add a `/clean` skill that lists timestamped runs with sizes and allows selective deletion
3. Optionally add `--keep N` flag to orchestrators

---

## S-16: CRITICAL BUG — validate-findings.py passes findings for unknown files

**Impact**: Critical | **Effort**: Low | **Category**: Correctness (bug)

In `validate-findings.py` line 253-260:

```python
cr = changed_lookup.get(file_path)
if cr is None or cr is True:
    passing.append(finding)  # BUG: treats "not in lookup" same as "null ranges"
```

`changed_lookup.get(file_path)` returns `None` for BOTH:
1. File has `null` changed_ranges (entire file is new) — correct to pass
2. File not in review-input at all — should be REJECTED

If a review agent reports findings in a file that wasn't in the review-input (hallucination or path mismatch), those findings pass through unfiltered.

**Fix**: Distinguish the two cases:
```python
if file_path not in changed_lookup:
    continue  # file not in review-input, reject
cr = changed_lookup[file_path]
if cr is None or cr is True:
    passing.append(finding)  # null = entire file new
```

---

## S-18: `file_path` vs `file` inconsistency across schemas

**Impact**: High | **Effort**: Medium | **Category**: Data contracts

- `prepare-review-input/output.schema.json`: uses `"file_path"`
- `SRP/review/output.schema.json`: uses `"file"`
- `validate-findings/file-output.schema.json`: uses `"file"`
- `synthesize-fixes/plan.schema.json`: uses `"file"`

The prepare agent writes `file_path`, the review agent reads it and outputs `file`. This works because the LLM adapts, but it's a latent bug — a stricter schema validator or a different LLM might fail.

**Fix**: Standardize on one name (`file_path` is more explicit). Update all schemas and all skills that reference the field.

### Verified status (2026-03-12)

**Not implemented — inconsistency confirmed.** Full inventory:

**Uses `file_path`:** `prepare-review-input/output.schema.json` (line 23), `prepare-changes.py` (line 150)

**Uses `file`:** All 5 review schemas (SRP, OCP, LSP, ISP, SwiftUI), all 5 fix schemas, `validate-findings/file-output.schema.json` (line 8), `synthesize-fixes/plan.schema.json` (line 8)

**Bridge code:** `validate-findings.py` reads `file_path` from review-input (line 103) and `file` from review output (line 162), outputs `file` (line 233). Works because the Python script manually maps between conventions.

**Plan:** Standardize on `file_path` everywhere (more descriptive). Update all 13 schema files + Python scripts.

---

## S-21: No tests for `prepare-changes.py`

**Impact**: High | **Effort**: Medium | **Category**: Test coverage

`validate-findings.py` has 28 tests. `generate-report.py` has 24 tests. `prepare-changes.py` has **zero**. It's the entry point for all diff parsing — the most critical deterministic script.

Missing test scenarios:
- Empty git repo
- No changes (clean tree)
- Staged vs unstaged vs untracked
- Renamed files
- Binary files
- Files with special characters in names
- Hunk regex edge cases

### Verified status (2026-03-12)

**Not implemented — confirmed.** No test file exists for `prepare-changes.py`. Six other scripts DO have tests: `discover-principles`, `generate-report`, `load-reference`, `parse-frontmatter`, `check-severity`, `validate-findings`.

**Plan:** Create `skills/prepare-review-input/scripts/tests/test_prepare_changes.py` following existing test pattern. Key test cases: `parse_diff()` with various unified diff formats, `_coalesce()` with adjacent/non-adjacent ranges, `extract_imports()` with Swift imports, end-to-end `build_output()` (mock git commands), edge cases (empty diff, binary files, renamed files).

---

## S-22: Missing JSON error handling in Python scripts

**Impact**: Medium | **Effort**: Low | **Category**: Robustness

`validate-findings.py` `load_json()` doesn't catch `json.JSONDecodeError`. Malformed JSON from a failed review agent causes an unhandled traceback instead of a clear error message.

Same applies to `generate-report.py`.

**Fix**: Wrap `json.load()` calls with try/except, print the file path and error, exit with code 1.

### Verified status (2026-03-12)

**Not implemented.** Four scripts have bare `json.load()`/`json.loads()` with no error handling:
1. `skills/validate-findings/scripts/validate-findings.py` — `load_json()` at line 35-37
2. `skills/validate-findings/scripts/check-severity.py` — line 44
3. `skills/generate-report/scripts/generate-report.py` — line 211
4. `skills/discover-principles/scripts/discover-principles.py` — line 195

Malformed JSON produces unhandled `json.JSONDecodeError` traceback instead of clean error.

**Plan:** Add try/except `json.JSONDecodeError` to each, print file path + error, `sys.exit(1)`.

---

## S-23: README.md is 2 lines with a typo

**Impact**: Medium | **Effort**: Low | **Category**: Documentation

Current README:
```
# solid-coder
Claude Code plugging that contains convenient skills/workflows for Reviewing/refactoring/coding using solid principles
```

- "plugging" → "plugin"
- Doesn't list the 3 user-facing skills (`/review`, `/refactor`, `/code`)
- Doesn't mention the 3 implemented principles (SRP, OCP, LSP)
- Doesn't describe the pipeline architecture or how to install

**Fix**: Rewrite README to cover: what it does, how to install, how to use, what principles are implemented.

### Verified status (2026-03-12)

**Not implemented.** README is still 2 lines with "plugging" typo. No install, usage, skills listing, or architecture overview.

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

## S-30: SwiftUI SUI-2 (state width) and SUI-3 (responsibility mixing) — validate SOLID coverage

**Impact**: Medium | **Effort**: Medium | **Category**: Metric design | **Status**: Validate

SwiftUI rule was initially designed with three metrics: SUI-1 (body complexity), SUI-2 (state width/cohesion), and SUI-3 (responsibility mixing). SUI-2 and SUI-3 were removed because they overlap with SRP (cohesion groups, verb count) and OCP (sealed points).

**Hypothesis:** SRP and OCP will catch state proliferation and mixed responsibilities in SwiftUI views.

**Risk:** SRP's cohesion analysis works on method-variable relationships. In a SwiftUI view, all `@State` properties feed into `body` (one computed property), so SRP may see 1 cohesion group even when state properties serve 3 unrelated concerns. If SRP consistently misses this, SUI-2 should be re-added.

**Validation plan:**
1. Run SRP on 3-5 SwiftUI views with known state proliferation (8+ state props, 2+ concerns)
2. Run SRP on 3-5 SwiftUI views with inline business logic (formatting, data fetching)
3. Run OCP on views with `APIClient.shared` or singleton usage
4. If SRP/OCP flag >= 80% of cases correctly → keep SUI-1 only
5. If SRP/OCP miss > 50% → re-add SUI-2 and/or SUI-3

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

## S-35: Pre-commit hook for frontmatter validation

**Impact**: Medium | **Effort**: Low | **Category**: Enforcement

**Status**: Pending — depends on S-33

Create `scripts/hooks/pre-commit` that runs `python scripts/registry.py --validate`. Blocks commits if any `Shared/` file is missing frontmatter. Three enforcement gates:

1. **Gate 1 — CC skill** (creation time) — DRY check + frontmatter prefill in `/code` skill
2. **Gate 2 — Pre-commit hook** (human-created files) — blocks commit
3. **Gate 3 — PR check** (CI) — same script, nothing merges without it

---

## S-37: Style rules separate pipeline — review-only, no fix generation

**Impact**: Medium | **Effort**: Medium | **Category**: Architecture

**Status**: Pending

Naming conventions, function smells, general code style do not fit the existing rule mechanics. No deterministic fix, no cross-principle synthesis. Feeding them into synthesize adds noise.

### Proposed structure

```
references/style/
  naming-conventions/
    rule.md              ← metrics + severity (MINOR only)
    review/
      instructions.md
      output.schema.json
    # NO fix/ folder — absence is the signal
    # NO refactoring.md
```

### Frontmatter flag

```yaml
---
name: naming-conventions
tier: style
severity-max: minor
synthesize: false    # explicit signal — skip fix generation
---
```

### Separate output contract

```json
{
  "solid_findings": [...],    // → synthesize → implement pipeline
  "style_findings": [...]     // → report only, no fix generation
}
```

`generate-report-agent` renders style findings as a separate section — observations, not actionable violations.

### Future style rules (planned)

- Naming conventions
- Function length / smells
- SwiftUI-specific style
- Concurrency patterns
- GCD usage guidelines

### Verified status (2026-03-12)

**Not implemented.** No concept of review-only rules exists anywhere:
- No `rule.md` frontmatter has `synthesize: false`, `fix: false`, or `review-only: true`
- `discover-principles.py` doesn't parse any such field
- `synthesize-fixes/SKILL.md` processes ALL non-COMPLIANT principles — no exclusion
- `generate-report.py` treats all findings uniformly — no fixable vs report-only distinction

**Plan:**
1. Add `fixable: false` (or `synthesize: false`) field to `rule.md` frontmatter for style rules
2. Update `discover-principles.py` to expose this field
3. In `synthesize-fixes/SKILL.md` Phase 1.4, exclude non-fixable principles
4. In `generate-report/SKILL.md`, render non-fixable findings as separate "observations" section
5. In `refactor/SKILL.md` Phase 4.6, only count fixable findings for `MINOR_ONLY` vs `HAS_SEVERE`

---

## S-39: Skip empty plans — don't synthesize or implement when no changes needed

**Impact**: Medium | **Effort**: Low | **Category**: Pipeline efficiency

### Problem

The synthesizer writes plan files for every reviewed file, even when there are no actionable findings. The refactor orchestrator (Phase 7) then spawns implement agents for these empty plans, wasting agent invocations.

### Fix

Two levels:

1. **Synthesizer**: Do not write a `.plan.json` file if there are zero suggestions or zero `to_do` items for a file. No file = no implement agent spawned.
2. **Orchestrator fallback**: Before spawning an implement agent, check if the plan has any actions. Skip if empty.

Level 1 is preferred — it's cleaner to not produce empty artifacts than to filter them downstream.

---

## S-40: `solid-spec` frontmatter field — link types to requirement specs

**Impact**: Medium | **Effort**: Low | **Category**: Future

**Status**: Future — validate current 4 fields first, add when spec workflow exists

---

## S-41: Local MCP server for `references/` — language-scoped principle loading

**Impact**: Medium | **Effort**: Medium | **Category**: Architecture

**Status**: Not implemented — would replace file-based `load-reference` with stdio MCP server; enables language namespacing (`principle://swift/SRP/rule`), server-side tag filtering, and partial section loading without reading whole files

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

### Dependencies

- `build-spec-query.py` needs `next-ready-spec` subcommand
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

---

## Open Suggestion Status Tracker

| ID | Summary | Impact | Effort | Status | Verified |
|----|---------|--------|--------|--------|----------|
| S-05 | Post-synthesis verification script | High | Medium | Not implemented — synthesis cross-check is LLM mental exercise, not automated | 2026-03-12 |
| S-09 | Detect oscillation in iteration loop | Medium | Low | Not implemented — only hard MAX_ITERATIONS cap, no cross-iteration comparison | 2026-03-12 |
| S-10 | Output cleanup mechanism | Low | Low | Not implemented — no cleanup, `.solid_coder/` not gitignored | 2026-03-12 |
| S-16 | **CRITICAL**: validate-findings passes unknown files | Critical | Low | Not implemented — `_filter_findings()` line 253 treats unknown files as "entire file new" | 2026-03-12 |
| S-18 | `file_path` vs `file` field inconsistency | High | Medium | Not implemented — `prepare-review-input` uses `file_path`, all 13 other schemas use `file` | 2026-03-12 |
| S-21 | No tests for `prepare-changes.py` | High | Medium | Not implemented — 6 other scripts have tests, this one has zero | 2026-03-12 |
| S-22 | Missing JSON error handling in Python scripts | Medium | Low | Not implemented — 4 scripts have bare json.load() with no error handling | 2026-03-12 |
| S-23 | README.md rewrite | Medium | Low | Not implemented — still 2 lines with typo | 2026-03-12 |
| S-26 | AST-based metric extraction (tree-sitter) | High | High | POC needed — validate on Examples/ first | — |
| S-30 | SwiftUI SUI-2/SUI-3 — validate SOLID coverage | Medium | Medium | Validate — needs testing | — |
| S-32 | DRY principle — full `references/DRY/` implementation | High | High | Not implemented — no `references/DRY/` directory | 2026-03-12 |
| S-33 | Grep-based discovery (`find-component.py`) + validation (`registry.py --validate`) | High | Medium | Not implemented — no `scripts/` directory exists | 2026-03-13 |
| S-35 | Pre-commit hook for frontmatter validation | Medium | Low | Not implemented — depends on S-33 | — |
| S-37 | Style rules separate pipeline | Medium | Medium | Not implemented — no mechanism for review-only rules | 2026-03-12 |
| S-39 | Skip empty plans — don't synthesize or implement when no changes needed | Medium | Low | Not implemented | — |
| S-40 | `solid-spec` frontmatter field — link types to requirement specs | Medium | Low | Future — validate current 4 fields first, add when spec workflow exists | — |
| S-41 | Local MCP server for `references/` — language-scoped principle loading | Medium | Medium | Not implemented — would replace file-based `load-reference` with stdio MCP server | — |
| S-42 | Full automation loop: spec → code → test → commit → PR | High | High | Not implemented — needs `next-ready-spec` script and orchestrator loop | — |
| S-43 | Rewrite mode — greenfield bypass in validate-plan | High | Low | Not implemented — design decided, depends on S-44 | 2026-03-19 |
| S-44 | `build-spec-from-code` skill — analyze existing code, produce rewrite spec with subtasks | High | High | Not implemented — design pending | 2026-03-19 |
