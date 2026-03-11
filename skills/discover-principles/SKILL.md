---
name: discover-principles
description: Discover principles from references directory and filter by matched tags from review-input.json.
argument-hint: --refs-root <path> [--review-input <path>] [--matched-tags <tags>]
allowed-tools: Bash, Read
user-invocable: false
---

# Discover Principles

Discover all principles in the references directory and optionally filter by tags.

## Execution

```bash
! python3 ${CLAUDE_PLUGIN_ROOT}/skills/discover-principles/scripts/discover-principles.py $ARGUMENTS
```

## Arguments

- `--refs-root <path>` — **(required)** Path to references directory
- `--review-input <path>` — Path to review-input.json (reads `matched_tags` from it for filtering)
- `--matched-tags <tags>` — Comma-separated list of tags to filter by
- `--glob <pattern>` — Custom glob pattern (default: `*/rule.md`)

## Modes

### Discovery (no filter args)
Returns all principles + `all_candidate_tags`. No principles are skipped.

### Filter (with `--review-input` or `--matched-tags`)
- No `tags` in rule.md → always active
- Has `tags` → active only if any tag intersects with matched tags

## Output

```json
{
  "all_candidate_tags": ["swiftui", "tca", "ui"],
  "active_principles": [
    {
      "name": "srp",
      "displayName": "Single Responsibility Principle",
      "folder": "/abs/path/references/SRP",
      "rule_path": "/abs/path/references/SRP/rule.md",
      "tags": null
    }
  ],
  "skipped_principles": [
    {
      "name": "swiftui-views",
      "folder": "...",
      "tags": ["swiftui"],
      "reason": "no matching tags"
    }
  ]
}
```

## How Tags Work

- Rules without `tags` in frontmatter are **always active** (core principles like SRP, OCP, LSP, ISP)
- Rules with `tags` are **conditionally active** — only when the code matches at least one tag
- Tags are matched case-insensitively
- Tag matching is done by the prepare-review-input agent, which analyzes imports + code patterns
