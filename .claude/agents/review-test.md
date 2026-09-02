---
name: review-test
description: Review agent to validate code rules
argument-hint: <code-files>
allowed-tools: Read, Grep, Glob, Bash, Write, Skill, ToolSearch, mcp__plugin_solid-coder_flow-engine__flow_start, mcp__plugin_solid-coder_flow-engine__flow_next
tools: Read, Grep, Glob, Bash, Write, Skill, ToolSearch, mcp__plugin_solid-coder_flow-engine__flow_start, mcp__plugin_solid-coder_flow-engine__flow_next
model: sonnet
---

- Read the file
- run flow_start tool with flow name: solid-file-review-single-prompt
