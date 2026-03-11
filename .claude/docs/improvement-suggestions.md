# Improvement Suggestions

Audit of the solid-coder plugin architecture. Each suggestion is independent and can be implemented in any order unless noted.

---

## S-01: Always-on SOLID enforcement during coding

**Impact**: High | **Effort**: Low | **Category**: New capability

**Status**: Blocked — needs design decision

The full pipeline only runs on explicit `/review` or `/refactor`. During normal coding, developers get zero SOLID guidance.

### Problem with `.claude/rules/`

Plugins **cannot distribute `.claude/rules/` files**. The plugin system is isolated by design — plugin contents do not merge into the target project's `.claude/` directory. Rules only auto-load from the actual project's `.claude/rules/`. This means:

- Plugin users would have to manually create rule files — breaks the distribution goal
- Symlinks are a workaround but fragile and not cross-platform
- Managed CLAUDE.md (system-level) requires IT/admin deployment

### Alternatives to explore

1. **Plugin `settings.json` with `agent` field**: Plugins can override the main agent behavior. Could inject SOLID awareness into the default agent's system prompt. Needs investigation — unclear if this affects all interactions or only plugin-scoped ones.

2. **Skills with auto-invocation**: Skills with a `description` field auto-invoke when Claude detects relevance (unless `disable-model-invocation: true`). A skill described as "Apply SOLID principles when writing Swift code" might auto-trigger. However, auto-invocation is unreliable — it depends on the LLM's judgment.

3. **PostToolUse hook on Write/Edit**: A plugin hook that fires after every file write, running a lightweight SOLID check. Deterministic trigger, but adds latency to every edit.

4. **Documentation-only**: Document that consumers should add `.claude/rules/` files to their projects. Provide the rule files as templates in the plugin's `references/` directory.

### Decision needed

Which approach (or combination) best balances the distribution goal with always-on enforcement? This affects whether the `/code` skill's Phase 2 (manual rule loading) can be simplified.

---

## S-02: Fix model selection for cost efficiency

**Impact**: High | **Effort**: Low | **Category**: Cost reduction

Current model assignment:

| Agent | Current Model | Task Type |
|-------|--------------|-----------|
| `principle-review-fx-agent` | Opus | Following documented checklists |
| `principle-review-agent` | Default | Following documented checklists |
| `synthesize-fixes-agent` | Opus | Deep cross-principle reasoning |
| `refactor-implement-agent` | Opus | Following a plan with code snippets |
| `code-agent` | Opus | Writing code with rules as constraints |
| `prepare-review-input-agent` | Sonnet | Diff parsing + unit detection |
| `validate-findings-agent` | Sonnet | Running Python script |
| `generate-report-agent` | Sonnet | Running Python script |

**Suggested changes**:

| Agent | Suggested Model | Rationale |
|-------|----------------|-----------|
| `principle-review-fx-agent` | **Sonnet** | Checklist execution with documented metrics — mechanical |
| `principle-review-agent` | **Sonnet** | Same reasoning |
| `synthesize-fixes-agent` | Opus (keep) | Genuine deep reasoning needed |
| `refactor-implement-agent` | **Sonnet** | Implementing from detailed plan with code snippets provided |
| `code-agent` | Opus (keep) | Needs reasoning to satisfy rules while writing |

**Estimated savings**: ~50-60% token cost reduction per run. Review agents are the most parallelized (3x), so downgrading them has outsized impact.

**Risk**: Sonnet may miss subtle violations. Mitigate by testing against the Examples/ directories for each principle.

---

## S-03: Pre-compute a rule index

**Impact**: Medium | **Effort**: Low | **Category**: Pipeline efficiency

Every run does `Glob references/**/review/instructions.md` then reads each rule.md frontmatter for activation status. This is 6+ file reads that return identical results every time.

**Suggestion**: Generate `references/index.json` at plugin install/update time:

