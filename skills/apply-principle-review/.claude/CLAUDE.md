# apply-principle-review

Single-principle code review skill. Reads a principle's rule definitions and review instructions, then evaluates each changed unit against those rules. Internal skill — never invoked directly by users.

## Purpose

Detect principle violations in changed code units by strictly applying the metrics and severity bands defined in a principle's `rule.md`. Produces structured findings per unit, scoped to the principle being evaluated.

## Design

### Principle-Agnostic Engine

This skill is the core of the system's scalability. It is **completely generic** — it has no knowledge of which principle it's reviewing until it loads the principle's rule and instruction files at runtime. SRP, OCP, SwiftUI, or any future principle all flow through the same skill with the same phases. Adding a new principle to the system requires only adding a new folder under `references/` with the right file structure; no changes to this skill are needed. The skill derives all its review behavior (metrics, severity bands, checklist steps, output schema) from the principle data it loads.

### Per-Unit Analysis

The core design choice is **per-unit granularity** (class, struct, enum, protocol, extension) rather than per-file. This ensures:

- **No units are skipped** — files with multiple declarations get each unit evaluated independently.
- **Findings attach to units, not files** — downstream consumers (synthesizer, implementation agents) can map findings precisely. The implementation plan is per-file but broken down per-unit internally.

### Change-Scoped Review

Only units with `has_changes == true` are reviewed. This is a deliberate constraint to prevent the model from reviewing or suggesting refactors for code the user didn't touch. The iteration loop handles ripple effects — if a change in one unit creates a violation in another, the next iteration's fresh review picks it up when that unit is modified.

### Strict Rule Application

The skill enforces hard constraints on LLM behavior:

- **Do NOT invent rules** — only apply what is explicitly in `rule.md`.
- **Do NOT expand exception lists** — apply ONLY the exceptions explicitly defined in `rule.md`. If a dependency looks similar to a listed exception but does not match the stated criteria, it is NOT an exception. Do not justify exceptions by "well-known patterns" or common industry practice (e.g., "Logger is a helper", "Analytics is cross-cutting"). The rule defines what qualifies. Nothing else does.
- **Do NOT merge or skip checklist steps** — follow the review instructions sequentially.

These exist because LLMs will create workarounds when facing ambiguity. In practice, models were observed fabricating exception cases when the rule didn't define one, leading to false negatives. The constraints force the model to fail explicitly rather than silently rationalize.

### Frontmatter-Driven Loading

Review instructions (`review/instructions.md`) use YAML frontmatter to declare paths to `rule.md` and `output.schema.json`. The original intent was to keep a structured, self-describing format that an orchestrator could parse and inject into skills/agents. This path wasn't fully realized and may be simplified in the future due to overhead, but the mechanism works and the skill depends on it.

## Arguments & Variables

**Arguments:** `<principle-folder> <code-files>`

| Variable | Source | Description |
|----------|--------|-------------|
| `RULES_PATH` | `${CLAUDE_PLUGIN_ROOT}/references` | Root path to all principle folders |
| `INPUT_SCHEMA` | `${CLAUDE_PLUGIN_ROOT}/skills/prepare-review-input/output.schema.json` | Schema for the review-input JSON |
| `NAME` | `$ARGUMENTS[0]` | Principle name (e.g., `SRP`, `OCP`, `SwiftUI`) |
| `OUTPUT_PATH` | `$ARGUMENTS[1]` | Output root. If not provided, defaults to `CURRENT_PROJECT/.solid-coder-<YYYYMMDDhhmmss>` |

## Flow

### Phase 1: Preparation

Create a tasklist and execute:

1. **Create output folder** — `OUTPUT_PATH/NAME`
2. **Parse instruction frontmatter** — Run `parse-frontmatter.py` on `RULES_PATH/NAME/review/instructions.md`. Extract `rules` and `output_schema` paths from the JSON output. Fallback: if `rules` is not present in frontmatter, use `RULES_PATH/NAME/rule.md`.
3. **Parse rule frontmatter** — Run `parse-frontmatter.py` on the resolved `rule.md`. Extract `required_patterns` and other metadata.
4. **Load references** — Run `load-reference.py` with file paths from step 3 (design patterns, referenced documents).
5. **Load rules** — Run `load-reference.py` with the rules path from step 2.
6. **Parse input** — Read and parse the review-input JSON. Extract file list and unit metadata (paths, line ranges, has_changes flags). Do NOT read source code files here — they are loaded one at a time in Phase 2.

### Phase 2: Analysis (per-unit detection)

Files are processed **one at a time** — source code is read just before reviewing, not all upfront. This keeps context focused on the file being reviewed rather than polluting the window with all files at once.

```
FOR each file in input DO
  1. Read this file's source code NOW
  FOR each unit (class, struct, enum, protocol, extension) where has_changes == true DO
    2. Scope analysis ONLY to this unit's line range (line_start..line_end)
       — ignore other declarations in the same file
    3. Create a second tasklist from the instruction steps
       — instructions may define additional analysis tasks
    4. Execute the tasklist, producing findings for this unit
  END
  — units where has_changes == false are skipped entirely
END
```

The key mechanism in Phase 2 is **dynamic task creation**: the review instructions themselves may contain checklist steps that become tasks. A second tasklist is created per unit from these instruction-driven steps and executed inline.

### Phase 3: Output

1. **Load output schema** — Read the schema file referenced in the instruction frontmatter.
2. **Generate output** — Produce structured JSON matching the schema. One finding per triggered metric.
3. **Write output** — Write to `OUTPUT_PATH/NAME/review-output.json`.

## Inputs / Outputs

**Input:** `<principle-folder> <code-files>` — principle name (e.g., `SRP`) maps to `references/{NAME}`. Code files is a path to JSON following `INPUT_SCHEMA`, produced by `prepare-review-input`.

**Output:** `{OUTPUT_PATH}/{NAME}/review-output.json` — structured findings per file per unit, matching the principle's `review/output.schema.json`.

## Utility Scripts

The skill delegates parsing and loading to Python scripts from sibling skills:

| Script | Skill | Purpose |
|--------|-------|---------|
| `parse-frontmatter.py` | `parse-frontmatter` | Extracts YAML frontmatter from markdown files as JSON |
| `load-reference.py` | `load-reference` | Loads reference files with frontmatter stripped |

Invocation pattern: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/<skill>/scripts/<script>.py <args>`

## Connections

| Direction | Module | Relationship |
|-----------|--------|-------------|
| Wrapped by | `apply-principle-review-agent` | Agent wrapper for parallel execution (Sonnet) |
| Upstream | `prepare-review-input` | Produces the normalized input JSON this skill consumes |
| Upstream | `discover-principles` | Determines which principles are active and matched |
| Downstream | `validate-findings` | Reads the output JSON — straightforward, no special contract |
| Downstream | `synthesize-fixes` | Consumes validated findings for cross-principle fix planning |

## Model Choice

Sonnet is used for review via `apply-principle-review-agent`. Sonnet follows structured instructions well for this task, which is pattern matching against defined rules rather than open-ended reasoning.

## Error Handling

**Intent:** Fail fast with an explicit error message. No partial output, no auto-resolution.

Fail conditions:
- Input doesn't match schema or is unrecognized
- Code files not found
- Instructions not found (`review/instructions.md`)
- Rules not found (`rule.md`)

**Current state:** Fail-fast behavior is not fully implemented. This is a known gap.

## Known Limitations

- **Large files / many violations** — files with many units or many findings per unit cause excessive iterations during the refactoring loop downstream. This is a practical bottleneck, not a bug in the skill itself.