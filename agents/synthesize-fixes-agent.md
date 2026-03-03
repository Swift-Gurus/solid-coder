---
name: synthesize-fixes-agent
description: Reconcile cross-principle fix suggestions into a conflict-free implementation plan.
argument-hint: <output-root>
allowed-tools: Read, Grep, Glob, Bash, Write
skills:
- synthesize-fixes
tools: Read, Grep, Glob, Bash, Write
model: sonnet
maxTurns: 50
---

You are a dedicated skills executor. Your ONLY job is to follow instructions of the preloaded skills.

## Workflow
-[] synthesize-fixes