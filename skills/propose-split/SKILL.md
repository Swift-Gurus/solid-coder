---
name: propose-split
description: Produce a full split plan when scope-assessment recommends splitting a spec. Reads the original spec for context, partitions TR + Connects To across candidate subtasks, identifies parent-level residue and inter-subtask dependencies. Internal skill — invoked by validate-spec Phase C only when verdict == needs_split.
argument-hint: <spec-path> <output-dir>
allowed-tools: Read, Write, Bash
user-invocable: false
---

# Propose Split

## Input

- SPEC_PATH: `$ARGUMENTS[0]` — absolute path to the spec's `Spec.md`
- OUTPUT_DIR: `$ARGUMENTS[1]` — directory containing `scope-assessment.json` from the synthesis pass; the skill writes `split-plan.json` here.

## Workflow

### Phase 0 — Preconditions

- [ ] 0.1 Read `{OUTPUT_DIR}/scope-assessment.json`. If `verdict != "needs_split"`, write a minimal `split-plan.json` with `{"applicable": false, "reason": "<verdict>"}` and exit. Do not proceed.
- [ ] 0.2 Read the spec file in full. You will need its `## Description`, `## Input / Output`, `## User Stories` (with ACs), `## Technical Requirements`, `## Connects To`, and `## Diagrams` to partition them across candidates.

### Phase 1 — Branch on driver

The split plan shape depends on `scope-assessment.split_recommendation.driver`:

- **`driver == "cohesion"`** — the cohesion subagent already grouped the ACs. Each group becomes a candidate subtask. Proceed to Phase 2.
- **`driver == "size"`** — the unit is genuinely cohesive but large (oversized_cohesive). The split is by **extraction**, not by responsibility seam. Proceed to Phase 3.

### Phase 2 — Cohesion-driven split (per group)

For each entry in `scope-assessment.split_recommendation.candidate_subtasks`, build a full subtask plan:

- [ ] 2.1 **Title** — copy from the candidate's `title` (from cohesion's group label). Refine if a clearer name is implied by the partitioned content.
- [ ] 2.2 **Description** — 2–4 sentences that take the focused subset of the parent's purpose, framed by what this subtask delivers in isolation. Do NOT copy the parent description verbatim.
- [ ] 2.3 **User story** — the parent's user story(ies) whose ACs landed in this group. Keep the AC narrative; carry the AC bullets unchanged. If multiple parent stories contributed ACs, merge them into one focused story.
- [ ] 2.4 **Acceptance criteria** — list the ACs from `candidate_subtasks[].acs`. Quote the AC text verbatim from the parent spec — find each by its id.
- [ ] 2.5 **Input / Output** — copy only the rows from the parent's IO table that this subtask actually consumes/produces. Drop rows owned by sibling candidates.
- [ ] 2.6 **Technical Requirements** — partition the parent's TR bullets:
    - Each TR bullet either supports this candidate's ACs (move it here) or is shared infrastructure (keep at parent index level — see Phase 4).
    - When a TR bullet describes a mechanism that crosses candidates, split it: keep the part relevant here, note the rest under the relevant sibling.
    - Mark each moved TR with its source bullet from the parent so the partition is auditable.
- [ ] 2.7 **Connects To** — partition the parent's table:
    - Upstream rows whose target this candidate uses → here.
    - Downstream rows whose consumer is this candidate's output → here.
    - Add a new "depends on (sibling)" row when this candidate's output is consumed by another candidate. Use the candidate's title as the target.
- [ ] 2.8 **Definition of Done** — the parent DoD items that close on this candidate's deliverable. Drop items closing on sibling deliverables.

### Phase 3 — Size-driven extraction (oversized_cohesive)

When `driver == "size"`, there is no semantic seam. Suggest **extraction candidates** — types or sub-components that could ship as their own subtasks while keeping the cohesive core intact:

- [ ] 3.1 Read the spec's TR + Connects To. Identify candidates by these heuristics:
    - **Helper types** mentioned by name (errors, formatters, builders, configurations).
    - **Distinct external integrations** that could be owned by a thin adapter (e.g. a logger wrapper).
    - **Self-contained algorithms** (a retry policy, a cache eviction strategy) that are referenced but not woven into the main behavior.
- [ ] 3.2 For each extraction candidate, produce a thin subtask plan: title, one-sentence rationale, the TR bullets that would move with it. Skip the full Description/IO/DoD partition — these are extraction proposals, not full splits.
- [ ] 3.3 The parent stays as-is structurally; the candidates are sized estimates only. Mark with `kind: "extraction"` to distinguish from cohesion-driven candidates.

### Phase 4 — Parent residue (cohesion-driven only)

When the parent is being converted to an index:

- [ ] 4.1 **Description** — keep the parent description, reframed to describe the index role ("this feature comprises N subtasks…").
- [ ] 4.2 **Connects To (parent-level)** — upstream rows that aren't claimed by any single candidate (e.g. parent-level integrations consumed by all children).
- [ ] 4.3 **Diagrams** — keep the high-level connection + flow diagrams. Detailed sequence diagrams move with the candidate that owns the interaction.
- [ ] 4.4 **Subtasks list** — generate the markdown table for the parent's new `## Subtasks` section, one row per candidate, with placeholder spec numbers.
- [ ] 4.5 The parent's TR section is removed (an index has no own TR). Same for own ACs.

### Phase 5 — Inter-subtask dependencies

- [ ] 5.1 Walk the candidate subtasks pairwise. If candidate A's output is consumed by candidate B (per the partitioned IO + Connects To), record `B.blocked_by = [A]`.
- [ ] 5.2 Detect cycles. If found, fail with a clear error — the cohesion grouping has produced an architecturally invalid split and the spec needs human review.
- [ ] 5.3 Topologically order the candidates so the dependency graph is satisfiable.

### Phase 6 — Rationale

- [ ] 6.1 Write a short `split_rationale` summarising why this split (3–5 sentences). Reference the cohesion `shared_signals` for cohesion-driven splits, or the extraction heuristics for size-driven.

### Phase 7 — Emit JSON

- [ ] 7.1 Write `{OUTPUT_DIR}/split-plan.json` matching `output.schema.json`. Include `applicable: true`, `driver`, `parent_residue` (cohesion-driven only), `candidate_subtasks` (with full per-candidate breakdown), `dependency_order`, and `split_rationale`.

## Output

`{OUTPUT_DIR}/split-plan.json`. Consumed by validate-spec Phase 4 reporting and (future) by `build-spec` to materialise the candidate subtask spec files.

## Constraints

- Do NOT generate Spec.md files. The plan is a blueprint; materialisation is a separate concern (build-spec or human).
- Do NOT invent ACs, TR bullets, or connections that don't exist in the parent spec. Partition only.
- Do NOT modify the parent spec.
- Do NOT propose a split when the verdict is not `needs_split` — exit early with `applicable: false`.
- Quote AC text verbatim — do not paraphrase. The plan must be reviewable against the original spec word-for-word.
