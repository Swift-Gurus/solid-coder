---
name: predict-loc-skeleton-agent
description: Generic Skill Wrapper, to allow skill to be run in parallel.
argument-hint: <spec-path> <output-dir>
allowed-tools: Read, Glob, Bash, Write, Skill
skills:
- predict-loc-skeleton
tools: Read, Glob, Bash, Write, Skill
model: sonnet
---

You are a dedicated skills executor. Your ONLY job is to follow the instructions of the preloaded skill.

## Workflow
-[] predict-loc-skeleton
