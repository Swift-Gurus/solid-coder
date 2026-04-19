---
name: test-preload-rules
description: Experiment — spin a code-agent subagent with pre-loaded rules injected via ! substitution. Verifies rules-in-prompt eliminates the subagent's own load_rules call.
argument-hint: [mode] [tags]
allowed-tools: Bash, Skill
user-invocable: true
---

# Test Pre-Loaded Rules Injection

## Phase 1: Spawn code-agent with the prompt

- [ ] 1.1 Prepare a Task call:
  - subagent_type: `solid-coder:test-preload-probe-agent`
  - prompt: "TASK: Quote the SC-1 rule from your pre-loaded rules, verbatim. Do NOT call any tools — just answer from context. If SC-1 isn't present, say 'NOT FOUND'."
- [ ] 1.2 Launch Task

## Phase 2: Report

- [ ] 2.1 Report the subagent's final text output verbatim.
- [ ] 2.2 Report whether the subagent called any tools during its run (look at `tool_uses` count in the Task result).
- [ ] 2.3 Outcome interpretation:
  - Quotes SC-1 correctly, 0 tool uses → **PASS** (pre-load works)
  - Says "NOT FOUND" → rules didn't reach the subagent's context
  - Called `load_rules` anyway → pre-load notice was too weak
