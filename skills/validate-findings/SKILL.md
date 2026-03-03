---
name: validate-findings
description: Filter findings to changes only and reorganize outputs by file for implementation.
argument-hint: <output-root>
allowed-tools: Bash
user-invocable: false
---

# Findings Validator

## Input
- OUTPUT_ROOT: $ARGUMENTS[0] — review output directory (e.g., `.solid_coder/review-20260227103000/`)

## Workflow
- [ ] 1.1 Run: `python3 ${SKILL_DIR}/validate-findings.py {OUTPUT_ROOT}`
- [ ] 1.2 Report the output summary and list files in `{OUTPUT_ROOT}/by-file/`
