---
number: SPEC-008
feature: diff hunks in review input
type: bug
status: draft
blocked-by: []
blocking: []
---

## Description

The refactor pipeline flags pre-existing SOLID violations as actionable findings
whenever a changed file is touched, even when the change is trivial. This erodes
trust in the review output and produces noise that obscures real regressions.
The fix equips review agents with actual diff hunk content so they can classify
whether each finding was introduced by the change, then filters out pre-existing
violations in `validate-findings` before they reach synthesize and implement.

## Bug Report

**Steps to reproduce:** Run `/refactor` on a file with a trivial change (field
rename, single case addition). Observe that pre-existing SRP or OCP violations
appear as actionable findings.

**Expected:** Only violations introduced or worsened by the change are reported.

**Actual:** All violations in a touched file are reported, regardless of whether
they predate the change.

**Root cause:** Review agents receive `changed_ranges` (line numbers) but not
actual diff content. For structural findings they evaluate the full unit and
correctly identify violations, but have no basis to determine whether the
violation was introduced by the change or predates it.

**Affected components:** `prepare-review-input`, all principle
`review/instructions.md` + `review/output.schema.json` files,
`validate-findings.py`.

## Changes

### Change 1 — `prepare-review-input`: emit `changed_hunks`

Add `changed_hunks[]` alongside `changed_ranges` on each file entry in
`review-input.json`. Run `git diff --unified=0 HEAD` (staged + unstaged) and
parse into structured hunks per file. For untracked files, use full file content
as a single hunk (`removed: ""`).

```json
{
  "file_path": "Sources/LogMessage.swift",
  "changed_ranges": [{ "start": 63, "end": 65 }],
  "changed_hunks": [{
    "start": 63,
    "end": 65,
    "removed": "  var skill: String\n  var args: String",
    "added": "  var name: String\n  var arguments: String\n  var status: String"
  }],
  "units": [...]
}
```

Fields:
- `start` / `end` — line numbers in the current (post-change) file, matching `changed_ranges`
- `removed` — lines prefixed with `-` in the diff, joined with `\n`, stripped of the `-` prefix
- `added` — lines prefixed with `+` in the diff, joined with `\n`, stripped of the `+` prefix

For untracked files: `removed` is `""`, `added` is the full file content.

### Change 2 — review instructions: set `introduced_by_change`

Add to each principle's `review/instructions.md`:

> **introduced_by_change**
>
> For each finding, set `introduced_by_change: true` if the changed lines
> (from `changed_hunks` in review-input.json) directly introduced or worsened
> the violation. Set `false` if the violation predates the change.
>
> Guidelines:
> - **Localized findings** (specific line — e.g. a type cast, a modifier chain):
>   check whether the offending line falls within a `changed_hunk.added` block.
>   If yes → `true`.
> - **Structural findings** (whole-unit — e.g. SRP cohesion groups, OCP sealed
>   variation points): read `changed_hunks` for the file. If the added lines
>   introduce a new verb, new stakeholder, new non-injected dependency, or new
>   state group → `true`. If the added lines are a rename, a field addition to
>   existing structure, or a single case delegation → `false`.
> - When in doubt, prefer `false` (do not over-report pre-existing debt).

Add to each `review/output.schema.json` findings array:
```json
"introduced_by_change": {
  "type": "boolean",
  "description": "True if the changed lines introduced or worsened this violation."
}
```

Required field. Default `true` for backward compatibility in consumers that
predate this spec.

### Change 3 — `validate-findings.py`: filter by `introduced_by_change`

In `_filter_findings`, after the existing `ranges_overlap` check:
```python
if not finding.get("introduced_by_change", True):
    continue  # pre-existing violation — drop
```

The `True` default preserves existing behavior for findings produced by older
review agents that do not yet emit the field.

## Connects To

| Direction  | Component                                       |
|------------|-------------------------------------------------|
| Modifies   | `prepare-review-input` skill                    |
| Modifies   | All principle `review/instructions.md`          |
| Modifies   | All principle `review/output.schema.json`       |
| Modifies   | `validate-findings.py`                          |
| Downstream | `synthesize-fixes`, `implement` (cleaner input) |

## Edge Cases

- Untracked files: no git diff available — treat full content as one hunk,
  `removed: ""`.
- Findings from review agents that predate this spec (no `introduced_by_change`
  field): default to `True` to preserve existing behavior.
- A finding that spans both changed and unchanged lines: classify based on
  whether the worsening element falls in the `added` block.

## Design Decisions

- **Default `True` on missing field** — preserves backward compatibility with
  older review agents that don't emit `introduced_by_change` yet.
- **Filter in `validate-findings`, not in review agents** — keeps review agents
  as pure reporters; the filtering policy lives in one place.
- **`git diff --unified=0 HEAD`** — `--unified=0` minimizes context noise and
  keeps hunk boundaries tight.

## Definition of Done

- [ ] `review-input.json` contains `changed_hunks` for every file with
      non-empty `changed_ranges`. Untracked files have `removed: ""`.
- [ ] All principle `review/output.schema.json` files include
      `introduced_by_change` as a required boolean field on findings.
- [ ] All principle `review/instructions.md` files include the
      `introduced_by_change` rule.
- [ ] `validate-findings.py` drops findings where `introduced_by_change == false`.
- [ ] Re-running the refactor pipeline on SPEC-001 changes produces zero
      findings for `LogParser` (field rename, no new verb/dependency) and zero
      findings for `LogViewerView` (single case delegation to
      `SkillToolExpandedContent`).
- [ ] A finding for a newly added `as?` cast in a changed line is correctly
      retained (`introduced_by_change: true`).
