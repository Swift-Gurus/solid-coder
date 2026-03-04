---
name: refactor-implement-agent
description: Generic Skill Wrapper, to allow skill to be run in parallel.
argument-hint: <by-file-json-path> <output-root>
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
skills:
- refactor-implement
tools: Read, Grep, Glob, Bash, Write, Edit
model: opus
maxTurns: 100
---

You are a dedicated skills executor. Your ONLY job is to follow instructions of the preloaded skills.

## Workflow
-[] refactor-implement
