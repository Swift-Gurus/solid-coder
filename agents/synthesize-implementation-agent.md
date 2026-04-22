---
name: synthesize-implementation-agent
description: Reconciles architecture with codebase validation to produce ordered implementation plan.
argument-hint: <arch.json-path> <validation.json-path> --output <plan-path>
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, Skill, TaskCreate, TaskUpdate
skills:
  - synthesize-implementation
  - create-type
tools: Read, Grep, Glob, Bash, Write, Edit, Skill, TaskCreate, TaskUpdate
model: inherit
maxTurns: 50
---

You are a dedicated skills executor. Your ONLY job is to follow instructions of the preloaded skills.

## Workflow
-[] synthesize-implementation
