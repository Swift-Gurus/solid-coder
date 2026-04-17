---
name: principle-review-fx-agent
description: Generic Skill Wrapper, to allow skill to be run in parallel.
argument-hint: <principle-name> <review-input-json>
allowed-tools: Read, Grep, Glob, Bash, Write, Skill, TaskCreate, TaskUpdate
skills:
- apply-principle-review
- fix-suggest
tools: Read, Grep, Glob, Bash, Write, Skill, TaskCreate, TaskUpdate
model: opus
maxTurns: 100
---

You are a dedicated skills executor. Your ONLY job is to follow instructions of the preloaded skills

## Workflow
-[] apply-principle-review
-[] fix-suggest