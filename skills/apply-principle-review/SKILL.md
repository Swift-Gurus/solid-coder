---
name: apply-principle-review
description: Generic code review that reads principle rules and follows review instructions. Internal skill — triggered by subagents only.
argument-hint: <principle-folder> <code-files>
allowed-tools: Read, Grep, Glob, Bash, Write, mcp__plugin_solid-coder_docs__load_rules, mcp__plugin_solid-coder_docs__load_detection_rules, mcp__plugin_solid-coder_docs__load_fix_for_violation, mcp__plugin_solid-coder_pipeline__submit_findings, mcp__plugin_solid-coder_pipeline__submit_batch_findings, mcp__plugin_solid-coder_pipeline__submit_fix
user-invocable: false
---

# Generic Code Review

## Input
- INPUT_SCHEMA: ${CLAUDE_PLUGIN_ROOT}/skills/prepare-review-input/output.schema.json
- NAME: $ARGUMENTS[0] (e.g., SRP,OCP)
- OUTPUT_PATH: $ARGUMENTS[1] - output root if not provided use CURRENT_PROJECT/.solid-coder-<YYYYMMDDhhmmss>
- Code files: path to json follows INPUT_SCHEMA

## Workflow
## Phase 1
Create Preparation task list and execute it
- [ ] 1.1 **Create output folder** - Create folder FOLDER == `OUTPUT_PATH/NAME`
- [ ] 1.2 **Load principle rules** — call `mcp__plugin_solid-coder_docs__load_detection_rules` with `principle: NAME`. The tool returns structured per-metric detection instructions and definitions when the principle has XML detection blocks in rule.md. If the principle has no XML detection blocks, it falls back to returning the full rule.md content — apply whichever form is returned throughout Phase 2.
- [ ] 1.3 **Parse input** -
  - read and parse input json
  - extract the list of files and their units (paths, line ranges, has_changes flags)
  - Do NOT read the source code files here — source files are read one at a time in Phase 2
## Phase 2
Process files **one at a time** — do NOT read all source files upfront.

FOR each file in review-input DO
  - [ ] 2.1 **Read the source file NOW** — Read only this file's source code. Do NOT read other files yet.
  FOR each unit (class, struct, enum) in file.units that has_changes == true DO
    - [ ] Apply the rules loaded in Phase 1.2 to this unit
    - [ ] Scope analysis to ONLY this unit's line range (line_start..line_end). Ignore other declarations.
  END
END


## Phase 3
Creating output.
- [ ] 3.1 **Read both schemas** — Read `${CLAUDE_PLUGIN_ROOT}/references/review-output.schema.json` (overall payload structure) and `${CLAUDE_PLUGIN_ROOT}/references/principles/NAME/review/output.schema.json` (required metric variables for this principle). The `<submission-metrics-example>` block in the detection rules already shows the correct shape.
- [ ] 3.2 **Submit findings** — Construct a partial output with `timestamp: ISO-8601 now` and `files: [...units with metrics: {NAME: {var: {value: N}}}]`. No `agent`, no `principle`, no `violations` in the submission — the server fills those. Call `mcp__plugin_solid-coder_pipeline__submit_findings` with `{partial_output: <document>, output_path: FOLDER/review-output.json}`. The server validates metrics against the per-principle schema, scores each metric via severity bands, writes the output file with `violations: [{rule_id, severity}]`, and returns a compact summary. Log the summary. Do NOT use the Write tool to write review-output.json directly.

## Constraints
- Do NOT invent rules — only apply what is in the rules file
- Do NOT expand exception lists — apply ONLY the exceptions explicitly defined in rule.md. If a dependency looks similar to a listed exception but does not match the stated criteria, it is NOT an exception. Do not justify exceptions by "well-known patterns" or common industry practice (e.g., "Logger is a helper", "Analytics is cross-cutting"). The rule defines what qualifies. Nothing else does.
- Do NOT merge or skip checklist steps
- Report one finding per triggered metric
- Do NOT auto-resolve issues in the workflow: 
  - if input doesnt match schema or unrecognized input -> fail with a message
  - if files are not found -> fail with a message
  - if instructions are not found -> fail with a message
  - if rules are not found -> fail with a message


