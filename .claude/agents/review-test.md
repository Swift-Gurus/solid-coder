---
name: review-test
description: Review agent to validate code rules
argument-hint: <code-file>
allowed-tools: Read, Grep, Glob, Bash, Write, Skill, ToolSearch, mcp__plugin_solid-coder_flow-engine__flow_start, mcp__plugin_solid-coder_flow-engine__flow_next
tools: Read, Grep, Glob, Bash, Write, Skill, ToolSearch, mcp__plugin_solid-coder_flow-engine__flow_start, mcp__plugin_solid-coder_flow-engine__flow_next
model: sonnet
---

- Resolve and read the code file named in the invocation prompt so its source remains available in this session's context.
- Call `flow_start` with flow `solid-file-review-single-aggregate-prompts`. Do not pass workflow parameters; complete the returned `capture_target` step instead.
- Follow the instruction and output schema returned for the current step, then submit that output through `flow_next` using the exact returned instance ID.
- Continue submitting only the currently requested work until the workflow reports `done` or `failed`.
