---
name: load-reference
description: Load reference files with frontmatter stripped. Accepts file paths and directories. Internal skill — used by other skills to load clean rule/pattern/example content.
argument-hint: <path> [<path> ...]
allowed-tools: Bash
user-invocable: false
---

# Load Reference

## Input
- PATHS: $ARGUMENTS — one or more file paths or directories to load

## Workflow

- [ ] 1.1 **Run loader script** — Execute:
  ```
  python3 ${CLAUDE_PLUGIN_ROOT}/skills/load-reference/scripts/load-reference.py <PATHS>
  ```
- [ ] 1.2 **Return output** — The script outputs each file's content (frontmatter stripped) to stdout, separated by `=== <path> ===` headers.

## Constraints
- NEVER truncate the output — no `head`, `tail`, `| head -N`, or line limits. The full content of every file must be returned. Truncated rules lead to missed constraints and violations.

## Output
Clean content from each file, with YAML frontmatter removed. Directories are expanded to all files within them.
