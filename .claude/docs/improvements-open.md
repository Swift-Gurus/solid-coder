# Open Improvement Suggestions

Suggestions that have not been implemented, need investigation, need POC validation, or are planned for the future.

Large architectural items (S-26, S-32, S-33, S-42, S-43, S-44) are in [@docs/improvements-open-arch.md](improvements-open-arch.md).

---

## S-05: Add post-synthesis verification script

**Impact**: Medium | **Effort**: Medium | **Category**: Reliability

**Status**: Deferred — scalability concern, iterative re-review is preferred

Phase 4 of synthesize-fixes asks the LLM to simulate other principles' metrics on proposed code. This is the weakest point — the LLM is likely to rubber-stamp its own output with `"passed": true`.

### Why deferred

Per-principle verification scripts don't scale. Each new rule (DIP, DRY, etc.) requires its own script with custom proxy checks (grep patterns, count heuristics) that are brittle and produce false positives/negatives. Maintenance burden grows linearly with rule count.

The iterative re-review approach (S-04) is the scalable alternative — after implementation, the same review agents re-check the changed files against all principles. This is principle-agnostic and reuses existing infrastructure rather than adding parallel validation scripts.

---

## S-09: Detect oscillation in iteration loop

**Impact**: Medium | **Effort**: Low | **Category**: Reliability

**Status**: Not implemented — low practical risk

If iteration 1 fixes issue A but introduces issue B, and iteration 2 fixes B but reintroduces A-like patterns, the loop oscillates without converging. In practice, the pipeline follows patterns properly and oscillation hasn't been observed. The real risk is when a fix modifies a caller site, which then gets re-reviewed in the next iteration and flagged for unrelated violations — this is more of a scoping problem (S-04) than oscillation.

**Suggestion**: In Phase 8 (Iteration Loop), before re-reviewing:

1. Compare finding IDs from iteration N vs iteration N-1. If >50% overlap → flag oscillation
2. Diff the source files against their pre-iteration-1 state. If net change is small (<10 lines divergence from original) → the iterations are undoing each other
3. If oscillation detected → stop, report both iterations' findings, let the developer decide

Also: log per-iteration finding IDs in the refactor-log.json so oscillation is visible in the output.

---


## S-16: CRITICAL BUG — validate-findings.py passes findings for unknown files

**Impact**: Critical | **Effort**: Low | **Category**: Correctness (bug)

In `validate-findings.py` line 253-260:

```python
cr = changed_lookup.get(file_path)
if cr is None or cr is True:
    passing.append(finding)  # BUG: treats "not in lookup" same as "null ranges"
```

`changed_lookup.get(file_path)` returns `None` for BOTH:
1. File has `null` changed_ranges (entire file is new) — correct to pass
2. File not in review-input at all — should be REJECTED

If a review agent reports findings in a file that wasn't in the review-input (hallucination or path mismatch), those findings pass through unfiltered.

**Fix**: Distinguish the two cases:
```python
if file_path not in changed_lookup:
    continue  # file not in review-input, reject
cr = changed_lookup[file_path]
if cr is None or cr is True:
    passing.append(finding)  # null = entire file new
```

---

## S-18: `file_path` vs `file` inconsistency across schemas

**Impact**: High | **Effort**: Medium | **Category**: Data contracts

- `prepare-review-input/output.schema.json`: uses `"file_path"`
- `SRP/review/output.schema.json`: uses `"file"`
- `validate-findings/file-output.schema.json`: uses `"file"`
- `synthesize-fixes/plan.schema.json`: uses `"file"`

The prepare agent writes `file_path`, the review agent reads it and outputs `file`. This works because the LLM adapts, but it's a latent bug — a stricter schema validator or a different LLM might fail.

**Fix**: Standardize on one name (`file_path` is more explicit). Update all schemas and all skills that reference the field.

### Verified status (2026-03-12)

**Not implemented — inconsistency confirmed.** Full inventory:

**Uses `file_path`:** `prepare-review-input/output.schema.json` (line 23), `prepare-changes.py` (line 150)

**Uses `file`:** All 5 review schemas (SRP, OCP, LSP, ISP, SwiftUI), all 5 fix schemas, `validate-findings/file-output.schema.json` (line 8), `synthesize-fixes/plan.schema.json` (line 8)

**Bridge code:** `validate-findings.py` reads `file_path` from review-input (line 103) and `file` from review output (line 162), outputs `file` (line 233). Works because the Python script manually maps between conventions.

**Plan:** Standardize on `file_path` everywhere (more descriptive). Update all 13 schema files + Python scripts.

---

## S-22: Missing JSON error handling in Python scripts

**Impact**: Medium | **Effort**: Low | **Category**: Robustness

`validate-findings.py` `load_json()` doesn't catch `json.JSONDecodeError`. Malformed JSON from a failed review agent causes an unhandled traceback instead of a clear error message.

Same applies to `generate-report.py`.

**Fix**: Wrap `json.load()` calls with try/except, print the file path and error, exit with code 1.

