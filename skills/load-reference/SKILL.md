---
name: load-reference
description: Load principle rules via gateway and internalize them as active constraints. Internal skill — used by other skills before writing code or making architectural decisions.
argument-hint: --mode <code|review|planner|synth-impl|synth-fixes> [--principle <name>] [--matched-tags <tags>]
allowed-tools: Bash
user-invocable: false
---

# Load & Internalize Rules

Loads principle rules via the gateway and forces you to process them before acting.

## Input
- GATEWAY: ${CLAUDE_PLUGIN_ROOT}/mcp-server/gateway.py
- MODE: `--mode` value — one of `code`, `review`, `planner`, `synth-impl`, `synth-fixes`. Resolves profile + exclude + review-content stripping from `mcp-server/modes.py`.
- PRINCIPLE: (optional) `--principle` value — load one principle by name (e.g., `srp`)
- MATCHED_TAGS: (optional) `--matched-tags` value — comma-separated tags to filter principles

## Workflow

- [ ] 1.1 **Run gateway** — Execute exactly with the caller's `--mode` value (do NOT translate to `--profile`):
  ```
  python3 {GATEWAY} load_rules --mode {MODE} [--principle {PRINCIPLE}] [--matched-tags {MATCHED_TAGS}]
  ```
  The mode determines what gets loaded AND whether review-only content (Detection/Scoring/Severity/Result blocks) is stripped. Non-review modes get stripped output.

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