```json
{
  "principles": {
    "SRP": { "activation": "always", "tier": "core", "patterns": ["structural/facade"] },
    "OCP": { "activation": "always", "tier": "core", "patterns": ["behavioral/strategy"] },
    "LSP": { "activation": "always", "tier": "core", "patterns": ["structural/adapter"] }
  },
  "version": "1.0.0"
}
```

One file read replaces N globs + N reads in Phase 2 (Discover Principles) of both review and refactor orchestrators.

**Maintenance**: Add a script or hook that regenerates the index when any `rule.md` changes.

**Update**: `parse-frontmatter` script now resolves paths and produces `files_to_load` per principle. A cached index would further reduce repeated script calls. Status: **Partially addressed** — caching is the remaining optimization.

---

## S-04: Short-circuit the pipeline for trivial changes

**Impact**: Medium | **Effort**: Low | **Category**: Pipeline efficiency

A 1-line typo fix triggers the full 6-phase pipeline.

### Caveat: small changes can still contain violations

A single line like `guard let x = obj as? ConcreteType` is an LSP violation (type-casting against a protocol conformer). Line count alone is not a safe proxy for "trivial." Any heuristic must account for this.

**Suggestion**: Use a two-tier gate after the prepare phase:

```
Tier 1 — Safe to skip (no false negatives):
  IF summary.changed_units == 0:
    → Skip review entirely, emit "no reviewable changes"
  IF only comments/whitespace changed (detectable from diff content):
    → Skip review entirely

Tier 2 — Run lightweight check instead of full pipeline:
  IF total changed lines < threshold (e.g., 10) AND no new types added:
    → Run a SINGLE in-context review (no agent spawning)
    → Load rules inline, check the diff directly
    → Emit findings or "clean" without the full pipeline overhead
```

Tier 2 avoids the false negative problem: small changes still get reviewed, but without spawning N parallel agents for a few lines. The orchestrator itself (which already has Opus context) checks the rules directly.

Make the threshold configurable via `--thorough` flag to force the full pipeline. Add to both review and refactor orchestrator SKILL.md files.

---

## S-05: Add post-synthesis verification script

**Impact**: High | **Effort**: Medium | **Category**: Reliability

Phase 4 of synthesize-fixes asks the LLM to simulate other principles' metrics on proposed code. This is the weakest point — the LLM is likely to rubber-stamp its own output with `"passed": true`.

**Suggestion**: Add a Python verification script (`scripts/verify-synthesis.py`) that performs concrete checks on the `suggested_fix` code in each plan action:

- **SRP proxy**: Count distinct method groups / property clusters in proposed types
- **OCP proxy**: Grep for `.shared`, `.default`, `static func`, direct `init(` of concrete types
- **LSP proxy**: Count protocol methods vs conformer implementations, detect `fatalError`/empty bodies
- **ISP proxy**: Flag protocols with 5+ methods (potential fat interface)

Run this after synthesis, before implementation. If a check fails, annotate the plan action with a warning. The implement agent can then flag it rather than blindly applying.

**Fits the architecture**: This follows the same pattern as `validate-findings.py` — a deterministic script as guardrail on LLM output.

---

## S-06: Graceful degradation for partial failures

**Impact**: Medium | **Effort**: Medium | **Category**: Reliability

Currently if one principle review agent fails, the orchestrator reports the error and the pipeline stalls. All other successful reviews are lost.

**Suggestion**: In Phase 4 (Collect Results) of both orchestrators:

```
FOR each principle review result:
  IF agent succeeded:
    → collect output normally
  IF agent failed:
    → log warning: "{principle} review failed: {error}"
    → add to warnings list
    → continue with remaining principles

IF all agents failed:
  → stop and report errors
IF some succeeded:
  → proceed with partial results
  → include "warnings" field in all downstream outputs
```

Update `validate-findings.py` and synthesis to handle missing principle data gracefully.

---

## S-07: Fix the `ruler.md` typo

