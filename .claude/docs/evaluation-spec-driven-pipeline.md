# solid-coder Evaluation: Spec-Driven Pipeline Analysis

**Date:** 2026-04-04
**Evaluator:** Claude Code (Opus 4.6)
**Context:** Evaluating solid-coder as a spec-driven development tool for an enterprise iOS rewrite, against the team's proposed AI pipeline approach.

---

## Executive Summary

solid-coder is a working multi-agent pipeline that reviews, plans, and implements Swift code using SOLID principles as enforceable, metric-driven rules. It is not documentation or a prototype — it has 22 skills, 10 agents, 7 complete principle sets, and 20 commits in the last two weeks showing active iteration.

The core pipeline (spec → architecture → validation → synthesis → implementation → review) is complete end-to-end.

---

## Claims Made — Verify These

### Claim 1: The spec→implement pipeline is complete and functional

**Evidence found:**
- `/build-spec` skill: 8-phase interview flow with buildability gate (validate-spec runs up to 3 rounds)
- `/implement` skill: 6-phase orchestrator — plan → validate-plan → synthesize-implementation → code → validate-implementation → refactor
- All intermediate agents exist: `plan-agent` (opus), `validate-plan-agent` (sonnet), `synthesize-implementation-agent` (opus), `code-agent` (opus)
- JSON schemas enforce contracts between every pipeline stage
- Real specs exist in `.claude/specs/` (SPEC-001 epic, SPEC-005 DRY, SPEC-007 build-spec-from-code, SPEC-008 diff-hunks, SPEC-009 nested subtask)

**Gap found:** No `.solid_coder/` output directory exists — no evidence of a complete end-to-end run producing artifacts. Specs exist but are about solid-coder itself, not an external project.

**Verdict:** Pipeline is structurally complete. No proof of production use on a real feature yet.

### Claim 2: Cross-principle synthesis catches cascading violations

**Evidence found:**
- `synthesize-fixes` skill uses a two-pass algorithm: Pass 1 drafts per-principle fixes, Pass 2 cross-checks every draft against ALL other active principles' metrics
- Cross-check examples documented: SRP extraction creating OCP sealed points, OCP injection creating SRP cohesion groups, ISP splits breaking LSP conformers
- Failed cross-checks attempt patching; if patching fails, finding is marked `unresolved` with reason
- Merge rules handle synergistic vs conflicting actions on same code region

**Gap found:** Cross-checking is LLM-simulated, not deterministic. The LLM "simulates" whether a proposed fix would worsen another principle's metrics. S-05 (post-synthesis verification) is deferred because per-principle verification scripts don't scale.

**Verdict:** The architecture is sound. The cross-check is the system's most valuable feature but also its weakest point — it depends on LLM judgment, not measured metrics.

### Claim 3: 7 complete principles with quantitative metrics

**Evidence found:**
- SRP: verb count, cohesion groups, stakeholders → COMPLIANT/MINOR/SEVERE bands
- OCP: sealed points, untestable dependencies → severity bands with factory/helper/boundary exceptions
- LSP: type checks, contract violations, empty/fatal methods → severity bands with framework-forced cast exceptions
- ISP: protocol width, conformer coverage → severity bands with marker/composition/single-conformer exceptions
- DRY: structural duplication, semantic duplication, inline shared logic → severity bands
- SwiftUI: body complexity, view purity, modifier chains, VM injection → 14 examples
- Testing: test completeness, coverage model → 8 examples

**Gap found:** DRY and Testing are listed as "Planned" in `overview.md` but actually exist in `references/`. Documentation is behind the code.

**Verdict:** Confirmed — 7 principles are implemented. Docs are stale on this point.

### Claim 4: The system solves the "gotcha encoding" problem

**Evidence found:**
- `/build-spec` Phase 6 runs `validate-spec --interactive` checking for: vague terms, undefined types, intent-described operations, implicit consumer contracts, unverified external APIs, ambiguous scope, implementation leaking, AC-architecture disconnects
- Up to 3 rounds of validation before spec is accepted
- Edge cases and design decisions are captured as acceptance criteria, not free-form text
- Technical requirements are preserved verbatim through the pipeline into implementation plan items

**Gap found:** The quality of gotcha detection depends on the LLM's knowledge of the domain. For platform-specific gotchas (e.g., NSOpenPanel must use runModal() not begin()), the system can only catch what the LLM already knows or what the user explicitly adds during the interview.

**Verdict:** Structurally strong — the interview + validation loop forces gotchas to surface. But it doesn't generate domain knowledge that nobody provides.

### Claim 5: Reuse detection prevents shared component collisions

**Evidence found:**
- `validate-plan` searches codebase for existing types via `search-codebase.py` (scans `solid-category` and `solid-description` frontmatter)
- Name-based fallback search (Phase 1.5) catches legacy code without frontmatter
- Each component classified as `create`/`reuse`/`adjust`/`conflict`
- Acceptance criteria matching tracks which ACs existing code satisfies vs doesn't
- Rewrite mode (`mode: rewrite` in spec frontmatter) short-circuits to all-`create`

**Gap found:** `search-codebase.py` depends on `solid-` prefixed frontmatter in Swift files. Legacy code without this frontmatter is caught only by name-based grep fallback, which is less reliable. The `find-component.py` script (S-33) for more sophisticated discovery is not implemented.

**Verdict:** Works for greenfield code that follows the frontmatter convention. Degrades gracefully for legacy code but isn't as strong there.

### Claim 6: Test coverage is adequate

