# Flows

## 1. Review Flow (`/review`)

`/review` is a **thin wrapper** over `/refactor --review-only`. It delegates the entire review+synthesize pipeline to refactor, then aggregates iteration data into a single MD + HTML report.

### Trigger
User runs `/review <target>` (branch, folder, file, or current changes).

### Steps

```
Step 1: Stage output root
─────────────────────────
  Action: Compute timestamp, set OUTPUT_ROOT = {project}/.solid_coder/review-<ts>/

Step 2: Run /refactor --review-only
───────────────────────────────────
  Delegates to refactor flow (see §2) with flags:
    --review-only  stops after Phase 6 (synthesize), no code changes, no iterations
    --output-root  forces refactor to write under OUTPUT_ROOT

  Produces:
    {OUTPUT_ROOT}/1/by-file/*.output.json
    {OUTPUT_ROOT}/1/synthesized/*.plan.json
    {OUTPUT_ROOT}/1/refactor-log.json  (status: "review_only")

Step 3: Generate reports
────────────────────────
  Runs: gateway.py generate_report --data-dir {OUTPUT_ROOT} --report-dir {OUTPUT_ROOT}
  Behavior:
    - Aggregates by-file findings across all iteration subdirs (dedup by finding_id)
    - Aggregates synthesized actions across all iterations (dedup by suggestion_id)
    - Organizes by file, produces one combined report
  Outputs:
    {OUTPUT_ROOT}/report.md
    {OUTPUT_ROOT}/report.html
```

---

## 2. Refactor Flow (`/refactor`)

The refactor flow **modifies source code**. It includes the full review pipeline plus synthesis, implementation, and iteration.

### Trigger
User runs `/refactor` with a target and optional flags: `--iterations N` (default 2), `--review-only` (stops after synthesize, no code changes), `--output-root <path>`, `--verbose`.

### Steps

```
Steps 1–3: Same as Review (Discover Principles + Prepare Input + Filter)

Step 4: Parallel Principle Review (review only, no fix)
──────────────────────────────────────────────────────
  Agent:  apply-principle-review-agent × N (parallel)
  Why:    Synthesis handles fix planning holistically — individual fix suggestions
          would be generated in isolation without cross-principle awareness
  Output: {OUTPUT_ROOT}/rules/{PRINCIPLE}/review-output.json

Step 5: Validate Findings
─────────────────────────
  Same as review flow Step 6

Step 6: Synthesize Fixes (Two-Pass)
────────────────────────────────────
  Agent:  synthesize-fixes-agent (opus)
  Input:  All validated findings + principle fix knowledge
  Action:
    Phase 1 — Load context:
      - Read all by-file/*.output.json
      - Load fix/instructions.md only for principles that have findings

    Phase 2 — Draft per-principle actions:
      - For each file, for each principle with findings:
        - Generate focused fix actions using that principle's fix patterns
        - Each action gets: suggestion_id, resolves[], todo_items[], suggested_fix

    Phase 3 — Cross-check:
      - For each draft action, check against ALL other active principles' metrics:
        - Would this SRP extraction create sealed points? (OCP check)
        - Would this OCP injection create multiple cohesion groups? (SRP check)
        - Would this new protocol hierarchy need type checking? (LSP check)
      - If a cross-check fails: patch the action using the failing principle's patterns
      - If patching fails: mark finding as "unresolved" with reason

    Phase 4 — Merge & Order:
      - Merge synergistic actions (e.g., SRP extraction + OCP injection for same code)
      - Resolve conflicts (same code claimed by multiple principles)
      - Dependency-order actions (depends_on graph)
      - Sort by severity (SEVERE first)

  Output: {OUTPUT_ROOT}/synthesized/{filename}.plan.json per file

Step 7: Parallel Implementation
────────────────────────────────
  Agent:  code-agent × M (opus, parallel, one per file)
  Input:  plan.json for one file
  Action:
    - Read plan, order by depends_on graph + severity
    - Apply code changes using Edit tool
    - For new types: split into separate files
      - Protocol + base implementation = one file (named after implementation)
      - Additional conformers = separate files
      - Small helpers (<10 lines) stay inline
    - Write per-file refactor-log.json
  Output: Modified source files + refactor-log.json

Step 8: Iteration Loop
───────────────────────
  Condition: iteration_counter < MAX_ITERATIONS
  Action:
    1. Increment counter
    2. Re-prepare input with source_type = "changes" (only modified files)
    3. Re-run review on changed files
    4. If new findings → re-synthesize + re-implement
    5. Repeat until clean or max iterations reached
  Output: Cumulative refactor-log.json with phase timings
```

