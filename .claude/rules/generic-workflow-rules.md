# Terminology

A **spec** is a `.claude/CLAUDE.md` file scoped to a specific module (skill, agent, or principle). The **root spec** is the project-level `.claude/CLAUDE.md` at the repository root.

# Spec Maintenance

When making changes to a module (skill, agent, or principle):

- Update the module's spec to reflect any changes to purpose, inputs/outputs, connections, design decisions, or gotchas.
- Only update the root spec if the change affects project-wide concerns: new modules added/removed, pipeline flow changes, new user-invocable skills, or changes to key concepts (retry limits, iteration behavior, etc).

**After every edit to a module file**, re-read the module's spec and check if the change affects any spec section (purpose, inputs/outputs, connections, design decisions, gotchas). If it does, update the spec in the same edit session — do not defer.

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

# Rules Are the Source of Truth

When a loaded rule explains how to do something (e.g., agent-wrapping-rules explains agent file structure), follow the rule directly. Do not read existing files "for reference" to verify the rule — that is redundant and wastes context.
