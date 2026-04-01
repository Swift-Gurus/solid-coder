--- 
name: apply-principle-review-agent
description: Generic Skill Wrapper, to allow skill to be run in parallel.
argument-hint: <principle-folder> <code-files>
allowed-tools: Read, Grep, Glob, Bash, Write
skills:
- apply-principle-review
tools: Read, Grep, Glob, Bash, Write
model: sonnet
---

