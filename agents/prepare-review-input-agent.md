--- 
name: prepare-review-input-agent
description: Generic Skill Wrapper, to allow skill to be run in parallel.
allowed-tools: Read, Grep, Glob, Bash, Write
skills:
- prepare-review-input
tools: Read, Grep, Glob, Bash, Write, mcp__plugin_solid-coder_pipeline__get_output_path
model: haiku
---