**Evidence found:**
- 12 of ~25 Python scripts have tests (~48%)
- Tested: build-spec-query, discover-principles, find-spec, load-reference, parse-frontmatter, prepare-review-input (2), synthesize-fixes, validate-findings (2), validate-plan, generate-report
- Not tested: prepare-changes.py (S-21 — zero tests, most critical diff-parsing script), split-plan.py, search-codebase.py (has test file but unclear coverage)
- Dependencies: pytest >= 7.0, jsonschema >= 4.0

**Gap found:** prepare-changes.py has zero tests and is the entry point for all diff parsing. No CI/CD pipeline exists. No pytest.ini or pyproject.toml for test configuration.

**Verdict:** Strategic coverage on utilities, but the most critical script (diff parsing) is untested.

### Claim 7: Known bugs are documented and tracked

**Evidence found:**
- S-16 (CRITICAL): validate-findings.py line 253 treats "file not in review-input" same as "entire file is new" — hallucinated findings pass through. 3-line fix, still open.
- S-18 (HIGH): `file_path` vs `file` field inconsistency across 13+ schemas — works because LLM adapts, but fragile
- S-22 (MEDIUM): 4 scripts have bare json.load() with no error handling
- S-09 (MEDIUM): No oscillation detection in iteration loop
- Improvements tracked across 3 files: open (30+ items), partial (12 items), archive (12 completed)

**Verdict:** Honest self-assessment. Known issues are documented with severity, effort, and verification dates. S-16 should be fixed before any demo — it's a credibility risk.

---

## Strengths (What Works Well)

1. **Spec is the enforceable contract** — not just documentation, but the input that drives architecture, validation, synthesis, and implementation
2. **Cross-principle synthesis** — fixes are checked against all active principles, not applied in isolation
3. **Quantitative severity** — COMPLIANT/MINOR/SEVERE from measured metrics, not subjective judgment
4. **Exception system** — reduces false positives (facades, factories, helpers, boundary adapters, NoOp objects all have explicit recognition criteria)
5. **Acceptance criteria preservation** — ACs flow verbatim from spec through arch.json into individual plan items; nothing summarized away
6. **Schema-enforced boundaries** — every pipeline stage validates JSON at entry/exit
7. **Active development** — 20 commits in 2 weeks, iterative bugfixing, not abandoned

## Weaknesses (What Needs Work)

1. **No end-to-end proof** — no `.solid_coder/` output from a real feature run exists
2. **Cross-checking is LLM-simulated** — the synthesis cross-check is the system's key differentiator but depends on LLM judgment, not deterministic verification
3. **S-16 critical bug unfixed** — 3-line fix that undermines credibility if found
4. **Schema inconsistency (S-18)** — `file_path` vs `file` across 13 schemas
5. **No CI/CD** — no automated test runs, no pre-commit hooks
6. **prepare-changes.py untested** — zero tests on the most critical script
7. **Documentation lag** — overview.md says DRY/Testing are "Planned" when they're implemented
8. **Reuse detection depends on frontmatter convention** — degrades for legacy code

## Strategic Assessment

### vs The Team's Proposed Pipeline

| Dimension | Team Pipeline | solid-coder |
|-----------|--------------|-------------|
| Spec origin | Reverse-engineered from existing code | Forward-written through interview + validation |
| Validation | "AI validates AI" — circular | SOLID metrics (quantitative) + human spec review (qualitative) |
| Gotcha capture | "Dev adds gotchas" — assumes deep knowledge | Forced through validate-spec interview loop |
| Shared components | Discovered at PR review time | Detected at plan-validation time via codebase search |
| Accountability | Diffuse — PM trusts AI, dev trusts factory | Single spec owner; every finding traces to a principle + metric |
| Extensibility | Unclear | Add a folder to `references/` — no code changes |

### What solid-coder does NOT solve

- **Business logic correctness** — SOLID principles catch structural quality, not "did we build the right thing"
- **Domain knowledge generation** — the system can interrogate a spec for gaps but can't invent platform gotchas the user doesn't know
- **The "AI checking AI" problem** — validate-implementation uses LLM screenshot comparison, which has the same circularity the team's pipeline has

### Recommended Next Steps for the Controlled Experiment

1. Fix S-16 (critical bug, 3 lines)
2. Fix S-18 (schema inconsistency) or at minimum document why it works
3. Pick a real feature from the enterprise app
4. Run `/build-spec` → `/implement` end-to-end
5. Keep all `.solid_coder/` artifacts as evidence
6. Measure: time (including spec writing), bugs found in review, bugs post-merge, can-another-dev-extend-it

### Key Metrics for the Experiment

| Metric | What It Proves |
|--------|---------------|
| Total time (spec + implementation) | Cost of upfront investment |
| SOLID findings in `/review` output | Structural quality of generated code |
| Bugs found in PR review | What automation missed |
| Bugs found post-merge | What everyone missed |
| Time for another dev to extend the feature | Knowledge transfer — the real differentiator |
| Spec accuracy after first production bug | Whether the spec improves from feedback |

---

## Verification Instructions

To validate these claims against a running system:

1. **Pipeline completeness**: Run `/build-spec` on a test feature → verify it produces a spec in `.claude/specs/` → run `/implement <spec>` → verify it produces architecture, plan, and code
2. **Cross-principle synthesis**: Run `/refactor` on a file with known multi-principle violations → check `synthesized/*.plan.json` for cross_check_result entries
3. **Severity metrics**: Run `/review` on `references/*/Examples/` files → verify severity classifications match the bands in each `rule.md`
4. **Reuse detection**: Add `solid-` frontmatter to a Swift file → run `/implement` on a spec that needs a similar type → verify `validate-plan` finds it
5. **S-16 bug**: Fabricate a review-output.json with findings for a file NOT in review-input.json → run validate-findings.py → verify the findings pass through (they shouldn't)