### Verified status (2026-03-12)

**Not implemented.** Four scripts have bare `json.load()`/`json.loads()` with no error handling:
1. `skills/validate-findings/scripts/validate-findings.py` — `load_json()` at line 35-37
2. `skills/validate-findings/scripts/check-severity.py` — line 44
3. `skills/generate-report/scripts/generate-report.py` — line 211
4. `mcp-server/lib/discover_principles.py` — line 195

Malformed JSON produces unhandled `json.JSONDecodeError` traceback instead of clean error.

**Plan:** Add try/except `json.JSONDecodeError` to each, print file path + error, `sys.exit(1)`.

---

## S-35: Pre-commit hook for frontmatter validation

**Impact**: Medium | **Effort**: Low | **Category**: Enforcement

**Status**: Pending — depends on S-33

Create `scripts/hooks/pre-commit` that runs `python scripts/registry.py --validate`. Blocks commits if any `Shared/` file is missing frontmatter. Three enforcement gates:

1. **Gate 1 — CC skill** (creation time) — DRY check + frontmatter prefill in `/code` skill
2. **Gate 2 — Pre-commit hook** (human-created files) — blocks commit
3. **Gate 3 — PR check** (CI) — same script, nothing merges without it

---

## S-37: Style rules separate pipeline — review-only, no fix generation

**Impact**: Medium | **Effort**: Medium | **Category**: Architecture

**Status**: Pending

Naming conventions, function smells, general code style do not fit the existing rule mechanics. No deterministic fix, no cross-principle synthesis. Feeding them into synthesize adds noise.

### Proposed structure

```
references/style/
  naming-conventions/
    rule.md              ← metrics + severity (MINOR only)
    review/
      instructions.md
      output.schema.json
    # NO fix/ folder — absence is the signal
    # NO refactoring.md
```

### Frontmatter flag

```yaml
---
name: naming-conventions
tier: style
severity-max: minor
synthesize: false    # explicit signal — skip fix generation
---
```

### Separate output contract

```json
{
  "solid_findings": [...],    // → synthesize → implement pipeline
  "style_findings": [...]     // → report only, no fix generation
}
```

`generate-report-agent` renders style findings as a separate section — observations, not actionable violations.

### Future style rules (planned)

- Naming conventions
- Function length / smells
- SwiftUI-specific style
- Concurrency patterns
- GCD usage guidelines

### Verified status (2026-03-12)

**Not implemented.** No concept of review-only rules exists anywhere:
- No `rule.md` frontmatter has `synthesize: false`, `fix: false`, or `review-only: true`
- `discover_principles.py` (in mcp-server/lib/) doesn't parse any such field
- `synthesize-fixes/SKILL.md` processes ALL non-COMPLIANT principles — no exclusion
- `generate-report.py` treats all findings uniformly — no fixable vs report-only distinction

**Plan:**
1. Add `fixable: false` (or `synthesize: false`) field to `rule.md` frontmatter for style rules
2. Update `mcp-server/lib/discover_principles.py` to expose this field
3. In `synthesize-fixes/SKILL.md` Phase 1.4, exclude non-fixable principles
4. In `generate-report/SKILL.md`, render non-fixable findings as separate "observations" section
5. In `refactor/SKILL.md` Phase 4.6, only count fixable findings for `MINOR_ONLY` vs `HAS_SEVERE`

---

## S-39: Skip empty plans — don't synthesize or implement when no changes needed

**Impact**: Medium | **Effort**: Low | **Category**: Pipeline efficiency

### Problem

The synthesizer writes plan files for every reviewed file, even when there are no actionable findings. The refactor orchestrator (Phase 7) then spawns implement agents for these empty plans, wasting agent invocations.

### Fix

Two levels:

1. **Synthesizer**: Do not write a `.plan.json` file if there are zero suggestions or zero `to_do` items for a file. No file = no implement agent spawned.
2. **Orchestrator fallback**: Before spawning an implement agent, check if the plan has any actions. Skip if empty.

Level 1 is preferred — it's cleaner to not produce empty artifacts than to filter them downstream.

---

## S-41: Local MCP server for `references/` — language-scoped principle loading

**Impact**: Medium | **Effort**: Medium | **Category**: Architecture

**Status**: Not implemented — would replace file-based `load-reference` with stdio MCP server; enables language namespacing (`principle://swift/SRP/rule`), server-side tag filtering, and partial section loading without reading whole files

---

## S-45: Design verification — structured pixel diff before refactor

**Impact**: High | **Effort**: High | **Category**: Pipeline enhancement

**Status**: POC needed — validate approach before committing

### Problem

`/implement` Phase 4.5 checks design compliance by having the LLM compare screenshots against code. The LLM checks for **presence** of elements ("app icon — present, title — present") but misses **visual accuracy** (spacing, alignment, colors, proportions). Result: "layout matches well" when the design is actually off.

### Why LLM-only comparison fails

- LLMs reason about structure, not pixels
- Comparing an image to code is fundamentally different from comparing two images
- "All elements present" ≠ "looks correct"

