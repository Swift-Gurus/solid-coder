# Partial Improvement Suggestions

Suggestions that have been partially implemented — some work done, remaining gaps identified.

---

## S-02: Fix model selection for cost efficiency

**Impact**: High | **Effort**: Low | **Category**: Cost reduction

Current model assignment:

| Agent | Current Model | Task Type |
|-------|--------------|-----------|
| `principle-review-fx-agent` | Opus | Following documented checklists |
| `apply-principle-review-agent` | Default | Following documented checklists |
| `synthesize-fixes-agent` | Opus | Deep cross-principle reasoning |
| `code-agent` | Opus | Writing code with rules as constraints |
| `prepare-review-input-agent` | Sonnet | Diff parsing + unit detection |
| `validate-findings-agent` | Sonnet | Running Python script |
| `generate-report-agent` | Sonnet | Running Python script |

**Suggested changes**:

| Agent | Suggested Model | Rationale |
|-------|----------------|-----------|
| `principle-review-fx-agent` | **Sonnet** | Checklist execution with documented metrics — mechanical |
| `apply-principle-review-agent` | **Sonnet** | Same reasoning |
| `synthesize-fixes-agent` | Opus (keep) | Genuine deep reasoning needed |
| `code-agent` | Opus (keep) | Needs reasoning to satisfy rules while writing |

**Estimated savings**: ~50-60% token cost reduction per run. Review agents are the most parallelized (3x), so downgrading them has outsized impact.

**Risk**: Sonnet may miss subtle violations. Mitigate by testing against the Examples/ directories for each principle.

### Verified status (2026-03-12)

**Partially implemented.** Actual current model assignments differ from original doc:

| Agent | Actual Model | Notes |
|-------|-------------|-------|
| `apply-principle-review-agent` | `sonnet` | Review-only in refactor pipeline — already downgraded |
| `principle-review-fx-agent` | `opus` | Review + fix in review pipeline — bundles two tasks |
| `prepare-review-input-agent` | `haiku` | Cheaper than suggested sonnet |
| `validate-findings-agent` | `haiku` | Cheaper than suggested sonnet |
| `generate-report-agent` | `haiku` | Cheaper than suggested sonnet |
| `synthesize-fixes-agent` | `opus` | Correct — needs deep reasoning |
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

**Update**: frontmatter parsing now handled by mcp-server/lib/ and produces `files_to_load` per principle. A cached index would further reduce repeated script calls. Status: **Partially addressed** — caching is the remaining optimization.

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

**Addressed**: The `/code` skill (Phase 5) now writes a structured `refactor-log.json` with `file` (target), `files_created[]` (new types), and `files_modified[]` (side-effect changes like call sites). The orchestrator (step 7.8) uses this to build `REVIEW_FILES` (targets + created) vs `DEPENDENT_FILES` (modified side effects), and only passes `REVIEW_FILES` to Phase 8.

**3. Change-boundary scoping (future)**: Even on first pass, scope the review to the changed units (functions, types) rather than the whole file. If a diff only touches a call site, don't review the caller's class for SOLID violations unrelated to the change.

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

**Update**: `parse-frontmatter` script now handles `PRINCIPLE_FOLDER_ABSOLUTE_PATH` token replacement and resolves all paths to absolute. rules loaded via docs MCP with frontmatter stripped get clean content. Skills use `!` bash calls to run these scripts. Status: **Partially addressed** — `CURRENT_PROJECT` and `{RULES_PATH}` still rely on LLM interpretation.

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

**Partially implemented.** Tag-based activation works: docs MCP `discover_principles` filters by tags. Rules without `tags` (SRP, OCP, LSP, ISP) are always active. SwiftUI has `tags: [swiftui]` making it conditional.

**Gaps:**
- No `category` or `cross_check_tier` fields in any actual `rule.md` frontmatter (ARCHITECTURE.md describes these but they're aspirational)
- `synthesize-fixes/SKILL.md` cross-checks against "all OTHER active principles" without tier hierarchy — doesn't implement directional cross-checking from ARCHITECTURE.md
- Tag system is binary: no tags = always, has tags = conditional. No formal tier concept.

**Plan:**
1. Add `tier: core|practice|framework` to each `rule.md` frontmatter
2. Update `discover-principles.py` to parse and expose tier field
3. Update `synthesize-fixes/SKILL.md` Phase 4.1 to respect tier-based cross-check direction

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

## Partial Suggestion Status Tracker

| ID | Summary | Impact | Effort | Status | Verified |
|----|---------|--------|--------|--------|----------|
| S-02 | Fix model selection (Sonnet for mechanical tasks) | High | Low | Partial — refactor pipeline uses sonnet for review, haiku for mechanical; review pipeline bundles review+fix in opus | 2026-03-12 |
| S-03 | Pre-compute rule index | Medium | Low | Partial — `mcp__plugin_solid-coder_docs__discover_principles` tool replaces manual glob+parse; caching is remaining optimization | — |
| S-04 | Short-circuit trivial changes (with LSP-safe tier 2) | Medium | Low | Partial — MINOR-only short-circuit exists in refactor; no pre-review triviality detection | 2026-03-12 |
| S-08 | Standardize path template substitution | Medium | Medium | Partial | — |
| S-11 | Prioritize ISP and DIP principles | High | High | Partial — ISP complete. DIP not started. | 2026-03-12 |
| S-12 | Schema validation for all agent outputs | Medium | Medium | Partial — validate-findings validates when plugin_root provided; synthesis output not validated; jsonschema silently optional | 2026-03-12 |
| S-13 | Delta-aware review — only report regressions | High | High | Partial — unit-level `has_changes` + line-range filtering work; no baseline for pre-existing violations in changed regions | 2026-03-12 |
| S-25 | Orchestrator error handling is ambiguous | High | Medium | Partial — prepare-input failures handled; parallel agent failures unspecified | 2026-03-12 |
| S-27 | Pre-plan target architecture before incremental refactoring | High | Medium | Partial — per-file planning exists in synthesize-fixes; no cross-file architectural vision | 2026-03-12 |
| S-36 | Two-tier rule system | High | Medium | Partial — tag-based activation works; no formal tier model or directional cross-checking | 2026-03-12 |
| S-38 | Extend `prepare-review-input` context detection | Medium | Medium | Partial — imports + tag matching exist; test detection missing; semantic patterns LLM-dependent | 2026-03-12 |
