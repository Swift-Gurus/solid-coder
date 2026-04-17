---
name: prepare-review-input
description: Normalize input (changes, folder, files, class, buffer) into structured review-input.json for review agents.
argument-hint: [changes|folder|file|files|buffer] [target]
allowed-tools: Read, Grep, Glob, Bash, Write
user-invocable: false
---

# Prepare Review Input

## Input
- SOURCE_TYPE: $ARGUMENTS[0] — one of: changes, folder, file, files, buffer
  - If $ARGUMENTS[0] is not a known type you must stop and show an error message. Unknown Type
  - If NO arguments provided → default to `changes` (staged + unstaged + untracked)
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
  - NO arguments → `changes` (default: review current git changes)
  - is a directory path → `folder`
  - is a file path → `file`
  - contains newlines or is after explicit `buffer` keyword → `buffer`
- [ ] 1.3 **Validate target** — Confirm file/folder is accessible (skip for changes type)
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
  - Collects staged + unstaged + untracked changes, parses diffs, writes per-file `changed_ranges`.
- [ ] 2.1.2 **Extract units + compute has_changes** — Run:
    ```bash
        python3 {SKILL_ROOT}/scripts/extract-units.py OUTPUT_PATH/review-input.json
    ```
  - Updates the JSON in place: fills `files[].units` with `{name, kind, line_start, line_end, has_changes}` and recomputes `summary.total_units` / `summary.changed_units`.
  - `has_changes` is `true` if any `changed_range` overlaps the unit's line span, else `false`. For files with null/empty `changed_ranges` (untracked), all units are `has_changes: true`.
  - Do NOT do this work by hand / via inline Python. If extract-units fails, fix the script instead of bypassing it.
- [ ] 2.1.3 **Match tags** — Read OUTPUT_PATH/review-input.json, examine `detected_imports` + the source files, merge matched tags into `matched_tags` (see Tag Matching).
- [ ] 2.1.4 **Write matched_tags back** — Update `matched_tags` in the JSON.

#### Phase 2.2: Folder
- [ ] 2.2.1 **Discover .swift files** — Glob the folder recursively.
- [ ] 2.2.2 **Write initial review-input.json** — Build `files[]` with each path and `changed_ranges: null`. Set `source_type: "folder"`. Then run `extract-units.py OUTPUT_PATH/review-input.json` to fill units (all `has_changes: true`).
- [ ] 2.2.3 **Match tags** — See Tag Matching.

#### Phase 2.3: File
- [ ] 2.3.1 **Write initial review-input.json** — `files: [{file_path: <path>, changed_ranges: null, units: []}]`, `source_type: "file"`. Run `extract-units.py` to fill units.
- [ ] 2.3.2 **Match tags** — See Tag Matching.

#### Phase 2.5: Files (explicit file list)
- [ ] 2.5.1 **Parse file list** — JSON array or space-separated paths.
- [ ] 2.5.2 **Write initial review-input.json** — One entry per file with `changed_ranges: null`. Set `source_type: "files"`. Run `extract-units.py`.
- [ ] 2.5.3 **Match tags** — See Tag Matching.

#### Phase 2.4: Buffer
- [ ] 2.4.1 **Write initial review-input.json** — Put the input string in `buffer.input`, `source_type: "buffer"`. Run `extract-units.py` to fill `buffer.units`.
- [ ] 2.4.2 **Match tags** — See Tag Matching.

### Phase 3: Assembly & Output
- [ ] 3.1 **Extract imports** (for folder/file/buffer modes) — Scan the loaded source code for `import <ModuleName>` statements. Collect unique module names into `detected_imports` array (sorted). For changes mode, the script already handles this.
- [ ] 3.2 **Write structured output** - using defined schema write to `OUTPUT_PATH/review-input.json` (include `detected_imports` and `matched_tags`)
- [ ] 3.3 **Validate output** — Run schema validation on the written file:
  ```bash
  python3 {SKILL_ROOT}/scripts/validate-output.py OUTPUT_PATH/review-input.json {SKILL_ROOT}/output.schema.json
  ```
  If validation fails, read the error message, fix the JSON to match the schema, re-write, and re-validate.

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

Handled by `scripts/extract-units.py`. The script finds every top-level `class`, `struct`, `protocol`, `enum`, `extension` declaration in each Swift source file and emits `{name, kind, line_start, line_end, has_changes}`. `line_end` is the line before the next unit (or end-of-file for the last unit).

Do not re-implement this logic in the agent's prompt or via inline Bash heredocs — always call the script.

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
