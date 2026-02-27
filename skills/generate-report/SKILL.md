---
name: generate-report
description: Generate a self-contained HTML report from SOLID review findings and fix suggestions.
argument-hint: <review-output-directory>
allowed-tools: Read, Glob, Write
---

# HTML Report Generator

## Input
- OUTPUT_DIR: $ARGUMENTS[0] — path to the review output directory (e.g., `.solid_coder/review-20260227103000/`)
- TEMPLATE: ${SKILL_DIR}/template.html

## Phase 1: Discover Outputs
- [ ] 1.1 Glob for `OUTPUT_DIR/**/review-output.json`
- [ ] 1.2 For each found `review-output.json`, check if a sibling `fix.json` exists in the same directory
- [ ] 1.3 Build a list of tuples: `{ principle_dir, review_path, fix_path | null }`
- [ ] 1.4 If no review-output.json files found → fail with message: "No review outputs found in {OUTPUT_DIR}"

## Phase 2: Read & Normalize JSON
- [ ] 2.1 For each tuple, read `review-output.json` and `fix.json` (if exists)
- [ ] 2.2 All review schemas use the same `files[]` structure. For each principle collect:
  - `principle_name` — from JSON `principle` field
  - `agent` — from JSON `agent` field
  - `files[]` — each entry has `{ file, scoring.final_severity, findings[] }`
  - `suggestions[]` — from fix.json (empty array if no fix.json)

## Phase 3: Generate HTML
- [ ] 3.1 Read TEMPLATE file
- [ ] 3.2 Use the template as the base HTML structure (keep all CSS and markup intact)
- [ ] 3.3 Populate the template sections with collected data following the comment placeholders in the template
- [ ] 3.4 Write the final HTML to `OUTPUT_DIR/report.html`

### Rendering Rules

1. **Badge classes**: lowercase severity → CSS class (`SEVERE` → `badge-severe`, `IMPORTANT` → `badge-severe`)
2. **HTML escape** all JSON string values (`<`, `>`, `&`, `"`)
3. **Code blocks**: strip markdown fences from `suggested_fix`, place content in `<div class="code-block">`
4. **Missing fields**: skip the HTML element, don't render empty containers
5. **File paths**: show filename only in `.file-label`, full path in `title` attribute
6. **Worst severity**: for multi-file principles, use worst `final_severity` in the summary row

## Constraints
- Do NOT modify source code files or review JSONs
- Do NOT add JavaScript — pure HTML + CSS only
- If a review-output.json fails to parse, skip that principle and note it in the report
- If OUTPUT_DIR has no review outputs, fail with a clear error message