**Impact**: Low | **Effort**: Trivial | **Category**: Correctness

In `skills/apply-principle-review/SKILL.md` line 25:

```
if rules are not provided use PRINCIPLE_FOLDER_ABSOLUTE_PATH/ruler.md path as fallback
```

Should be `rule.md`, not `ruler.md`. This fallback silently fails if the primary path resolution doesn't work.

---

## S-08: Standardize path template substitution

**Impact**: Medium | **Effort**: Medium | **Category**: Reliability

Three different substitution syntaxes exist:

| Pattern | Used In | Interpreted By |
|---------|---------|----------------|
| `${CLAUDE_PLUGIN_ROOT}` | SKILL.md frontmatter | Claude Code runtime |
| `PRINCIPLE_FOLDER_ABSOLUTE_PATH` | instructions.md frontmatter | LLM string replacement |
| `CURRENT_PROJECT` | Orchestrator skills | LLM interpretation |
| `{RULES_PATH}` | Skill body | LLM variable expansion |

LLM-interpreted substitution is unreliable. The LLM might forget to substitute, substitute incorrectly, or partially substitute.

**Suggestion**:
- Use `${CLAUDE_PLUGIN_ROOT}` (runtime-resolved) wherever possible
- In orchestrators, resolve ALL paths to absolute paths BEFORE passing to subagents
- Pass only concrete absolute paths in agent prompts — never template variables
- Consider using `!`command`` dynamic context injection for paths that need runtime resolution

**Update**: `parse-frontmatter` script now handles `PRINCIPLE_FOLDER_ABSOLUTE_PATH` token replacement and resolves all paths to absolute. `load-reference` strips frontmatter so agents get clean content. Skills use `!` bash calls to run these scripts. Status: **Partially addressed** — `CURRENT_PROJECT` and `{RULES_PATH}` still rely on LLM interpretation.

---

## S-09: Detect oscillation in iteration loop

**Impact**: Medium | **Effort**: Low | **Category**: Reliability

If iteration 1 fixes issue A but introduces issue B, and iteration 2 fixes B but reintroduces A-like patterns, the loop oscillates without converging.

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

---

## S-11: Prioritize ISP and DIP principles

**Impact**: High | **Effort**: High | **Category**: Review quality

With only SRP/OCP/LSP, the cross-checking matrix has gaps. Common cascade patterns:

| Fix | Undetected Cascade |
|-----|--------------------|
| SRP extraction | Creates fat interface (ISP violation) |
| SRP extraction | Injects concrete dependency (DIP violation) |
| OCP protocol creation | Protocol too wide for some conformers (ISP violation) |

The synthesis phase cross-checks against active principles only. Missing ISP/DIP means these cascades pass verification.

**Suggestion**: Implement at least lightweight versions:

- **ISP rule.md**: Metrics for protocol width (method count), conformer coverage (% methods with real implementations)
- **DIP rule.md**: Metrics for concrete vs protocol dependencies, init parameter types

Even without full review/fix/refactoring docs, having the rule.md enables cross-checking during synthesis (Phase 4 reads rule.md for metric definitions).

---

## S-12: Validate agent output against schemas deterministically

**Impact**: Medium | **Effort**: Medium | **Category**: Reliability

JSON schema validation currently happens in `validate-findings.py` but is optional (plugin-root arg can be omitted). Review agent outputs (`review-output.json`, `fix.json`) are not validated at all — the schema files exist in the references but nothing enforces them.

**Suggestion**:

1. Make plugin-root argument **required** in `validate-findings.py`. Use `--no-validate` flag for test mode
2. Add a lightweight schema validation step after each review agent completes:
   ```python
   # validate-output.py <json-file> <schema-file>
   ```
   Call this from the orchestrator in Phase 4 (Collect Results) before proceeding
3. If validation fails, treat as partial failure (see S-06) rather than silent corruption

---

## S-13: Delta-aware review — only report regressions, not pre-existing violations

