# Agent Wrapping

An **agent** is a thin wrapper that allows a skill to run as a subagent — enabling parallel execution or model selection. Agents live in `agents/` and are `.md` files with YAML frontmatter.

## When to Create an Agent

Create an agent wrapper when a skill needs to:
- Run in **parallel** with other skills (e.g., multiple principle reviews at once)
- Run on a **specific model** different from the caller (e.g., Sonnet for reviews, Opus for synthesis)
- Run in **isolation** as a subagent with its own context window

Not every skill needs an agent. Lightweight utilities called inline do not need wrapping.

## Agent File Structure

Agent files live at `agents/<agent-name>.md`. The file has two parts:

### 1. Frontmatter

```yaml
---
name: <agent-name>
description: <one-line description of what this agent does>
argument-hint: <arguments passed through to the skill>
allowed-tools: <comma-separated tool list>
skills:
  - <skill-name>          # skills this agent has access to
tools: <comma-separated tool list>
model: <sonnet|opus>      # which model runs this agent
maxTurns: <number>        # optional, for complex skills
---
```

Key fields:
- **`skills`** — lists the skill(s) the agent can invoke. Most agents wrap exactly one skill.
- **`model`** — determines which model runs the agent. Use `sonnet` for structured/pattern-matching tasks (reviews), `opus` for reasoning-heavy tasks (synthesis, coding).
- **`tools`** — the tools available to the agent. Must include what the skill needs (check the skill's `allowed-tools` frontmatter).
- **`maxTurns`** — optional. Set for skills that need many tool calls (coding, synthesis). Omit for simple skills.

### 2. Body

The body is minimal — it delegates to the skill:

```markdown
You are a dedicated skills executor. Your ONLY job is to follow instructions of the preloaded skills.

## Workflow
-[] <skill-name>
```

For single-skill agents that are purely wrappers (no custom instructions), the body can be empty — the frontmatter alone is sufficient.

## Naming Convention

Agent names mirror the skill they wrap, with `-agent` suffix:
- `apply-principle-review` → `apply-principle-review-agent`
- `synthesize-fixes` → `synthesize-fixes-agent`
- `code` → `code-agent`

## Arguments

Arguments flow through from the caller to the agent to the skill. The agent's `argument-hint` should match the wrapped skill's `argument-hint`.