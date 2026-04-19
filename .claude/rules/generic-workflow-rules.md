# Terminology

A **spec** is a `.claude/CLAUDE.md` file scoped to a specific module (skill, agent, or principle). The **root spec** is the project-level `.claude/CLAUDE.md` at the repository root.

# Spec Maintenance

When making changes to a module (skill, agent, or principle):

- Update the module's spec to reflect any changes to purpose, inputs/outputs, connections, design decisions, or gotchas.
- Only update the root spec if the change affects project-wide concerns: new modules added/removed, pipeline flow changes, new user-invocable skills, or changes to key concepts (retry limits, iteration behavior, etc).

**After every edit to a module file**, re-read the module's spec and check if the change affects any spec section (purpose, inputs/outputs, connections, design decisions, gotchas). If it does, update the spec in the same edit session — do not defer.

# Spec Lifecycle

Specs start in `.claude/specs/` as drafts. Each spec is a folder (e.g. `SPEC-NNN-slug/`) containing `Spec.md` and an optional `resources/` directory for designs, images, and other materials. When a spec is implemented and its module has a `.claude/CLAUDE.md`, the spec content moves into that module spec — **including the YAML frontmatter** (number, feature, status, blocked-by, blocking). Update `status` to `done` when moving. Then delete the original spec folder from `.claude/specs/`.

This keeps the spec traceable (the number and dependency chain stay with the module) while eliminating the duplicate.

**Do NOT remove entries from `blocked-by`** when a dependency is completed. The dependency chain is a permanent record. Resolution is tracked by `status`, not by list membership.

## Dependency Validation (before implementing a spec)

Before starting implementation of any spec, validate that all `blocked-by` dependencies have `status: done`. Specs may live in two places:

1. `.claude/specs/**/Spec.md` — draft specs not yet implemented (each in its own folder)
2. `*/.claude/CLAUDE.md` — implemented specs (moved into their module)

**Validation procedure:**

For each `SPEC-NNN` in the spec's `blocked-by` list:
1. Grep for `number: SPEC-NNN` across both `.claude/specs/` and all `*/.claude/CLAUDE.md` files
2. Read the matched file's frontmatter and check `status:`
3. If status is NOT `done` → **stop execution** and report: "Blocked: SPEC-NNN (status: {status}) must be done before this spec can be implemented."

If ANY dependency is not `done`, do not proceed. List all blocking specs and their current statuses.

# New Module Creation

When creating a new module (skill, agent, or principle), always create a spec (`.claude/CLAUDE.md`) within the module's folder. The spec should document purpose, inputs/outputs, connections to other modules, design decisions, and gotchas.

# Referencing Skills from Skills

Skills can delegate work to other skills. When a skill needs another skill's capabilities, reference it by its fully qualified name using the `**solid-coder:<skill-name>**` format in the SKILL.md instructions.

Use the exact phrase: `use skill **solid-coder:<skill-name>** to <what it does>`

**Do:**
- `use skill **solid-coder:discover-principles** to discover active principles with --refs-root references/`
- `use skill **solid-coder:load-reference** to load the rule_path content`
- `use skill **solid-coder:create-type** to apply naming conventions`

**Don't:**
- Inline the other skill's script calls (`python3 ${CLAUDE_PLUGIN_ROOT}/skills/.../scripts/...`)
- Duplicate the other skill's logic in your own phases
- Call the other skill's internal files directly via Read/Glob

The skill executor resolves the reference and handles invocation. The calling skill only needs to specify the skill name and arguments.

# Invoking Skills as Subagents

When a skill needs to run another skill as a **subagent** (isolated context, specific model), use the Task call pattern instead of inline skill references. This is the standard pattern for orchestrator skills that coordinate multi-phase workflows.

**Pattern:**
```markdown
- [ ] N.1 Prepare a Task call:
  - subagent_type: `solid-coder:<agent-name>`
  - prompt:
    ```
    <arguments as key-value pairs>
    ```
- [ ] N.2 Launch Task
- [ ] N.3 From the Task result, extract <what you need>
  - If the Task failed, stop and report the error
```

**When to use subagents vs inline skills:**
- **Subagent** (Task call): When the skill needs isolation, runs on a specific model, or could run in parallel with others. Always use the `-agent` wrapper (e.g., `plan-agent`, not `plan`).
- **Inline skill** (`**solid-coder:<skill>**`): For lightweight utilities that run in the caller's context (e.g., `parse-frontmatter`, `load-reference`, `discover-principles`).

**For parallel execution**, prepare multiple Task calls and launch ALL in a SINGLE message:
```markdown
- [ ] N.3 For EACH item, prepare a Task call:
    - subagent_type: `solid-coder:<agent-name>`
    - prompt: ...
- [ ] N.4 Launch ALL Tasks in a SINGLE message (multiple Task tool calls for parallel execution)
- [ ] N.5 Wait for all to complete
```

# Rules Are the Source of Truth

When a loaded rule explains how to do something (e.g., agent-wrapping-rules explains agent file structure), follow the rule directly. Do not read existing files "for reference" to verify the rule — that is redundant and wastes context.

# Confirm approach before acting
Before starting non-trivial work, use AskUserQuestion to confirm your understanding of the task and proposed approach.

# Use AskUserQuestion for choices
Whenever you need to present the user with multiple options or choices, use the AskUserQuestion tool instead of listing them in text output.