**Impact**: High | **Effort**: High | **Category**: Review quality / noise reduction

### Problem

When a developer changes 1 line inside a 200-line class, the entire unit is reviewed (`has_changes == true`). Unit-level findings like "class has 3 cohesion groups" span `line_start: 10, line_end: 150` — which always overlaps the changed range. Result: pre-existing violations are reported as if the developer caused them.

`validate-findings.py` `ranges_overlap()` can't solve this because unit-level metrics are inherently unit-wide.

### Desired behavior

| Scenario | Action |
|----------|--------|
| New file (untracked) | Full review — no baseline exists |
| Modified file, new unit added | Full review of the new unit only |
| Modified file, existing unit changed | **Delta review** — only report if change made metrics worse |
| Modified file, existing unit unchanged | Skip (already works via `has_changes`) |

### Design: baseline metrics in `review-input.json`

Extend the prepare phase to capture the **base version** of modified units:

**In `prepare-changes.py`** (or the prepare agent):

1. For `source_type: branch` or `changes`, resolve the base commit (`HEAD` for changes, merge-base for branch)
2. For each file with `changed_ranges`, run `git show {base}:{filepath}` to get the base version
3. For each unit in the base version, compute its line range
4. Add a `change_type` field to each unit in the output:

```json
{
  "name": "UserManager",
  "kind": "class",
  "line_start": 10,
  "line_end": 150,
  "has_changes": true,
  "change_type": "modified",
  "base_line_start": 10,
  "base_line_end": 140
}
```

`change_type` values:
- `"new"` — unit doesn't exist in base (added in this change)
- `"modified"` — unit exists in both but has changed lines
- `"unchanged"` — unit exists in both, no changes (skip)

**In review instructions** (per-principle `instructions.md`):

Add a delta-review directive:

```
For units with change_type == "modified":
  1. Read the current version of the unit
  2. Apply metrics as normal → current_severity
  3. Read the base version (available via base_line_start..base_line_end from git show)
  4. Apply the SAME metrics to the base version → base_severity
  5. Report a finding ONLY IF current_severity > base_severity
  6. If current_severity <= base_severity, emit COMPLIANT (change didn't make it worse)

For units with change_type == "new":
  1. Apply full review — no baseline comparison
```

**In `validate-findings.py`**:

Add a `change_type`-aware filter:

```python
def should_include(finding, unit_change_type):
    if unit_change_type == "new":
        return True  # new units get full review
    if unit_change_type == "modified":
        # Only include if the finding indicates regression
        return finding.get("is_regression", True)
    return False  # unchanged units skipped
```

### Alternative: Cached baseline approach

Instead of computing base metrics at review time (which requires the LLM to review two versions), cache the last review's findings:

1. After each review, store findings in `.solid_coder/baseline/{filepath}.json`
2. On next review, load the baseline and compare finding IDs/severities
3. Only report findings that are new or worsened

**Pros**: No extra LLM cost, purely deterministic comparison
**Cons**: First run has no baseline (full review), stale cache if code changes outside the tool

### Impact on pipeline stages

| Stage | Change needed |
|-------|---------------|
| `prepare-changes.py` | Add `change_type` field, resolve base commit |
| `prepare-review-input-agent` | Pass base file content or reference to review agents |
| `review/instructions.md` (per principle) | Add delta-review directive for `modified` units |
| `validate-findings.py` | Filter by `change_type` + regression flag |
| `synthesize-fixes` | Only synthesize fixes for regression findings |
| `review-input.json` schema | Add `change_type` and `base_line_start/end` fields |

### Known pitfall: iteration loop + untracked files (S-14)

Files created by iteration 1 remain untracked. When iteration 2 runs `prepare-changes.py`, `git ls-files --others` lists them as untracked → the entire file is treated as "new" with `changed_ranges` spanning every line. Even if iteration 2 only adjusted 3 lines, the review sees the whole file. See S-14 for the fix.

