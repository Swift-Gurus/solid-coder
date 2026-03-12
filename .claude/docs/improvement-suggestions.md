# Improvement Suggestions

Audit of the solid-coder plugin architecture. Each suggestion is independent and can be implemented in any order unless noted.

---

## S-01: Always-on SOLID enforcement during coding

**Impact**: High | **Effort**: Low | **Category**: New capability

**Status**: Resolved by design

The full pipeline only runs on explicit `/review` or `/refactor`. During normal coding, developers get zero SOLID guidance.

### Resolution

A dedicated `/implement` skill will be the SOLID-enforced coding entry point. The skill prompt itself loads SOLID references and enforces principles during execution — no need to distribute `.claude/rules/` files, rely on auto-invocation heuristics, or add hooks. `/code` can reference `/implement` internally.

This sidesteps all previously considered alternatives (rules distribution, hooks, auto-invocation, documentation-only) because the skill-based workflow **is** the enforcement mechanism — deterministic, every invocation.

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

### Verified status (2026-03-12)

**Partially implemented.** Actual current model assignments differ from original doc:

| Agent | Actual Model | Notes |
|-------|-------------|-------|
| `principle-review-agent` | `sonnet` | Review-only in refactor pipeline — already downgraded |
| `principle-review-fx-agent` | `opus` | Review + fix in review pipeline — bundles two tasks |
| `prepare-review-input-agent` | `haiku` | Cheaper than suggested sonnet |
| `validate-findings-agent` | `haiku` | Cheaper than suggested sonnet |
| `generate-report-agent` | `haiku` | Cheaper than suggested sonnet |
| `synthesize-fixes-agent` | `opus` | Correct — needs deep reasoning |
| `refactor-implement-agent` | `opus` | Could potentially be sonnet |
| `code-agent` | `opus` | Correct — needs reasoning |

**Remaining optimization:** `principle-review-fx-agent` uses opus because it bundles review + fix suggestions. Could split into sonnet review + separate opus fix-suggest for savings.

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

## S-04: Scope review to what was actually changed

**Impact**: Medium | **Effort**: Low | **Category**: Pipeline efficiency

**Status**: In progress — iteration-level scoping being tested

### Problem

The pipeline reviews entire files/classes even when only a small part was modified. If we updated a caller site, the caller itself shouldn't be reviewed — only the changed code and what it directly affects. Detecting "trivial" changes by line count is unreliable (a single line can be an LSP violation), so that's not the right heuristic.

### Three levels of scoping

**1. Iteration scoping (in progress)**: During refactor iterations, only re-review files that were modified in the previous round — skip files that passed and weren't touched.

**2. Target vs dependent scoping (needed)**: When re-reviewing after implementation, distinguish between:
- **Review candidates**: files that are plan targets OR were **created** during implementation (new types, protocols, extracted classes)
- **Skip**: files that already existed before the refactor, weren't in any plan, but got modified as a side effect (e.g., call site updates in class N)

The refactor logs have this data: plan `file` fields = targets, `files_created[]` = new files, everything else modified = dependents.

**Implementation**: This filtering belongs in `prepare-review-input`, not the orchestrator. When `source_type: "files"`, the prepare agent should receive metadata about which files are targets/created vs dependents, and exclude dependents from `review-input.json`.

**Gap**: The plan JSON has a `file` field (target) — that's real. But `files_created[]` in the refactor log is assumed by the orchestrator (step 7.8) without being enforced — the `/code` skill only lists files as a text summary (Phase 5), not structured JSON. To make this filtering work, either:
- The `/code` skill needs structured output with `files_created[]` and `files_modified[]`
- Or the orchestrator derives it from git (diff before/after each implement agent run)

**3. Change-boundary scoping (future)**: Even on first pass, scope the review to the changed units (functions, types) rather than the whole file. If a diff only touches a call site, don't review the caller's class for SOLID violations unrelated to the change.

---

## S-05: Add post-synthesis verification script

**Impact**: Medium | **Effort**: Medium | **Category**: Reliability

**Status**: Deferred — scalability concern, iterative re-review is preferred

