---
name: cohesion-cluster
description: Cluster a spec's acceptance criteria into cohesion groups using a 4-signal extraction + 2-signal transitive clustering rule, and label each group as a candidate split boundary. Internal skill — invoked by validate-spec Phase C.
argument-hint: <spec-path> <output-dir>
allowed-tools: Read, Write
user-invocable: false
---

# Cohesion Cluster

## Input

- SPEC_PATH: `$ARGUMENTS[0]` — absolute path to the spec's `Spec.md`
- OUTPUT_DIR: `$ARGUMENTS[1]` — absolute path to the output directory; the skill writes `cohesion.json` there.

## Workflow

### Phase 1 — Extract ACs and signals

- [ ] 1.1 Read the spec file in full.
- [ ] 1.2 Locate the user-stories section. Canonical heading is `## User Stories`; also accept any H2 whose label contains "Stories" or "Scenarios". Within that section, identify each user story:
    - **Typical form:** an H3 heading (`### `) introducing the story. The canonical convention is `### US-N: <title>`, but variations like `### Story N`, `### Scenario N`, or just `### <title>` are valid.
    - **Edge case:** if ACs appear directly under `## User Stories` with no H3 boundaries, treat the whole section as a single story.
- [ ] 1.3 For each story, list its acceptance criteria — bullets (`-`, `*`, or `+`) describing observable behavior, typically in a `When ... then ...` shape. Continue collecting bullets until the next H2 or H3 heading. Ignore obvious meta-bullets (the story narrative paragraph, sub-explanations).
- [ ] 1.4 Assign each AC a stable id. Prefer the canonical form `US-{n}.{m}` when stories are numbered (e.g. `### US-2: ...` → `US-2.1`, `US-2.2`, ...). Otherwise fall back to `STORY-{n}.{m}` using the story's 1-based ordinal position within the section. `m` is always the 1-based bullet index within the story.
- [ ] 1.5 For each AC, extract the four signals:

    | Signal | What to look for |
    |---|---|
    | **Data type / model** | Concrete types or models the AC reads, writes, or transforms. Use the spec's own naming (e.g. `SessionEvent`, `LogsProviderError`). |
    | **Screen / view** | Named screen or view the AC is observable on. `null` if no UI involvement. |
    | **External integration** | Library, package, protocol, or external API the AC relies on (e.g. `JSONLineReaderBuilder`, `AsyncSequence`, `URLSession`). |
    | **Lifecycle phase** | One of: `construction`, `subscribe`, `observation`, `cancel`, `mutation`, `teardown`. Pick the phase the AC operates in — when in doubt use `subscribe` for runtime observable behavior. |

    Multi-value signals are allowed (e.g. an AC may touch two data types).

### Phase 2 — Cluster (2-signal transitive)

- [ ] 2.1 Two ACs cluster together if they share **at least 2 signals of the same kind** (e.g. they both touch the same data type AND the same lifecycle phase). Sharing only one kind is not enough.
- [ ] 2.2 Cluster transitively: if A clusters with B and B clusters with C, all three share a group.
- [ ] 2.3 Iterate until stable. Output the disjoint groups.
- [ ] 2.4 Map `group_count` to the band table from [README § Scope Metrics](../../spec-driven-development/specs/README.md#scope-metrics):
    - `1` → COMPLIANT
    - `2` → MINOR
    - `3+` → SEVERE

### Phase 3 — Label each group

- [ ] 3.1 For each group, write a short human label (3–6 words) that names the seam — derived from the dominant shared signals. Examples: "decorator runtime", "built-in policies", "cancellation lifecycle".
- [ ] 3.2 List the shared signals that joined the ACs in the group, so a reviewer can see why the cluster formed.

### Phase 4 — Emit JSON

- [ ] 4.1 Write `{OUTPUT_DIR}/cohesion.json` matching `output.schema.json`. Include `group_count`, `severity`, `groups` (each with `label`, `acs`, `shared_signals`), and `spec_path`.

## Constraints

- Do NOT cluster on a single shared signal — the rule is 2-signal minimum, deliberately strict to avoid folding everything together via shared library names.
- Do NOT invent signals not present in the AC text. If an AC genuinely has no screen, its `screen` signal is `null` (not "main view").
- Do NOT rewrite or paraphrase ACs — refer to them by their assigned id (`US-{n}.{m}` or `STORY-{n}.{m}`).
- Group labels are advisory; humans rename when materialising subtasks.
