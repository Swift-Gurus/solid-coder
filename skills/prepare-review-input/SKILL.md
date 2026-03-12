---
name: prepare-review-input
description: Normalize input (branch diff, folder, files, class, buffer) into structured review-input.json for review agents.
argument-hint: [branch|changes|folder|file|files|buffer] [target] [--base <branch>]
allowed-tools: Read, Grep, Glob, Bash, Write
user-invocable: false
---

# Prepare Review Input

## Input
- SOURCE_TYPE: $ARGUMENTS[0] — one of: branch, changes, folder, file, files, buffer
  - If $ARGUMENTS[0] is not a known type you must stop and show an error message. Unknown Type
  - If NO arguments provided → default to branch diff (current branch vs base)
- OUTPUT_ROOT: $ARGUMENTS[1] - output root if not provided use CURRENT_PROJECT/.solid-coder-<YYYYMMDDhhmmss>
- CANDIDATE_TAGS: optional list of tags from the orchestrator (extracted from rule.md frontmatters)
- OUTPUT_PATH: {OUTPUT_ROOT}/prepare
- SKILL_ROOT: ${CLAUDE_PLUGIN_ROOT}/skills/prepare-review-input
## Workflow

### Phase 1: Input Detection & Validation
Create Preparation task list and execute it.
- [ ] 1.1 **Create output folder** — Create `OUTPUT_PATH`
- [ ] 1.2 **Detect source type** — 
  - SOURCE_TYPE not recognized, fail with the message (don't continue):
  - NO arguments → `branch` (default: review all changes on current branch)
  - is a directory path → `folder`
  - is a file path → `file`
  - contains newlines or is after explicit `buffer` keyword → `buffer`
- [ ] 1.3 **Validate target** — Confirm file/folder is accessible (skip for branch type)
- [ ] 1.4 **Read output schema** — Read `output.schema.json` from this skill's directory

### Phase 2: Loading content
- [ ] 2.0.1 **Load content**
   - if mode is Changes then load content using Phase 2.1
   - if mode is Folder then load content using Phase 2.2
   - if mode is File then load content using Phase 2.3
   - if mode is Files then load content using Phase 2.5
   - if mode is Buffer then load content using Phase 2.4

#### Phase 2.1: Changes 
- [ ] 2.1.1 **Run prepare-changes script** — 
    ```bash
        python3 {SKILL_ROOT}/scripts/prepare-changes.py -o OUTPUT_PATH/review-input.json
    ```
  - This collects staged + unstaged + untracked changes, parses diffs, and writes structured JSON with per-file changed ranges
- [ ] 2.1.2 **Read generated JSON** — Read `OUTPUT_PATH/review-input.json`
- [ ] 2.1.3 **Read changed files** — Read each file listed in the JSON from disk
- [ ] 2.1.4 **Identify units** — Run unit identification on each file (see Unit Identification)
  - Set `has_changes` for every unit — it must be `true` or `false`, NEVER `null`:
    - if the file's `changed_ranges` is `null`, empty, or missing → set `has_changes = true` for ALL units in that file (whole-file review)
    - if the file has `changed_ranges` (non-empty array) →
         check if ANY changed_range overlaps with [unit.line_start, unit.line_end].
         Overlap = range.start <= unit.line_end AND range.end >= unit.line_start.
         If overlap exists → has_changes = true, otherwise → has_changes = false
- [ ] 2.1.5 **Match tags** — If CANDIDATE_TAGS were provided (see Tag Matching section below), match them against the code you've read and merge with `detected_imports` into `matched_tags`
- [ ] 2.1.6 **Update JSON** — Write units and matched_tags back into `OUTPUT_PATH/review-input.json` and update summary counts

#### Phase 2.2: Folder
- [ ] 2.2.1 **Read all files**
- [ ] 2.2.2 **Match tags** — If CANDIDATE_TAGS were provided, match them against the code (see Tag Matching)

#### Phase 2.3: File
- [ ] 2.3.1 **Read the file**
- [ ] 2.3.2 **Match tags** — If CANDIDATE_TAGS were provided, match them against the code (see Tag Matching)

#### Phase 2.5: Files (explicit file list)
- [ ] 2.5.1 **Parse file list** — Extract the list of file paths from the input (provided as JSON array or space-separated paths)
- [ ] 2.5.2 **Read each file** — Read all listed files from disk. If a file doesn't exist (was deleted), skip it.
- [ ] 2.5.3 **Identify units** — Run unit identification on each file (see Unit Identification). Set `has_changes = true` for ALL units (whole-file review).
- [ ] 2.5.4 **Set changed_ranges** — Set `changed_ranges: null` for every file (triggers whole-file review)
- [ ] 2.5.5 **Match tags** — If CANDIDATE_TAGS were provided, match them against the code (see Tag Matching)
- [ ] 2.5.6 **Write structured output** — Write to `OUTPUT_PATH/review-input.json` with `source_type: "files"`

#### Phase 2.4: Buffer
- [ ] 2.4.1 **Capture buffer string** — Store raw input
- [ ] 2.4.2 **Match tags** — If CANDIDATE_TAGS were provided, match them against the buffer (see Tag Matching)

### Phase 3: Assembly & Output
- [ ] 3.1 **Extract imports** (for folder/file/buffer modes) — Scan the loaded source code for `import <ModuleName>` statements. Collect unique module names into `detected_imports` array (sorted). For changes mode, the script already handles this.
- [ ] 3.2 **Write structured output** - using defined schema write to `OUTPUT_PATH/review-input.json` (include `detected_imports` and `matched_tags`)

## Diff Parsing

Parse unified diff to extract changed line ranges per file:

1. Split by `^diff --git a/(.*) b/(.*)$` — use b/ path as file_path
2. Find hunk headers: `^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@`
   - Group 1 = new file start line
3. Walk hunk lines from start line:
   - `+` line (not `+++`): mark line as changed, increment line counter
   - `-` line (not `---`): skip (deletion), do NOT increment
   - ` ` context line: increment line counter
4. Coalesce adjacent changed lines into ranges `{ "start": N, "end": M }`

## Unit Identification

Read the file and list every top-level declaration:
- **What to find:** class, struct, protocol, enum, extension
- **For each:** report `name`, `kind`, `line_start`
- **line_start** = the line number where the declaration begins
- **line_end:** = the line number of the next unit - 1

## Tag Matching

If CANDIDATE_TAGS is provided (non-empty list), determine which tags apply to the code being reviewed. You already have the code loaded from Phase 2.

1. Start with `detected_imports` from the script output (raw import names like `SwiftUI`, `UIKit`, `Combine`)
2. For each CANDIDATE_TAG, check if the code matches it:
   - Check `detected_imports` — does any import name match the tag (case-insensitive)?
   - Check code patterns — e.g., tag `gcd` matches `DispatchQueue` usage, tag `structured-concurrency` matches `async`/`await`/`Task {` usage, tag `combine` matches `Publisher`/`Subscriber` usage
   - Use your judgment for semantic tags that don't map directly to imports
3. Merge all matched tags into the `matched_tags` array (lowercase, deduplicated)

If CANDIDATE_TAGS is empty or not provided, set `matched_tags` to an empty array.

## Constraints
- Do NOT modify any source files
- Do NOT write buffer input to a separate file — keep it in the JSON
- Do NOT resolve any issues with the workflow, if anything fails:
  - file not found
  - will consume too many tokens > 200k
  You fail with a message