Phase 4 of synthesize-fixes asks the LLM to simulate other principles' metrics on proposed code. This is the weakest point — the LLM is likely to rubber-stamp its own output with `"passed": true`.

### Why deferred

Per-principle verification scripts don't scale. Each new rule (DIP, DRY, etc.) requires its own script with custom proxy checks (grep patterns, count heuristics) that are brittle and produce false positives/negatives. Maintenance burden grows linearly with rule count.

The iterative re-review approach (S-04) is the scalable alternative — after implementation, the same review agents re-check the changed files against all principles. This is principle-agnostic and reuses existing infrastructure rather than adding parallel validation scripts.

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

### Verified status (2026-03-12)

**Already fixed.** No `ruler.md` references remain anywhere in the codebase. `skills/apply-principle-review/SKILL.md` line 25 correctly reads `rule.md`.

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

### Verified status (2026-03-12)

**ISP: Implemented.** `references/ISP/` has the full structure matching SRP/OCP/LSP: `rule.md` (ISP-1, ISP-2, ISP-3 metrics), `review/instructions.md`, `review/output.schema.json`, `fix/instructions.md`, `fix/output.schema.json`, `refactoring.md`, and `Examples/` with 4 Swift files.

**DIP: Not implemented.** `references/DIP/` does not exist.

**Plan for DIP:** Create `references/DIP/` with full structure:
- `rule.md` — DIP metrics (dependency direction, abstraction layer analysis, concrete vs protocol deps, init parameter types)
- `review/instructions.md` + `output.schema.json` — detection phases per SRP/OCP/LSP/ISP pattern
- `fix/instructions.md` + `output.schema.json` — fix strategies for DIP violations
- `refactoring.md` — before/after patterns
- `Examples/` — compliant and violation Swift files

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

### Verified status (2026-03-12)

**Partially implemented.** `validate-findings.py` does validate when `plugin_root` is provided (lines 95-96, 122-130). It validates review-input, review-output, and fix.json against their schemas. Uses `jsonschema` library with graceful fallback (warns if not installed).

**Gaps:**
- Synthesize-fixes output (`plan.json`) is never validated against `plan.schema.json`
- If `jsonschema` isn't installed, validation silently skips (just stderr warning)
- No validation of review agent outputs *before* they reach validate-findings

**Plan:**
- Add `jsonschema` to `requirements.txt` as hard dependency
- Add schema validation for synthesize-fixes plan output
- Make jsonschema a hard requirement (fail if not installed)

---

## S-13: Delta-aware review — only report regressions, not pre-existing violations

**Impact**: High | **Effort**: High | **Category**: Review quality / noise reduction

**Status**: Deferred — likely unnecessary with `/implement` workflow

If `/implement` follows SOLID guidelines from the start and doesn't repeat itself, the code it produces should be clean by construction. Delta-aware review (comparing base vs modified) is only needed when reviewing *human-written* code that may have pre-existing violations. For the `/implement` workflow, the skill controls the entire output — pre-existing violations don't apply. This remains relevant only for `/review` on legacy codebases.

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

### Verified status (2026-03-12)

**Partially implemented.** Three layers of delta-awareness exist:
1. `prepare-changes.py` produces per-file `changed_ranges` arrays ✓
2. `apply-principle-review/SKILL.md` Phase 2 skips units where `has_changes == false` ✓
3. `validate-findings.py` `_filter_findings()` rejects findings whose line ranges don't overlap changed ranges ✓

**Gap:** Review agents analyze the **entire unit** — they report ALL violations within a changed unit, including pre-existing ones. Post-filtering catches findings outside changed ranges, but pre-existing violations whose line ranges overlap changed regions still pass through. No baseline mechanism to distinguish "new violation" from "pre-existing violation in changed region."

None of the review instructions (`references/*/review/instructions.md`) mention delta, regression, or `has_changes`.

---

## S-14: Fix iteration loop baseline for created files

**Impact**: High | **Effort**: Low | **Category**: Correctness (bug)

**Status**: Not applicable — iterations use `"files"` mode, not `"changes"`

