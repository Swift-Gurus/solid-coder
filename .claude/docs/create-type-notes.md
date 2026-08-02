# create-type — Developer Notes

## Gotchas

- **Adding a new `solid-stack` value requires updating all dependents.** The stack vocabulary in `skills/create-type/SKILL.md` Phase 3.3 is the source of truth, but it is hardcoded in other places that will silently fall out of sync:
  - `skills/plan/scripts/validate-arch.py` — `VALID_STACKS` set (unknown stacks emit a warning during plan validation)
  - `references/principles/frontmatter/rule.md`, `code/instructions.md`, and `fix/FM-4.md` — the `solid-stack` vocabulary is duplicated there for the FM-4 (incorrect stack) detection/fix instructions
  - Any future scripts that parse or validate stack values

  When adding a new stack entry, grep for `VALID_STACKS` across the codebase and update every match.