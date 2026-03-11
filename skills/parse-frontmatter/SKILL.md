---
name: parse-frontmatter
description: Parse YAML frontmatter from a markdown file and return structured JSON with resolved paths. Internal skill — used by other skills and instructions to load metadata.
argument-hint: <file-path>
allowed-tools: Bash, Read
user-invocable: false
---

# Parse Frontmatter

## Input
- FILE_PATH: $ARGUMENTS[0] — path to a `.md` file with YAML frontmatter

## Workflow

- [ ] 1.1 **Run parser script** — Execute:
  ```
  python3 ${CLAUDE_PLUGIN_ROOT}/skills/parse-frontmatter/scripts/parse-frontmatter.py <FILE_PATH>
  ```
- [ ] 1.2 **Return JSON** — The script outputs JSON to stdout. Return it as the skill result.

## Output
JSON object containing all frontmatter fields with:
- Path fields (`rules`, `output_schema`, `input_schema`, `examples`) resolved to absolute paths relative to the file's directory
- `required_patterns` resolved to absolute paths under `<grandparent>/design_patterns/` (auto-detected from file location)
- `PRINCIPLE_FOLDER_ABSOLUTE_PATH` tokens replaced with the actual parent directory
- `_source`: absolute path of the parsed file
- `_dir`: absolute path of the file's parent directory

## Error Handling
- Missing file → exit 1 with error message
- No frontmatter found → exit 1 with error message
- Invalid YAML → exit 1 with error message
