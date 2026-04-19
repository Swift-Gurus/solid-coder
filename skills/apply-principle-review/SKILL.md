---
name: apply-principle-review
description: Generic code review that reads principle rules and follows review instructions. Internal skill — triggered by subagents only.
argument-hint: <principle-folder> <code-files>
allowed-tools: Read, Grep, Glob, Bash, Write
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
- [ ] 1.2 **Load rules** — Run:
  `! python3 ${CLAUDE_PLUGIN_ROOT}/mcp-server/gateway.py load_rules --mode review --principle NAME`
  - This returns the rule content, review instructions, examples, and design patterns for this principle
  - Parse JSON output. If `errors` is non-empty → fail with the error
  - Store `rules[NAME]` — contains `rule`, `instructions`, `examples`, `patterns`
- [ ] 1.3 **Parse input** -
  - read and parse input json
  - extract the list of files and their units (paths, line ranges, has_changes flags)
  - Do NOT read the source code files here — source files are read one at a time in Phase 2
## Phase 2
Process files **one at a time** — do NOT read all source files upfront.

FOR each file in review-input DO
  - [ ] 2.1 **Read the source file NOW** — Read only this file's source code. Do NOT read other files yet.
  FOR each unit (class, struct, enum) in file.units that has_changes == true DO
    Creating/appending tasks from the instructions.
    Once you read instructions and rules, they might contain more tasks.
    Create a second tasklist and execute it
    IMPORTANT: Scope analysis to ONLY this unit's line range (line_start..line_end).
    Ignore other declarations in the same file.
  END
END


## Phase 3
Creating output.
- [ ] 3.1 **Load output schema** — Read the schema file referenced in frontmatter
- [ ] 3.2 **Generate output** — Produce structured output matching the output schema, write to created FOLDER `review-output.json`
- [ ] 3.3 **Validate output** — Run:
  `! python3 ${CLAUDE_PLUGIN_ROOT}/mcp-server/gateway.py validate_phase_output --json-path FOLDER/review-output.json --schema-path {principle_folder}/review/output.schema.json`
  If validation fails, read the error, fix the output JSON, re-write, and re-validate.

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