### Proposed solution: structured diff → LLM

Convert the visual comparison into structured data the LLM can reason about:

```
Design.png + Implementation.png
    ↓
compare-design.py (OpenCV / pixelmatch)
    ↓
{
  "match_percentage": 87.3,
  "diff_regions": [
    {
      "bounds": { "x": 20, "y": 150, "w": 300, "h": 50 },
      "diff_percentage": 34.2,
      "design_dominant_color": "#F5F5F5",
      "actual_dominant_color": "#FFFFFF"
    }
  ],
  "layout_shift": { "vertical_offset": 12, "horizontal_offset": 0 },
  "diff_image": "path/to/diff.png"
}
    ↓
LLM receives: design image + implementation image + diff image + structured JSON
    → Strong signals, not "does it look right?"
    → Outputs actionable fix directives
```

### Pipeline integration

New Phase 4.5 in `/implement`, between code and refactor:

1. Build target (`xcodebuild`)
2. Capture implementation screenshots (simulator or snapshot test)
3. Run `compare-design.py` → structured diff JSON + diff image
4. If `match_percentage` < threshold → LLM reads both images + diff data → fix directives
5. Feed fixes back to `/code` before refactor runs

### Screenshot capture options (need POC)

| Approach | Pros | Cons |
|---|---|---|
| `swift-snapshot-testing` (Point-Free) | Deterministic, works macOS+iOS, renders SwiftUI views | Needs test target, library dependency |
| `xcrun simctl io booted screenshot` | No library needed | Needs running simulator, app must be launched |
| Xcode preview rendering | Closest to dev workflow | Flaky, undocumented API |

### Comparison tool options (need POC)

| Tool | Output | Language |
|---|---|---|
| OpenCV (`cv2.absdiff` + `findContours`) | Bounding boxes, color histograms, edge comparison | Python |
| `pixelmatch` | Diff percentage + diff image | JS/Node |
| ImageMagick `compare` | Diff image, metrics | CLI |
| Resemble.js | JSON with mismatch %, bounding boxes | JS/Node |

### POC plan

1. Take 2-3 design screenshots from a recent `/implement` run
2. Manually capture implementation screenshots
3. Try OpenCV diff → evaluate quality of structured output
4. Try pixelmatch → evaluate quality
5. Feed structured diff to LLM → evaluate if fix directives are actionable
6. Compare against current LLM-only approach (Phase 4.5)

### Dependencies

- Build infrastructure (xcodebuild must work in the project)
- Screenshot capture mechanism (TBD from POC)
- OpenCV or similar (`pip install opencv-python numpy`)
- `swift-snapshot-testing` if using snapshot approach

---

## Open Suggestion Status Tracker

| ID | Summary | Impact | Effort | Status | Verified |
|----|---------|--------|--------|--------|----------|
| S-05 | Post-synthesis verification script | High | Medium | Not implemented — synthesis cross-check is LLM mental exercise, not automated | 2026-03-12 |
| S-09 | Detect oscillation in iteration loop | Medium | Low | Not implemented — only hard MAX_ITERATIONS cap, no cross-iteration comparison | 2026-03-12 |
| S-16 | **CRITICAL**: validate-findings passes unknown files | Critical | Low | Not implemented — `_filter_findings()` line 253 treats unknown files as "entire file new" | 2026-03-12 |
| S-18 | `file_path` vs `file` field inconsistency | High | Medium | Not implemented — `prepare-review-input` uses `file_path`, all 13 other schemas use `file` | 2026-03-12 |
| S-22 | Missing JSON error handling in Python scripts | Medium | Low | Not implemented — 4 scripts have bare json.load() with no error handling | 2026-03-12 |
| S-26 | AST-based metric extraction (tree-sitter) | High | High | POC needed — see [arch file](improvements-open-arch.md#s-26) | — |
| S-32 | DRY principle — full `references/DRY/` implementation | High | High | Not implemented — see [arch file](improvements-open-arch.md#s-32) | 2026-03-12 |
| S-33 | Grep-based discovery + validation scripts | High | Medium | Not implemented — see [arch file](improvements-open-arch.md#s-33) | 2026-03-13 |
| S-35 | Pre-commit hook for frontmatter validation | Medium | Low | Not implemented — depends on S-33 | — |
| S-37 | Style rules separate pipeline | Medium | Medium | Not implemented — no mechanism for review-only rules | 2026-03-12 |
| S-39 | Skip empty plans — don't synthesize or implement when no changes needed | Medium | Low | Not implemented | — |
| S-41 | Local MCP server for `references/` — language-scoped principle loading | Medium | Medium | Not implemented — would replace file-based `load-reference` with stdio MCP server | — |
| S-42 | Full automation loop: spec → code → test → commit → PR | High | High | Not implemented — see [arch file](improvements-open-arch.md#s-42) | — |
| S-45 | Design verification — structured pixel diff before refactor | High | High | POC needed — validate OpenCV/pixelmatch approach | — |