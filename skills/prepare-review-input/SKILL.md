---
name: prepare-review-input
description: Normalize input (branch diff, folder, class, buffer) into structured review-input.json for review agents.
argument-hint: [folder|class|buffer] [target] [--base <branch>]
allowed-tools: Read, Grep, Glob, Bash, Write
user-invocable: true
---

# Prepare Review Input

## Input
- SOURCE_TYPE: $ARGUMENTS[0] — one of: branch, changes, folder, file, buffer
  - If $ARGUMENTS[0] is not a known type you must stop and show an error message. Unknown Type
  - If NO arguments provided → default to branch diff (current branch vs base)
- OUTPUT_ROOT: $ARGUMENTS[1] - output root if not provided use CURRENT_PROJECT/.solid-coder-<YYYYMMDDhhmmss>
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
  - if the file has no changed_ranges → has_changes = true
  - if the file has changed_ranges  →
       check if ANY changed_range overlaps with [unit.line_start, unit.line_end].
       Overlap = range.start <= unit.line_end AND range.end >= unit.line_start.
       If overlap exists → has_changes = true, otherwise → has_changes = false
- [ ] 2.1.5 **Update JSON** — Write units back into `OUTPUT_PATH/review-input.json` and update summary counts

#### Phase 2.2: Folder
- [ ] 2.2.1 **Read all files**

#### Phase 2.3: File
- [ ] 2.3.1 **Read the file**

#### Phase 2.4: Buffer
- [ ] 2.4.1 **Capture buffer string** — Store raw input

### Phase 3: Assembly & Output
- [ ] 3.1 **Write structured output** - using defined schema write to `OUTPUT_PATH/review-input.json`

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

## Constraints
- Do NOT modify any source files
- Do NOT write buffer input to a separate file — keep it in the JSON
- Do NOT resolve any issues with the workflow, if anything fails:
  - file not found
  - will consume too many tokens > 200k
  You fail with a message
