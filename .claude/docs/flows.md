# Flows

## 1. Review Flow (`/review`)

The review flow is **read-only** — it analyzes code and produces an HTML report without modifying any source files.

### Trigger
User runs `/review` with a target (branch, folder, file, or current changes).

### Steps

```
Step 1: Discover Principles
───────────────────────────
  Agent:  orchestrator (inline)
  Action:
    - Runs discover-principles skill → all principles + all_candidate_tags
  Output: Principle list + candidate tags for activation

Step 2: Prepare Input
─────────────────────
  Agent:  prepare-review-input-agent (haiku)
  Input:  User target + candidate_tags from Step 1
  Action:
    - For "changes" mode: runs prepare-changes.py to parse git diff + extract imports
    - For all modes: identifies Swift units (class, struct, protocol, enum, extension)
    - Detects which units overlap changed line ranges
    - Matches candidate_tags against code (imports + usage patterns) → matched_tags
  Output: {OUTPUT_ROOT}/prepare/review-input.json (with detected_imports + matched_tags)

Step 3: Filter Principles
─────────────────────────
  Agent:  orchestrator (inline)
  Action:
    - Runs discover-principles skill with --review-input → active_principles
    - Rules with no tags → always active
    - Rules with tags → active only if any tag in matched_tags
  Output: Filtered list of active principles

Step 4: Parallel Principle Review + Fix
───────────────────────────────────────
  Agent:  principle-review-fx-agent × N (opus, parallel)
  Input:  review-input.json + principle-specific instructions + rule + examples
  Action per agent:
    1. Run apply-principle-review skill:
       - Load rule.md metrics and severity bands
       - Load review/instructions.md phased checklist
       - Load design pattern references (if required_patterns set)
       - For each file/unit with has_changes == true (null is never expected — prepare-input must set true or false):
         - Compute metrics (e.g., SRP: verb count, cohesion groups, stakeholders)
         - Check exceptions (facade, helper, boundary adapter, NoOp)
         - Score severity
         - Emit findings with IDs (e.g., srp-001)
    2. Run fix-suggest skill:
       - Load fix/instructions.md
       - For each finding, generate fix suggestion with:
         - Suggested code changes
         - Todo items (checklist)
         - Verification criteria
  Output: {OUTPUT_ROOT}/rules/{PRINCIPLE}/review-output.json + fix.json

Step 5: Collect & Print Summary
───────────────────────────────
  Agent:  orchestrator (inline)
  Action: Reads all review-output.json files, prints summary table
  Output: Console summary (principle | files | findings | worst severity)

Step 6: Validate Findings
─────────────────────────
  Agent:  validate-findings-agent (haiku)
  Action: Runs validate-findings.py which:
    - Filters findings to only those in changed line ranges
      (skipped for folder/file/buffer source types)
    - Reorganizes findings by file path
    - Schema-validates all inputs
    - Matches fix suggestions to their findings
  Output: {OUTPUT_ROOT}/by-file/{filename}.output.json

Step 7: Generate Report
───────────────────────
  Agent:  generate-report-agent (haiku)
  Action: Runs generate-report.py which:
    - Reads all by-file/*.output.json
    - Renders self-contained HTML with:
      - Summary table (file, severity badge, counts)
      - Per-file sections with principle-grouped findings
      - Fix suggestions with code blocks and verification
  Output: {OUTPUT_ROOT}/report.html
```

### Sequence Diagram

```
User ──► /review target
          │
    ┌─────▼───────┐
    │ Discover     │ ──► all_candidate_tags
    │ Principles   │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ Prepare      │ ──► review-input.json (with matched_tags)
    │ Input        │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ Filter       │ ──► active_principles
    │ Principles   │
    └──────┬──────┘
           │
    ┌──────▼───────────────────────────────────┐
    │         Parallel Review + Fix            │
    │  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  │
    │  │ SRP │  │ OCP │  │ LSP │  │ ISP │  │
    │  └──┬──┘  └──┬──┘  └──┬──┘  └──┬──┘  │
    └─────┼────────┼────────┼────────┼──────┘
          │        │        │        │
          ▼        ▼        ▼        ▼
    ┌─────────────────────────────────┐
    │ Validate Findings                │ ──► by-file/*.output.json
    └──────────────┬──────────────────┘
                   │
    ┌──────────────▼──────────────────┐
    │ Generate Report                  │ ──► report.html
    └─────────────────────────────────┘
```

---

## 2. Refactor Flow (`/refactor`)

The refactor flow **modifies source code**. It includes the full review pipeline plus synthesis, implementation, and iteration.

### Trigger
User runs `/refactor` with a target and optional `--iterations N` (default 2).

### Steps

```
Steps 1–3: Same as Review (Discover Principles + Prepare Input + Filter)

Step 4: Parallel Principle Review (review only, no fix)
──────────────────────────────────────────────────────
  Agent:  principle-review-agent × N (parallel)
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
      - Retry up to 3 attempts. If violations remain after 3 attempts: mark finding as "unresolved" with reason

    Phase 4 — Merge & Order:
      - Merge synergistic actions (e.g., SRP extraction + OCP injection for same code)
      - Resolve conflicts (same code claimed by multiple principles)
      - Dependency-order actions (depends_on graph)
      - Sort by severity (SEVERE first)

  Output: {OUTPUT_ROOT}/synthesized/{filename}.plan.json per file

Step 7: Parallel Implementation
────────────────────────────────
  Agent:  refactor-implement-agent × M (opus, parallel, one per file)
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
Suggestion (fix-suggest)
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
