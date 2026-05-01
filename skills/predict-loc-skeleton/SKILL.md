---
name: predict-loc-skeleton
description: Draft a behavioural skeleton of the spec in the project's language with real per-AC logic, count LOC, and project total implementation size. Internal skill — invoked by validate-spec Phase C.
argument-hint: <spec-path> <output-dir>
allowed-tools: Read, Glob, Bash, Write
user-invocable: false
---

# Predict LOC — Skeleton

## Input

- SPEC_PATH: `$ARGUMENTS[0]` — absolute path to the spec's `Spec.md`
- OUTPUT_DIR: `$ARGUMENTS[1]` — absolute path to the output directory. The skill writes `skeleton.json` there and stores skeleton files under `{OUTPUT_DIR}/skeleton/`.

## Workflow

### Phase 1 — Detect language

- [ ] 1.1 Determine the dominant source language of the project containing the spec:
    ```bash
    PROJECT_ROOT=$(git -C "$(dirname {SPEC_PATH})" rev-parse --show-toplevel 2>/dev/null || dirname {SPEC_PATH})
    find "$PROJECT_ROOT" -type f \( -name "*.swift" -o -name "*.kt" -o -name "*.kts" -o -name "*.ts" -o -name "*.tsx" -o -name "*.py" \) -not -path "*/.*" | sed -E 's/.*\.([^.]+)$/\1/' | sort | uniq -c | sort -rn | head -5
    ```
- [ ] 1.2 Map the dominant extension to a language:

    | Extension(s) | Language | Multiplier |
    |---|---|---:|
    | `.swift` | Swift | 1.15 |
    | `.kt`, `.kts` | Kotlin | 1.10 |
    | `.ts`, `.tsx` | TypeScript | 1.10 |
    | `.py` | Python | 1.20 |

    The multiplier is small because the skeleton already contains real logic — it covers minor production overhead (extensions, conformance scaffolding, accessor synthesis) that the agent typically omits.

- [ ] 1.3 If no extension dominates or the project is empty, default to **Swift**.

### Phase 2 — Sketch the skeleton

- [ ] 2.1 Read the spec file in full.
- [ ] 2.2 Identify the types, protocols, and methods the spec implies — drawn from `## Technical Requirements`, `## Connects To`, and behaviors described in `## User Stories`.
- [ ] 2.3 Create the output directory: `mkdir -p {OUTPUT_DIR}/skeleton`.
- [ ] 2.4 Write files under `{OUTPUT_DIR}/skeleton/` in the detected language. **Rules:**
    - One file per top-level type, named after the type.
    - Include type signatures: properties (with types), method/function signatures, protocol/interface members.
    - **Bodies contain real logic — what the AC actually requires.** Naive implementations are fine; no optimisation. The point is to capture per-method complexity (a retry loop is genuinely more LOC than a getter).
    - Error handling only when an AC explicitly calls for it.
    - Imports are real (they're real LOC).
    - No tests — tests scale separately and are excluded from the production-LOC metric.
    - No comments beyond what is structurally required.
    - No defensive checks the ACs do not require.
    - If the spec implies multiple conformers, sketch each as its own file.
- [ ] 2.5 If a type or behavior cannot be sketched because the spec is too vague, note it in the output's `unsketched` array — do NOT invent behavior the spec does not describe.

### Phase 3 — Count and project

- [ ] 3.1 Count non-blank, non-comment lines across the skeleton files:
    ```bash
    find {OUTPUT_DIR}/skeleton -type f | xargs grep -cv '^\s*$\|^\s*//\|^\s*#' | awk -F: '{sum += $2} END {print sum}'
    ```
- [ ] 3.2 Compute `projected_loc = round(skeleton_loc × multiplier)`.
- [ ] 3.3 Map `projected_loc` to the band table from [README § Scope Metrics](../../spec-driven-development/specs/README.md#scope-metrics):
    - `< 200` → COMPLIANT
    - `200 – 400` → MINOR
    - `> 400` → SEVERE

### Phase 4 — Emit JSON

- [ ] 4.1 Write `{OUTPUT_DIR}/skeleton.json` matching `output.schema.json`. Include `skeleton_loc`, `language`, `multiplier_used`, `projected_loc`, `severity`, `skeleton_files` (relative paths under `{OUTPUT_DIR}/skeleton/`), `unsketched` (if any), and `spec_path`.

## Output

`{OUTPUT_DIR}/skeleton.json` matching `output.schema.json`. The skeleton files themselves are intermediate artifacts — useful for debugging but not consumed by downstream skills.

## Constraints

- Do NOT optimise or harden the impl — naive logic is fine. The skeleton is sized, not run.
- Do NOT write tests — tests are excluded from the production-LOC metric.
- Do NOT invent types or behaviors the spec doesn't imply. If the spec is too vague to sketch, flag it in `unsketched` and let the buildability checks (Phase B) catch the underspecification.
- Do NOT modify the spec file or anything outside `{OUTPUT_DIR}`.