### Sequence Diagram

```
User ──► /refactor target --iterations 2
          │
    ┌─────▼───────┐
    │ Discover     │ ──► candidate_tags
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ Prepare      │ ──► matched_tags
    │ Input        │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ Filter +     │                   ┌──────────────────┐
    │ Parallel     │                   │                  │
    │ Review       │◄──────────────────│  ITERATION LOOP  │
    │ (review only)│                   │  (max N times)   │
    └──────┬──────┘                   │                  │
           │                          └────────▲─────────┘
    ┌──────▼──────┐                            │
    │ Validate     │                            │
    └──────┬──────┘                            │
           │                                    │
    ┌──────▼──────┐                            │
    │ Synthesize   │                            │
    │ (two-pass)   │                            │
    └──────┬──────┘                            │
           │                                    │
    ┌──────▼──────────────┐                    │
    │ Parallel Implement   │────────────────────┘
    │ (one agent per file) │    (if new findings on re-review)
    └─────────────────────┘
```

---

## 3. Code Flow (`/code`)

The code flow **writes or modifies Swift code** with SOLID principles as active constraints.

### Trigger
User runs `/code` with a plan JSON, spec file, or inline prompt.

### Steps

```
Step 1: Parse Input
───────────────────
  Accepts three input forms:
    - plan.json (from synthesize-fixes, with specific actions to implement)
    - Spec file (markdown describing what to build)
    - Inline prompt (natural language description)

Step 2: Discover & Load Rules
─────────────────────────────
  - Run discover-principles skill → all principles + candidate tags
  - If candidate tags exist: scan source for matching tags, re-run discovery with matched tags
  - For each active principle: run parse-frontmatter on rule.md
  - Run load-reference to load rules and references with frontmatter stripped
  - These become active constraints for code generation

Step 3: Write Code
──────────────────
  For each piece of code to write, follows a dependency resolution tree:
    1. Search project for existing protocol/type → reuse if found
    2. Check if extension conformance can satisfy need → use if possible
    3. Create adapter/wrapper → if the type can't conform directly
    4. Create helper → only if it's an exception type (Encoder, Formatter, Lock)

  File organization:
    - Protocol + base implementation = one file (named after implementation)
    - Additional conformers = separate files
    - Small helpers (<10 lines) stay inline

Step 4: Self-Check
──────────────────
  - For every file created or modified:
    - Run each loaded rule's metrics against the code
    - If SEVERE violations found: fix inline immediately
    - If MINOR: note but don't necessarily fix

Step 5: Report
──────────────
  - List all files created/modified
```

---

## 4. Input Source Types

The `prepare-review-input` stage handles five different ways to specify what to review:

| Source Type | What It Analyzes | Changed Ranges |
|-------------|------------------|----------------|
| `branch` | Diff between current branch and base | Lines from git diff |
| `changes` | Staged + unstaged + untracked files | Lines from git diff + full untracked files |
| `folder` | All Swift files in directory | Entire files (no filtering) |
| `file` | Single Swift file | Entire file (no filtering) |
| `buffer` | Inline code passed directly | Entire content (no filtering) |

For `branch` and `changes`, findings are later filtered to only changed line ranges by the validation step. For `folder`, `file`, and `buffer`, all findings are kept.

---

## 5. Finding Lifecycle

A finding progresses through these states across the pipeline:

```
Detection (review)
    │
    ▼
Filtered (validate — must overlap changed range)
    │
    ▼
Planned (synthesize — cross-checked, dependency-ordered)
    │
    ├──► Resolved (implemented successfully)
    │
    └──► Unresolved (cross-check failed, no safe fix possible)
```

Each finding carries a principle-prefixed ID (e.g., `srp-001`, `ocp-003`, `lsp-002`) that threads through the entire pipeline for traceability.