The iteration loop (Phase 8.2) uses `input: "files" {CHANGED_FILES}`, which sends full file paths to the prepare agent — not git diffs. The `git add` at step 7.8 is for hygiene, not for enabling delta review. Since `source_type: "files"` reviews whole files without consulting git baselines, the untracked-file bug described below doesn't occur. The downside (whole-file review flagging pre-existing violations) is covered by S-13.

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

### Verified status (2026-03-12)

**Not a real bug — reclassify as non-issue.** Investigation found that `addresses` and `resolves` are used at **different pipeline stages** intentionally:
- `addresses` is in per-principle fix suggestions (`fix/output.schema.json`) — consumed by `validate-findings.py`
- `resolves` is in the synthesized fix plan (`plan.schema.json`) — produced by `synthesize-fixes` after consuming validate-findings output

These are separate data structures at different stages. The synthesizer reads **findings** (not suggestions) and produces its own `resolves` field for action items. The field names represent different concepts. No mapping is needed.

**Minor note:** SwiftUI `fix/output.schema.json` has structural differences from the SOLID fix schemas (nests under `files[].suggestions[]` with `suggestion_id` instead of `id`) — this is a schema consistency issue, not the `addresses`/`resolves` bug.

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

### Verified status (2026-03-12)

**Not implemented — inconsistency confirmed.** Full inventory:

**Uses `file_path`:** `prepare-review-input/output.schema.json` (line 23), `prepare-changes.py` (line 150)

**Uses `file`:** All 5 review schemas (SRP, OCP, LSP, ISP, SwiftUI), all 5 fix schemas, `validate-findings/file-output.schema.json` (line 8), `synthesize-fixes/plan.schema.json` (line 8)

**Bridge code:** `validate-findings.py` reads `file_path` from review-input (line 103) and `file` from review output (line 162), outputs `file` (line 233). Works because the Python script manually maps between conventions.

**Plan:** Standardize on `file_path` everywhere (more descriptive). Update all 13 schema files + Python scripts.

---

## S-19: Unit context lost in validation schema

**Impact**: High | **Effort**: Low | **Category**: Data contracts

`validate-findings.py` writes `unit_name` and `unit_kind` into the output (lines 190-198), but `file-output.schema.json` doesn't define these fields. The synthesize-fixes `plan.schema.json` also lacks unit context in its actions.

This means:
- Schema validation would reject the actual output
- If schema validation is ever enforced strictly, unit context is stripped
- The synthesis agent loses information about which unit a finding belongs to

**Fix**: Add `unit_name` (string) and `unit_kind` (enum: class/struct/enum/protocol/extension) to both `file-output.schema.json` principles items and `plan.schema.json` actions.

### Verified status (2026-03-12)

**Implemented.** Unit context IS preserved through the full pipeline:
1. `prepare-review-input` outputs `files[].units[]` with `name`, `kind`, `line_start`, `line_end`, `has_changes`
2. Review agents output `files[].units[]` with `unit_name`, `unit_kind` + findings
3. `validate-findings.py` (lines 166-198) preserves `unit_name`/`unit_kind` into by-file output
4. `file-output.schema.json` (lines 31-36) includes these fields
5. `synthesize-fixes/SKILL.md` (step 3.1) groups findings by unit

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

## S-24: Empty `design_patterns/creational/` directory

**Impact**: Low | **Effort**: Trivial | **Category**: Cleanup

The directory exists but is empty. No principle references it. No docs mention it.

**Fix**: Delete it, or add a `.gitkeep` with a comment if it's planned for future use.

### Verified status (2026-03-12)

**Confirmed still empty.** `references/design_patterns/behavioral/` has `strategy.md`, `structural/` has `adapter.md`, `decorator.md`, `facade.md`. `creational/` exists with zero files.

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

### Verified status (2026-03-12)

**Partially implemented.** Explicit error handling exists for `prepare-review-input` failures (Phase 2.3 in both orchestrators: "If the Task failed, stop and report the error"). Refactor pipeline handles all-compliant (Phase 4.5) and all-skipped (Phase 7.6).

