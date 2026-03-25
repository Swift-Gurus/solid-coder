---
name: validate-spec-spec
description: Spec for the buildability validator skill — checks specs for vague terms, undefined types, and implicit contracts.
type: spec
---

# validate-spec — Spec

## Purpose

Validates that a spec is concrete enough to implement without ambiguity. Catches vague terms, undefined types, intent-described operations, implicit consumer contracts, and unverified external APIs.

## Inputs / Outputs

|-----------|------|--------|----------|
| Input | Spec file | Markdown with YAML frontmatter | Any `.claude/specs/` or module spec path |
| Input | Parent spec (if exists) | Markdown | Resolved from `parent` frontmatter field |
| Output | Validation report | Structured text | Printed to stdout |

## Connects To

| Upstream | Relationship |
|----------|-------------|
| `skills/build-spec` | Invokes validate-spec in Phase 4 (buildability gate) with `--interactive` |
| Any spec file | Read-only input |

| Downstream | Relationship |
|------------|-------------|
| None | Report-only — does not modify specs |

## Key Design Decisions

- **Read-only** — never modifies the spec. Reports findings, optionally asks the user to resolve them.
- **Two modes** — standalone (report only) and interactive (used by build-spec, asks user to resolve gaps). Mode determined by `--interactive` flag.
- **Type-aware structural checks** — required sections differ by spec type (feature vs bug vs epic). Don't flag missing bug sections on a feature spec.
- **Epic-specific buildability scan** — epics are intentionally high-level, so Phase 3 applies a different check set: vague scope, undefined subtasks (named but not scoped), missing success criteria, and ambiguous cross-subtask ownership. Standard checks (undefined types, consumer contracts, unverified APIs) are skipped for epics.
- **User story quality check (Phase 3-Standard)** — validates story format, flags acceptance criteria that are not independently verifiable (e.g. "works correctly"), and flags criteria that describe implementation rather than observable behavior.
- **Structural checks updated** — all specs require Diagrams (connection + flow, sequence if async/multi-actor). Features/subtasks require User Stories instead of Workflow. UI/Mockup section required when spec mentions screens, views, components, or user interaction — placeholder counts as a gap.
- **Question-per-finding** — in interactive mode, each finding becomes a focused question. Answers are returned to the caller (build-spec) for draft patching.
- **AC-architecture disconnect check (Phase 3.8)** — verifies that every behavioral AC traces to a specific architectural mechanism in Technical Requirements, and that every claimed architectural mechanism handles all interaction types shown in mockups. Catches specs where behavior is described but no architecture supports it, or where a "unified" mechanism doesn't actually cover all cases.

## Gotchas

- Don't invent requirements — only flag what's vague or missing in what's already written. The validator doesn't know what the spec *should* say.
- Parent context is loaded for reference only — don't flag gaps that are clearly answered in the parent spec.
- Vague term detection should be contextual — "handle errors" in a Description is vague, but "handle errors by returning Result<T, Error>" is concrete.