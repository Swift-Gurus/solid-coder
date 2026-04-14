---
name: load-reference
description: Load principle rules via gateway and internalize them as active constraints. Internal skill — used by other skills before writing code or making architectural decisions.
argument-hint: --profile <review|code> [--principle <name>] [--matched-tags <tags>]
allowed-tools: Bash
user-invocable: false
---

# Load & Internalize Rules

Loads principle rules via the gateway and forces you to process them before acting.

## Input
- GATEWAY: ${CLAUDE_PLUGIN_ROOT}/mcp-server/gateway.py
- PROFILE: `--profile` value — `review` or `code`
- PRINCIPLE: (optional) `--principle` value — load one principle by name (e.g., `srp`)
- MATCHED_TAGS: (optional) `--matched-tags` value — comma-separated tags to filter principles

## Workflow

- [ ] 1.1 **Run gateway** — Execute:
  ```
  python3 {GATEWAY} load_rules --profile {PROFILE} [--principle {PRINCIPLE}] [--matched-tags {MATCHED_TAGS}]
  ```
  This outputs the full rule content as readable text — rules, instructions, examples, code rules, and design patterns for each active principle.

- [ ] 1.2 If the command fails → report the error and stop.

- [ ] 1.3 **Read every principle section in full.** Do NOT skim, summarize, or "scan at summary level." Each principle section contains:
  - **RULE** — metric IDs, thresholds, severity bands, and exceptions. You must know the exact numbers.
  - **INSTRUCTIONS** — detection checklists or fix patterns. You must follow them step by step.
  - **CODE RULES** — hard coding constraints. Every line of code must satisfy them.
  - **EXAMPLES** — compliant and violation code. Study both — the violation patterns show what NOT to do.
  - **DESIGN PATTERNS** — recognition conditions (e.g., facade: all-protocol deps + pure delegation + no internal construction).

  If the output contains 8 principles, you read all 8 in full. There is no shortcut.

## Constraints
- NEVER truncate the output — the full content of every principle must be read
- NEVER skim or summarize rules — read every metric, every threshold, every exception. "Summary level" is a violation of this skill.
- NEVER say "I've read X and Y, let me scan the rest" — that means you are skipping. Read ALL of them at the same depth.
- The loaded rules are the source of truth — do NOT invent additional rules or expand exception lists beyond what's explicitly defined