**Gaps — no defined behavior for:**
- Parallel review agent failures: "wait for all to complete" with no partial failure handling
- Synthesis failure in refactor pipeline
- Implementation agent failures
- What constitutes "failure" (crash? empty output? malformed JSON?)

**Plan:** Add explicit clauses to each Task-launching phase:
- Parallel agents: "If any Task fails, collect successful results and report which failed with error messages. Continue with available results if ≥1 succeeded."
- Synthesis: "If Task fails, write diagnostic log and stop"
- Implementation: "If any Task fails, report failure but don't roll back successful implementations"

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

### Verified status (2026-03-12)

**Partially implemented.** `synthesize-fixes/SKILL.md` acts as per-file architecture planning — reads all findings, drafts fixes in dependency order (OCP → LSP → ISP → SRP), cross-checks against other principles, and produces ordered plans. This is architecturally aware.

**Gap:** Planning happens at the **per-file** level, not system/module level. No cross-file architectural vision — doesn't consider how changes to file A affect file B, doesn't plan shared types/protocols across files, each file gets an independent plan.

**Plan:** Add "Phase 0: Architecture Vision" to `synthesize-fixes/SKILL.md` that reads all per-file findings together, identifies cross-file dependencies, produces a global type map before per-file planning.

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

### Verified status (2026-03-12)

**Implemented.** `skills/code/SKILL.md` Phase 2, step 2.2 (line 34) explicitly says: "NOTE: If Phase 1 loaded no source files (greenfield — spec or prompt only), skip tag scanning and use all principles from step 2.1."

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

## S-31: SwiftUI "dumb view" rule — views must not contain business logic

**Impact**: High | **Effort**: Low | **Category**: Metric design | **Status**: Validate

Core principle: SwiftUI views should be dumb — they represent state, nothing more. Business logic (fetching, sorting, filtering, validation, computation) belongs in a ViewModel or domain layer, not in the View struct.

**The gap:** A view with a single `fetchData()` method still has 1 verb by SRP metrics → COMPLIANT. SRP doesn't distinguish between "renders" (acceptable view verb) and "fetches" (unacceptable view verb). The issue is not verb *count* but verb *type* relative to the unit's architectural role.

**Options:**
1. Add as SUI-2 (SwiftUI-specific) — "Non-view logic count" metric, any data/business method in a View struct → SEVERE
2. Extend SRP with a View-aware rule — when unit conforms to `View`, any non-view verb escalates severity
3. Keep as a general convention without metric enforcement

Depends on S-30 validation results.

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

## S-33: Component registry script (`scripts/registry.py`)

**Impact**: High | **Effort**: Medium | **Category**: Tooling

**Status**: Pending

No `scripts/` directory exists in the project. The registry script is the foundation for DRY enforcement — it scans Swift files in `Sources/Shared/` for YAML frontmatter comments and returns structured JSON.

### Frontmatter format (in Swift files)

```swift
// ---
// name: GenericRow
// category: layout/row
// description: HStack with configurable leading icon and content slots
// use-when: any row needing a leading icon with flexible content
// do-not-use-when: grids, sectioned lists, rows with trailing actions (use ActionRow)
// props: icon: String?, leading: @ViewBuilder, trailing: @ViewBuilder?
// added: 2026-01-15
// ---
```

Required fields: `name`, `category`, `description`, `use-when`, `do-not-use-when`, `props`, `added`

Categories: `layout/row`, `layout/container`, `modifier`, `service`, `utility`

### Output format

```json
[
  {
    "name": "GenericRow",
    "file": "Sources/Shared/Components/GenericRow.swift",
    "category": "layout/row",
    "description": "HStack with configurable leading icon and content slots",
    "use-when": "any row needing a leading icon with flexible content",
    "do-not-use-when": "grids, sectioned lists, rows with trailing actions",
    "props": "icon: String?, leading: @ViewBuilder, trailing: @ViewBuilder?"
  }
]
```

### Validation mode

