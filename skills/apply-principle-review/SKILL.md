---
name: apply-principle-review
description: Generic code review that reads principle rules and follows review instructions. Internal skill — triggered by subagents only.
argument-hint: <principle-folder> <code-files>
allowed-tools: Read, Grep, Glob, Bash
user-invocable: false
---

# Generic Code Review

## Input
- RULES_PATH: ${CLAUDE_PLUGIN_ROOT}/references
- INPUT_SCHEMA: ${CLAUDE_PLUGIN_ROOT}/skills/prepare-review-input/output.schema.json
- NAME: $ARGUMENTS[0] (e.g., SRP,OCP)
- OUTPUT_PATH: $ARGUMENTS[1] - output root if not provided use CURRENT_PROJECT/.solid-coder-<YYYYMMDDhhmmss>
- Code files: path to json follows INPUT_SCHEMA

## Workflow
## Phase 1
Create Preparation task list and execute it
- [ ] 1.1 **Create output folder** - Create folder FOLDER == `OUTPUT_PATH/NAME`
- [ ] 1.2 **Load instructions** — Read `RULES_PATH/NAME/review/instructions.md`
- [ ] 1.3 **Parse frontmatter** — Extract `rules` and `output_schema` paths.
  - substitute PRINCIPLE_FOLDER_ABSOLUTE_PATH with {RULES_PATH}/{NAME} 
  - if rules are not provided use PRINCIPLE_FOLDER_ABSOLUTE_PATH/ruler.md path as fallback
- [ ] 1.4 **Load rules** — Read the rules file referenced in frontmatter
- [ ] 1.5 **Load patterns** — Parse `required_patterns` from rule.md frontmatter. For each entry, read `{RULES_PATH}/design_patterns/{entry}.md`
- [ ] 1.6 **Parse input** -
  - read and parse input json
  - extract files and units from json 
## Phase 2
FOR each file DO
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
- [ ] 3.2 **Generate output** — Produce structured outuput matching the output schema, write to created FOLDER `review-output.json`

## Constraints
- Do NOT invent rules — only apply what is in the rules file
- Do NOT merge or skip checklist steps
- Report one finding per triggered metric
- Do NOT auto-resolve issues in the workflow: 
  - if input doesnt match schema or unrecognized input -> fail with a message
  - if files are not found -> fail with a message
  - if instructions are not found -> fail with a message
  - if rules are not found -> fail with a message


