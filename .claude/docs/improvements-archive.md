# Archived Improvement Suggestions

Completed, resolved, or no-longer-applicable suggestions. Full details were in the original improvement-suggestions.md.

| ID | Summary | Impact | Effort | Status | Verified |
|----|---------|--------|--------|--------|----------|
| S-01 | Always-on SOLID enforcement (rules not distributable via plugin) | High | Low | Done — `/implement` skill is the SOLID-enforced coding entry point | 2026-03-19 |
| S-06 | Graceful degradation for partial failures | Medium | Medium | Done — prepare failures, all-compliant, and partial review handling sufficient | 2026-03-19 |
| S-07 | Fix `ruler.md` typo | Low | Trivial | Done — no `ruler.md` references remain | 2026-03-12 |
| S-14 | Fix iteration loop: `git add` between iterations | High | Low | Done | — |
| S-15 | `addresses` vs `resolves` field name | Low | — | Not a bug — different fields at different pipeline stages, intentional design | 2026-03-12 |
| S-17 | Missing `tier`/`activation` in rule.md frontmatter | High | Low | Done — replaced with tag-based activation via `discover-principles` skill | — |
| S-19 | Unit context lost in validation/synthesis schemas | High | Low | Done — unit_name/unit_kind preserved through full pipeline | 2026-03-12 |
| S-20 | Missing `has_changes` in prepare-input schema | Medium | Trivial | Done — type is `"boolean"`, not nullable | 2026-03-12 |
| S-24 | Empty `design_patterns/creational/` directory | Low | Trivial | Confirmed empty | 2026-03-12 |
| S-28 | Short-circuit MINOR-only findings — skip synthesis/implement | Medium | Low | Done — refactor pipeline Phase 4.6 with check-severity.py | 2026-03-12 |
| S-29 | `/code` greenfield gap — no source files for tag matching | Medium | Low | Done — Phase 2.2 line 34 explicitly handles greenfield | 2026-03-12 |
| S-31 | SwiftUI "dumb view" rule | High | Low | Done — implemented as SUI-2 (View Purity) metric | — |
| S-21 | No tests for `prepare-changes.py` | High | Medium | Done — `test_prepare_changes.py` exists in prepare-review-input/scripts/tests/ | 2026-04-13 |
| S-23 | README.md rewrite | Medium | Low | Done — fully rewritten with diagrams, workflow descriptions, skills listing | 2026-04-13 |
| S-30 | SwiftUI SUI-2/SUI-3 — validate SOLID coverage | Medium | Medium | Done — SUI-2 (View Purity) and SUI-3 (Modifier Chain Length) both implemented in SwiftUI rule.md | 2026-04-13 |
| S-40 | `solid-spec` frontmatter field | Medium | Low | Done — `solid-spec` field implemented in create-type SKILL.md | 2026-04-13 |
| S-43 | Rewrite mode — greenfield bypass in validate-plan | High | Low | Done — validate-plan Phase -1.2 detects mode: rewrite and skips to all-create output | 2026-04-13 |
| S-44 | `build-spec-from-code` skill | High | High | Done — skill created at skills/build-spec-from-code/ | 2026-04-13 |
| S-10 | Output cleanup mechanism | Low | Low | Done — implement Phase 6.3 deletes .solid_coder/ on successful run | 2026-04-13 |