```bash
python scripts/registry.py --validate
# Fails if: any Shared/ file missing frontmatter
# Fails if: similarity score > 0.85 between any two use-when fields
# Fails if: required fields are empty
```

### Synonym groups for semantic grep (Layer 1)

- row: cell, item, tile, entry, listRow
- icon: symbol, image, leading, badge
- container: wrapper, shell, frame, card
- loading: spinner, skeleton, placeholder, shimmer
- list: collection, feed, grid, stack

### Verified status (2026-03-12)

**Not implemented.** No top-level `scripts/` directory exists. Scripts live within individual skills (`skills/*/scripts/`). Existing `parse-frontmatter.py` parses YAML frontmatter from markdown files. `discover-principles.py` discovers principles by globbing `*/rule.md`. Neither handles Swift file frontmatter.

**Plan:** Create `scripts/registry.py` that: (1) walks `Sources/Shared/**/*.swift`, (2) parses Swift comment frontmatter (`// ---` blocks), (3) outputs structured JSON, (4) `--validate` mode checks for missing frontmatter + use-when similarity. Could reuse `parse-frontmatter.py` logic for YAML parsing.

---

## S-34: `/code` skill Section 3.5 — Shared Component Creation

**Impact**: Medium | **Effort**: Low | **Category**: Pipeline enhancement

**Status**: Pending — depends on S-32, S-33

Add Section 3.5 to `skills/code/SKILL.md` Phase 3 (File Organization). When creating ANY new file in `Sources/Shared/`:

1. Run DRY check (both layers): `python scripts/registry.py` + grep synonyms
2. If match found → configure existing component, do NOT create new file
3. If no match → design generic component, prefill frontmatter FIRST, then write Swift

### Verified status (2026-03-12)

**Not implemented.** `skills/code/SKILL.md` Phase 3 has sections 3.1-3.4 only. No mention of shared components, DRY checks, or frontmatter prefill. Closest existing logic is 3.1's "Always search before creating" instruction.

**Plan:** Add Section 3.5 "Shared Component Creation" after 3.4 in `skills/code/SKILL.md`: search for existing shared components, place reusable types in shared location, add frontmatter to new files, cross-reference with DRY rules.

---

## S-35: Pre-commit hook for frontmatter validation

**Impact**: Medium | **Effort**: Low | **Category**: Enforcement

**Status**: Pending — depends on S-33

Create `scripts/hooks/pre-commit` that runs `python scripts/registry.py --validate`. Blocks commits if any `Shared/` file is missing frontmatter. Three enforcement gates:

1. **Gate 1 — CC skill** (creation time) — DRY check + frontmatter prefill in `/code` skill
2. **Gate 2 — Pre-commit hook** (human-created files) — blocks commit
3. **Gate 3 — PR check** (CI) — same script, nothing merges without it

---

## S-36: Two-tier rule system — formalize always-on vs dynamic rules

**Impact**: High | **Effort**: Medium | **Category**: Architecture

**Status**: Pending

`discover-principles` already does tag-based activation, but there's no formal tier model. The handover proposes:

**Tier 1 — SOLID (always loaded, full pipeline):**
- `activation: always` — goes through full review → synthesize → implement pipeline

**Tier 2 — Dynamic (loaded based on detected context):**
- SwiftUI: `activation: imports: [SwiftUI]`
- Concurrency: `activation: imports: [Combine, _Concurrency]`
- GCD: `activation: patterns: [DispatchQueue, DispatchGroup]`
- Testing: `activation: context: [XCTestCase, Testing]`

### Key insight

`refactor-implement` should only receive rules referenced in the analysis — not everything available. Currently may load too broadly.

### Verified status (2026-03-12)

**Partially implemented.** Tag-based activation works: `discover-principles.py` filters by tags. Rules without `tags` (SRP, OCP, LSP, ISP) are always active. SwiftUI has `tags: [swiftui]` making it conditional.

