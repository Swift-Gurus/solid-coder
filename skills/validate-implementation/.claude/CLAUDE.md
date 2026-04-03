---
number: n/a
feature: validate-implementation
status: done
---

# validate-implementation

## Purpose

Post-implementation checkpoint that gates the expensive refactor phase. Reads the full pipeline context (spec, arch, validation, plan), verifies completeness against what was planned, and collects user feedback with screenshots for visual verification. The key insight: LLMs cannot reliably compare a design image against code — they must compare image vs image.

## Inputs / Outputs

| Direction | What | Format |
|-----------|------|--------|
| Input | Output root directory | Path containing spec.md, arch.json, validation.json, implementation-plan.json, resources/ |
| Input | User screenshots | Images provided via AskUserQuestion |
| Input | User feedback | Text provided via AskUserQuestion |
| Output | Fix plan | JSON at `{OUTPUT_ROOT}/design-fix-plan.json` (implementation-plan schema) |
| Output | Status | `approved`, `has_fixes`, `skipped`, or `stopped` |

## Flow

```
Phase 1: Load context (spec, arch, plan, resources)
    ↓
Phase 2: Verify completeness (components exist? plan items done? criteria met?)
    ↓
Phase 3: Visual validation (if UI — ask user for screenshots, compare images)
    ↓
Phase 4: Present findings, collect user feedback
    ↓ approved → return
    ↓ has issues → Phase 5
Phase 5: Produce fix plan (implementation-plan format), user confirms
    ↓
Phase 6: Write design-fix-plan.json
```

## Connects To

| Skill/Agent | Relationship |
|-------------|-------------|
| `/implement` | Called inline at Phase 4.5, between code and refactor |
| `code-agent` | Consumes `design-fix-plan.json` (implementation-plan format) via `mode: implement`. Rules load from `matched_tags`. |

## Design Decisions

- **Full pipeline context** — reads spec, arch, validation, and plan. Not just the plan. This catches missing components, unfollowed reuse decisions, and unmet acceptance criteria.
- **Image vs image, never image vs code** — the LLM cannot mentally render SwiftUI code to compare against a screenshot. It must see both images.
- **User in the loop** — the user builds, runs, and screenshots. No build automation dependency.
- **Gate before refactor** — fixes design/completeness issues (cheap, targeted) before running the expensive SOLID review.
- **Confirm directives** — user picks which differences to fix vs which are intentional.
- **Three verification layers**: completeness (do components exist?), criteria (are requirements met?), visual (does it look right?).