### Relationship to S-04

This supersedes the S-04 "trivial change" short-circuit for modified files. With delta-aware review, a 1-line change that doesn't worsen any metric naturally produces zero findings — no short-circuit needed. S-04's Tier 1 (skip when `changed_units == 0` or comments-only) is still useful as an early exit before even running the review.

---

## S-14: Fix iteration loop baseline for created files

**Impact**: High | **Effort**: Low | **Category**: Correctness (bug)

### Problem

During the refactor iteration loop:

1. Iteration 1 implementation creates `PaymentProcessor.swift` (new file, untracked by git)
2. Iteration 2 calls `prepare-changes.py` with `source_type: "changes"`
3. `git ls-files --others` returns `PaymentProcessor.swift` as untracked
4. `prepare-changes.py` line 127-131 treats untracked files as entirely new: `changed_ranges: [{start: 1, end: line_count}]`
5. The full file gets reviewed as if every line is new

This means iteration 2 re-reviews the entire file instead of just the adjustments it made. Pre-existing patterns from iteration 1's extraction are flagged again, causing noise and potentially oscillation (S-09).

### Root cause

Git has no baseline for untracked files. `git diff` can't produce a diff for a file that was never staged or committed. The iteration loop doesn't create any intermediate commits or snapshots between iterations.

### Fix: `git add` between iterations

After implementation, stage all created and modified files. Then iteration 2's `git diff --staged` and `git diff` show only the actual changes from iteration 2.

Add to the refactor orchestrator between step 7.7 and the current 7.8 (renumber 7.8 → 7.9):

```
- [ ] 7.8 Stage implemented changes:
  - From the refactor logs collected in 7.5, collect:
    - Each log's `file` (the modified source file)
    - Each log's `files_created[]` entries
  - Run: `git add <file1> <file2> ...` with all collected paths
```

No extra file reads needed — the orchestrator already has the paths in context from step 7.5. One inline Bash call with explicit file list (no wildcards, no `git add .`).

`prepare-changes.py` already handles staged diffs correctly (line 107: `git diff --staged`). Once files are staged, iteration 2 sees only the real delta.

**Side effect**: Files remain staged if the refactor is aborted. This is acceptable — the developer would want to see what was changed anyway, and `git reset` is trivial.

---

## S-15: CRITICAL BUG — `addresses` vs `resolves` field name break

**Impact**: Critical | **Effort**: Low | **Category**: Data integrity (bug)

The finding ID threading mechanism is broken by a field rename mid-pipeline:

- Fix schemas (SRP/OCP/LSP `fix/output.schema.json`): `"addresses": ["srp-001"]`
- validate-findings preserves `addresses` correctly
- synthesize-fixes `plan.schema.json`: changes to `"resolves": ["srp-001"]`

No schema documents this mapping. The synthesizer must manually translate `addresses` → `resolves`, but nothing validates this happened correctly.

**Fix**: Either rename `addresses` → `resolves` consistently in all fix schemas, or add explicit documentation of the mapping in the synthesis skill. Prefer consistency — pick one name.

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

## S-17: Missing `tier` and `activation` fields in rule.md frontmatter

**Impact**: High | **Effort**: Low | **Category**: Correctness (missing feature)

The architecture docs describe a tier system (`core`/`practice`/`framework`) with `activation: always` vs conditional import-based activation. But none of the three rule.md files (SRP, OCP, LSP) actually contain `tier` or `activation` fields in their frontmatter.

The code skill's Phase 2 reads `activation` to decide which rules to load. The orchestrators glob for principles and assume all are active. This works by accident (all 3 are core/always), but will break when framework-tier principles are added.