**Gaps:**
- No `category` or `cross_check_tier` fields in any actual `rule.md` frontmatter (ARCHITECTURE.md describes these but they're aspirational)
- `synthesize-fixes/SKILL.md` cross-checks against "all OTHER active principles" without tier hierarchy — doesn't implement directional cross-checking from ARCHITECTURE.md
- Tag system is binary: no tags = always, has tags = conditional. No formal tier concept.

**Plan:**
1. Add `tier: core|practice|framework` to each `rule.md` frontmatter
2. Update `discover-principles.py` to parse and expose tier field
3. Update `synthesize-fixes/SKILL.md` Phase 4.1 to respect tier-based cross-check direction

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

## S-38: Extend `prepare-review-input` context detection

**Impact**: Medium | **Effort**: Medium | **Category**: Pipeline enhancement

**Status**: Pending

Tag matching in `prepare-review-input` exists but doesn't detect:

- **Concurrency model**: async/await vs GCD (`DispatchQueue`) vs Combine (`Publisher`/`Subscriber`)
- **Test target vs production target**: presence of `XCTestCase`, `@testable import`, `Testing` framework
- **UI framework**: SwiftUI vs UIKit vs AppKit

This detection is needed for Tier 2 dynamic rule loading (S-36). The `prepare-review-input` skill already collects imports — extend it to also classify these dimensions.

### Verified status (2026-03-12)

**Partially implemented.** The SKILL.md Tag Matching section (lines 96-106) describes import detection and pattern matching including concurrency model detection (`DispatchQueue` → gcd, `async/await` → structured-concurrency, `Publisher/Subscriber` → combine). UI framework handled through import detection.

**Gaps:**
- Test vs production target detection: no mechanism for `XCTest` import, `*Tests.swift` naming, or test target membership
- Concurrency model detection described in SKILL.md instructions but NOT codified in `prepare-changes.py` — the script only extracts raw imports. Semantic pattern matching relies entirely on LLM judgment at runtime.
- No structured taxonomy — tag matching is open-ended ("use your judgment")

**Plan:**
1. Add test file detection to `prepare-changes.py`: check `XCTest`/`Testing` imports, `*Tests.swift` naming, add `is_test_file` field per file
2. Move semantic pattern matching from LLM instructions into Python script for deterministic results
3. Add framework detection patterns beyond imports (e.g., `@Observable` → SwiftUI, `UIViewController` → UIKit)

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

## Suggestion Status Tracker

| ID | Summary | Impact | Effort | Status | Verified |
|----|---------|--------|--------|--------|----------|
| S-01 | Always-on SOLID enforcement (rules not distributable via plugin) | High | Low | Blocked — needs design decision | — |
| S-02 | Fix model selection (Sonnet for mechanical tasks) | High | Low | Partial — refactor pipeline uses sonnet for review, haiku for mechanical; review pipeline bundles review+fix in opus | 2026-03-12 |
| S-03 | Pre-compute rule index | Medium | Low | Partial — `discover-principles` script replaces manual glob+parse; caching is remaining optimization | — |
| S-04 | Short-circuit trivial changes (with LSP-safe tier 2) | Medium | Low | Partial — MINOR-only short-circuit exists in refactor; no pre-review triviality detection | 2026-03-12 |
| S-05 | Post-synthesis verification script | High | Medium | Not implemented — synthesis cross-check is LLM mental exercise, not automated | 2026-03-12 |
| S-06 | Graceful degradation for partial failures | Medium | Medium | Pending | — |
| S-07 | Fix `ruler.md` typo | Low | Trivial | Done — no `ruler.md` references remain | 2026-03-12 |
| S-08 | Standardize path template substitution | Medium | Medium | Partial | — |
| S-09 | Detect oscillation in iteration loop | Medium | Low | Not implemented — only hard MAX_ITERATIONS cap, no cross-iteration comparison | 2026-03-12 |
| S-10 | Output cleanup mechanism | Low | Low | Not implemented — no cleanup, `.solid_coder/` not gitignored | 2026-03-12 |
| S-11 | Prioritize ISP and DIP principles | High | High | Partial — ISP complete. DIP not started. | 2026-03-12 |
| S-12 | Schema validation for all agent outputs | Medium | Medium | Partial — validate-findings validates when plugin_root provided; synthesis output not validated; jsonschema silently optional | 2026-03-12 |
| S-13 | Delta-aware review — only report regressions | High | High | Partial — unit-level `has_changes` + line-range filtering work; no baseline for pre-existing violations in changed regions | 2026-03-12 |
| S-14 | Fix iteration loop: `git add` between iterations | High | Low | Done | — |
| S-15 | `addresses` vs `resolves` field name | Low | — | Not a bug — different fields at different pipeline stages, intentional design | 2026-03-12 |
| S-16 | **CRITICAL**: validate-findings passes unknown files | Critical | Low | Not implemented — `_filter_findings()` line 253 treats unknown files as "entire file new" | 2026-03-12 |
| S-17 | Missing `tier`/`activation` in rule.md frontmatter | High | Low | Done — replaced with tag-based activation via `discover-principles` skill | — |
| S-18 | `file_path` vs `file` field inconsistency | High | Medium | Not implemented — `prepare-review-input` uses `file_path`, all 13 other schemas use `file` | 2026-03-12 |
| S-19 | Unit context lost in validation/synthesis schemas | High | Low | Done — unit_name/unit_kind preserved through full pipeline | 2026-03-12 |
| S-20 | Missing `has_changes` in prepare-input schema | Medium | Trivial | Done — type is `"boolean"`, not nullable | 2026-03-12 |
| S-21 | No tests for `prepare-changes.py` | High | Medium | Not implemented — 6 other scripts have tests, this one has zero | 2026-03-12 |
| S-22 | Missing JSON error handling in Python scripts | Medium | Low | Not implemented — 4 scripts have bare json.load() with no error handling | 2026-03-12 |
| S-23 | README.md rewrite | Medium | Low | Not implemented — still 2 lines with typo | 2026-03-12 |
| S-24 | Empty `design_patterns/creational/` directory | Low | Trivial | Confirmed empty | 2026-03-12 |
| S-25 | Orchestrator error handling is ambiguous | High | Medium | Partial — prepare-input failures handled; parallel agent failures unspecified | 2026-03-12 |
| S-26 | AST-based metric extraction (tree-sitter) | High | High | POC needed — validate on Examples/ first | — |
| S-27 | Pre-plan target architecture before incremental refactoring | High | Medium | Partial — per-file planning exists in synthesize-fixes; no cross-file architectural vision | 2026-03-12 |
| S-28 | Short-circuit MINOR-only findings — skip synthesis/implement | Medium | Low | Done — refactor pipeline Phase 4.6 with check-severity.py | 2026-03-12 |
| S-29 | `/code` greenfield gap — no source files for tag matching | Medium | Low | Done — Phase 2.2 line 34 explicitly handles greenfield | 2026-03-12 |
| S-30 | SwiftUI SUI-2/SUI-3 — validate SOLID coverage | Medium | Medium | Validate — needs testing | — |
| S-31 | SwiftUI "dumb view" rule | High | Low | Done — implemented as SUI-2 (View Purity) metric | — |
| S-32 | DRY principle — full `references/DRY/` implementation | High | High | Not implemented — no `references/DRY/` directory | 2026-03-12 |
| S-33 | Component registry script (`scripts/registry.py`) | High | Medium | Not implemented — no `scripts/` directory exists | 2026-03-12 |
| S-34 | `/code` skill Section 3.5 — Shared Component Creation | Medium | Low | Not implemented — no Section 3.5 in SKILL.md | 2026-03-12 |
| S-35 | Pre-commit hook for frontmatter validation | Medium | Low | Not implemented — depends on S-33 | — |
| S-36 | Two-tier rule system | High | Medium | Partial — tag-based activation works; no formal tier model or directional cross-checking | 2026-03-12 |
| S-37 | Style rules separate pipeline | Medium | Medium | Not implemented — no mechanism for review-only rules | 2026-03-12 |
| S-38 | Extend `prepare-review-input` context detection | Medium | Medium | Partial — imports + tag matching exist; test detection missing; semantic patterns LLM-dependent | 2026-03-12 |