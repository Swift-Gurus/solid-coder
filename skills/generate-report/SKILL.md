---
name: generate-report
description: Generate a self-contained HTML report from validated per-file findings and fix suggestions.
argument-hint: <output-root>
allowed-tools: Bash
user-invocable: false

---

# HTML Report Generator

## Input
- OUTPUT_ROOT: $ARGUMENTS[0] — review output directory (e.g., `.solid_coder/review-20260227103000/`)
- SKILL_ROOT: ${CLAUDE_PLUGIN_ROOT}/skills/generate-report

## Workflow
- [ ] 1.1 Run:
    ```bash
        python3 {SKILL_ROOT}/scripts/generate-report.py {OUTPUT_ROOT}
    ```
- [ ] 1.2 Report the path to the generated HTML: `{OUTPUT_ROOT}/report.html`