**Fix**: Add to each rule.md frontmatter:
```yaml
tier: core
activation: always
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

---

## S-19: Unit context lost in validation schema

**Impact**: High | **Effort**: Low | **Category**: Data contracts

`validate-findings.py` writes `unit_name` and `unit_kind` into the output (lines 190-198), but `file-output.schema.json` doesn't define these fields. The synthesize-fixes `plan.schema.json` also lacks unit context in its actions.

This means:
- Schema validation would reject the actual output
- If schema validation is ever enforced strictly, unit context is stripped
- The synthesis agent loses information about which unit a finding belongs to

**Fix**: Add `unit_name` (string) and `unit_kind` (enum: class/struct/enum/protocol/extension) to both `file-output.schema.json` principles items and `plan.schema.json` actions.

---

## S-20: `has_changes` null handling in prepare-input

**Impact**: Medium | **Effort**: Trivial | **Category**: Data contracts | **Status**: Done

The schema allowed `has_changes: null`, but `apply-principle-review` checks `has_changes == true` — so null-valued units were silently skipped. Three fixes applied:

1. **Schema** (`output.schema.json`): Tightened `has_changes` type from `["boolean", "null"]` to `"boolean"`
2. **Prepare skill** (`prepare-review-input/SKILL.md`): Clarified step 2.1.4 — `has_changes` must always be `true` or `false`, never `null`. When `changed_ranges` is null/empty/missing → all units get `has_changes = true`
3. **Docs**: Updated `flows.md` to note null is never expected

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

---

## S-22: Missing JSON error handling in Python scripts

**Impact**: Medium | **Effort**: Low | **Category**: Robustness

`validate-findings.py` `load_json()` doesn't catch `json.JSONDecodeError`. Malformed JSON from a failed review agent causes an unhandled traceback instead of a clear error message.

Same applies to `generate-report.py`.

**Fix**: Wrap `json.load()` calls with try/except, print the file path and error, exit with code 1.

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

---

## S-24: Empty `design_patterns/creational/` directory

**Impact**: Low | **Effort**: Trivial | **Category**: Cleanup

The directory exists but is empty. No principle references it. No docs mention it.

**Fix**: Delete it, or add a `.gitkeep` with a comment if it's planned for future use.

---

## S-25: Orchestrator error handling is ambiguous

**Impact**: High | **Effort**: Medium | **Category**: Robustness

Across both orchestrators (review and refactor), error handling follows a pattern of "if the Task failed, stop and report the error" without specifying:

1. What constitutes failure (agent crash? empty output? malformed JSON?)
2. Whether partial results from parallel agents should be kept or discarded
3. How to detect that an agent partially succeeded (wrote files but returned error)

Key scenarios with no defined behavior:
- 2 of 3 principle reviews succeed, 1 fails → currently unclear (related to S-06)
- Prepare agent writes review-input.json but it's empty/malformed
- Glob returns zero matches in Phase 2 (no principles found)
- Source file deleted between prepare and review phases

**Fix**: Add explicit error handling steps:
- After each agent call, validate that expected output files exist and are valid JSON
- After parallel launches, count successes/failures and decide: all-fail = stop, partial = continue with warning
- After Phase 2, require at least 1 principle found or stop with "no principles configured" error

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

## S-27: Pre-plan target architecture before incremental refactoring

**Impact**: High | **Effort**: Medium | **Category**: Pipeline efficiency

**Origin**: IAPManager analysis — Run 5 took 5 iterations (57 min) because each fix exposed new violations. The agent never asked "what should the final architecture look like?" before starting.

### Problem

The refactor loop is **myopic**. Each iteration reviews, finds violations, fixes them, then discovers the fixes introduced new violations. Example from IAPManager Run 5:

```
Iter 1: "3 cohesion groups" → extract 2 classes
Iter 2: "extracted classes use SKPaymentQueue.default() concretely" → add protocol
Iter 3: "canMakePayments is in the wrong class now" → move it back
Iter 4: "Logger.default is sealed, constructor is internal" → add IAPLogging, makeDefault()
Iter 5: finally clean
```

Every fix was locally correct but globally unaware. A human architect would have designed the target state upfront: "InAppPurchaseManager becomes a Facade, two extracted classes behind protocols, all singletons injected." One pass, done.

### Proposal: Conditional planning phase (iteration 0)

Add a planning phase that activates **only when the initial review finds 3+ SEVERE findings across multiple principles**. That's the signal that incremental fixes will cascade.

```
Review (existing) → if complex → Plan target architecture → Apply all at once → Review → likely done
```

The planning prompt consumes the review output:

```
Given these violations:
- SRP: 3 cohesion groups (product catalog, transaction processing, price formatting)
- OCP: 8 sealed variation points (SKPaymentQueue.default, Logger.default, ...)

Design the minimal set of types, protocols, and ownership relationships
that resolves ALL violations simultaneously. Output:
- Target class list with responsibilities
- Protocol definitions needed
- Dependency injection strategy
- Where construction lives (factory/facade pattern)
```

The implementation agent then applies the full decomposition in one shot instead of incrementally discovering it.

### When NOT to plan

- Single-principle violations (1 SRP issue, no OCP) → normal loop handles in 1-2 iterations
- MINOR-only findings → no action needed
- Simple extractions (1 cohesion group to extract) → planning overhead not worth it

### Trigger heuristic

```
IF severe_findings >= 3 AND principles_with_severe >= 2:
    run planning phase
ELSE:
    run normal incremental loop
```

### Expected impact

Based on IAPManager data:
- Run 5 (no planning): 5 iterations, 57 min
- With planning: estimated 2 iterations (plan + verify), ~25 min
- Savings: ~55% time reduction for complex refactorings

### Risks

- Plan could be wrong — bad decomposition applied in one shot is harder to undo than incremental steps
- Planning requires different reasoning (architecture) than reviewing (checklist compliance) — may need a separate "architect" prompt
- Harder to validate a plan than to validate code against rules

### Mitigation

The review iteration still runs after implementation. If the plan was wrong, the normal loop catches remaining issues — worst case is back to the current behavior. Planning is additive, not replacing the safety net.

---

## S-28: Short-circuit MINOR-only findings — skip synthesis and implementation

**Impact**: Medium | **Effort**: Low | **Category**: Pipeline efficiency

**Origin**: IAPManager analysis — Runs 6/7/8 spent 37 minutes total on verification passes that produced zero code changes. Run 8 went through all 5 phases (including synthesize + implement) only to generate empty plans.

### Problem

When the review phase finds only MINOR findings, the pipeline should stop immediately. Currently:

1. Runs 6 and 7 correctly stopped after review (no validate/synthesize/implement) — **good**
2. Run 8 ran validate → synthesize → implement, producing 4 plan files with 0 actions — **waste** (~3.5 min of synthesize+implement for nothing)

The inconsistency suggests the short-circuit logic exists but isn't reliable.

### Fix: Two short-circuit points

**Point 1 — After review (in orchestrator):**

```
After Phase 3 (Collect Results):
  IF all findings are MINOR (severe_count == 0):
    → Write refactor-log.json with status: "all_compliant"
    → Skip validate, synthesize, implement phases entirely
    → Exit iteration loop
```

This is what runs 6/7 did correctly. Ensure this is deterministic, not LLM-dependent.

**Point 2 — Before launching a re-verification run:**

If the previous iteration already converged with `all_compliant` + only MINORs, a re-run of the same code will produce the same result. The orchestrator (or the user invoking `/refactor`) should recognize this and skip.

### Where to check

Investigate why Run 8 went through synthesize+implement despite only MINOR findings. Likely the short-circuit check is in the orchestrator SKILL.md as a natural language instruction, and the LLM didn't follow it consistently. Consider making it a deterministic check in the Python validation script instead.

---

## S-29: `/code` skill greenfield gap — no source files for tag matching

**Impact**: Medium | **Effort**: Low | **Category**: Correctness

**Status**: Pending

The `/code` skill Phase 2.2 assumes source files exist to scan for tag matching:

```
If `all_candidate_tags` is non-empty:
  - Scan the source files from Phase 1 for imports and code patterns that match the candidate tags
```

In greenfield scenarios (spec or inline prompt only, no existing source file), there are no source files to scan. Phase 1 only loads a spec/markdown or prompt text — not source code.

### Current behavior

The skill silently falls through — tag matching produces no matches, so only tagless (always-active) principles load. Tagged principles (e.g., SwiftUI, TCA) would be skipped even when the spec explicitly describes building a SwiftUI view.

### Proposed fix

Add a fallback chain to Phase 2.2:

1. **Source files exist** (modification mode) → scan them for tags (current behavior)
2. **No source files, spec exists** → scan the spec/prompt content against candidate tags (e.g., spec mentions "SwiftUI" → matches `swiftui` tag)
3. **No source files, no spec** → load all principles (safest default)

This mirrors how `/review` and `/refactor` don't have this problem — they always operate on existing code.

---

## Suggestion Status Tracker

| ID | Summary | Impact | Effort | Status |
|----|---------|--------|--------|--------|
| S-01 | Always-on SOLID enforcement (rules not distributable via plugin) | High | Low | Blocked — needs design decision |
| S-02 | Fix model selection (Sonnet for mechanical tasks) | High | Low | Pending |
| S-03 | Pre-compute rule index | Medium | Low | Partial — `discover-principles` script replaces manual glob+parse; caching is remaining optimization |
| S-04 | Short-circuit trivial changes (with LSP-safe tier 2) | Medium | Low | Pending |
| S-05 | Post-synthesis verification script | High | Medium | Pending |
| S-06 | Graceful degradation for partial failures | Medium | Medium | Pending |
| S-07 | Fix `ruler.md` typo | Low | Trivial | Pending |
| S-08 | Standardize path template substitution | Medium | Medium | Partial |
| S-09 | Detect oscillation in iteration loop | Medium | Low | Pending |
| S-10 | Output cleanup mechanism | Low | Low | Pending |
| S-11 | Prioritize ISP and DIP principles | High | High | Pending |
| S-12 | Schema validation for all agent outputs | Medium | Medium | Pending |
| S-13 | Delta-aware review — only report regressions | High | High | Pending |
| S-14 | Fix iteration loop: `git add` between iterations | High | Low | Done |
| S-15 | **CRITICAL**: `addresses` vs `resolves` field name break | Critical | Low | Pending |
| S-16 | **CRITICAL**: validate-findings passes unknown files | Critical | Low | Pending |
| S-17 | Missing `tier`/`activation` in rule.md frontmatter | High | Low | Done — replaced with tag-based activation via `discover-principles` skill. No tags = always active. |
| S-18 | `file_path` vs `file` field inconsistency | High | Medium | Pending |
| S-19 | Unit context lost in validation/synthesis schemas | High | Low | Pending |
| S-20 | Missing `has_changes` in prepare-input schema | Medium | Trivial | Done — field exists in schema; tightened type from `["boolean", "null"]` to `"boolean"` and clarified prepare-input must never emit null |
| S-21 | No tests for `prepare-changes.py` | High | Medium | Pending |
| S-22 | Missing JSON error handling in Python scripts | Medium | Low | Pending |
| S-23 | README.md rewrite | Medium | Low | Pending |
| S-24 | Empty `design_patterns/creational/` directory | Low | Trivial | Pending |
| S-25 | Orchestrator error handling is ambiguous | High | Medium | Pending |
| S-26 | AST-based metric extraction (tree-sitter) | High | High | POC needed — validate on Examples/ first |
| S-27 | Pre-plan target architecture before incremental refactoring | High | Medium | Pending |
| S-28 | Short-circuit MINOR-only findings — skip synthesis/implement | Medium | Low | Pending |
| S-29 | `/code` greenfield gap — no source files for tag matching | Medium | Low | Pending |