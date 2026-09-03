---
number: SPEC-043
feature: combined-rule-presentation
type: subtask
status: complete
parent: SPEC-010
blocked-by: [SPEC-037, SPEC-039, SPEC-042]
blocking: [SPEC-036]
---

# Combined Rule Presentation

## Description

Allow several independently materialized rule workflows to share one model-facing turn without merging their execution state. Rule discovery, policy enablement, applicability conditions, `for_each` instances, output validation, attempts, events, replay, scoring, and result aggregation remain authoritative per rule and per review unit. Combined presentation changes only how compatible ready work is rendered and how one nested response is mapped back to those existing instances.

The first consumer is the experimental single-prompt review bundle. SRP, OCP, and LSP may be presented together after their ordinary applicability decisions select them. ISP and DRY retain their current individual execution because they still require per-unit preparation/search context. This is an opt-in boundary, not a permanent exclusion: a later workflow may move that preparation to file scope and opt either rule into the same presentation contract without changing the engine.

## Input / Output

| | Detail |
|---|---|
| Input | An enclosing workflow group declaring `presentation.mode: combined`, containing compatible batched child workflows selected through existing conditions and policy |
| Output | One model instruction containing each selected rule prompt/schema once and a nested domain-keyed submission translated into ordinary per-instance outputs |
| Consumers | Experimental combined review workflows, later `rules: all` bundles, `flow_start`, `flow_next`, event replay, scoring, and Stop enforcement |

## User Stories

### US-1: Combine dynamically applicable rules

As a workflow author, I want all compatible rules selected for the current units presented together so I do not hardcode a second rule-selection mechanism or pay one model turn per rule.

**Acceptance Criteria:**

- An inline group may opt into combined presentation:

```yaml
- group: combined_unit_review
  presentation:
    mode: combined
  steps:
    - include:
        workflow: srp-single-prompt
      as: srp
      depends_on: [prepare_review]
      for_each:
        source: "{{steps.prepare_review.outputs.units}}"
        mode: batch
        label: "{{item.target.name}}"
      with:
        review_unit: "{{item}}"

    - include:
        workflow: ocp-single-prompt
      as: ocp
      depends_on: [prepare_review]
      for_each:
        source: "{{steps.prepare_review.outputs.units}}"
        mode: batch
        label: "{{item.target.name}}"
      with:
        review_unit: "{{item}}"
```

- `presentation.mode` accepts `individual` or `combined`; omission means `individual`.
- The enclosing group identity defines the combination boundary. Authors do not repeat an arbitrary presentation-group string on every child.
- Existing workflow conditions, rule matchers, scope adapters, and project policy decide which child instances exist and become ready. Presentation never reimplements or bypasses applicability.
- Only ready child agent steps with batch labels participate. Engine-owned steps drain normally, skipped rules remain absent, and unrelated ready steps remain outside the turn.
- The first supported rule shape is one ready aggregate agent step per included rule, as used by the existing single-prompt experiments. Granular multi-step rule workflows retain their current execution.
- ISP and DRY remain individually presented in the first experiment. Their exclusion is workflow configuration, not an engine special case or hardcoded rule-name list.

### US-2: Render one compact combined contract

As an agent, I want one instruction showing every applicable rule and unit clearly so I can return complete results without seeing engine identities.

**Acceptance Criteria:**

- Each selected rule section contains its authored alias, prompt, and output contract once.
- Each rule section lists the ordered domain labels to which it applies. Rules may apply to different subsets of units.
- Complete source buffers, normalized review objects, applicability metadata, internal include aliases, runtime instance IDs, indexes, and result envelopes are not rendered.
- The response envelope is nested first by exact domain label and then by exact authored rule alias:

```json
{
  "outputs": {
    "ReportComposer": {
      "srp": {"<declared SRP outputs>": "<values>"},
      "ocp": {"<declared OCP outputs>": "<values>"}
    }
  }
}
```

- A unit contains only the rule keys that MCP listed for that unit.
- Prompt/schema sections are assembled from typed ready-step data. Downstream code does not parse, split, deduplicate, or infer meaning from authored prompt strings.

### US-3: Preserve per-instance correctness

As the flow engine, I want one combined submission to retain the same correctness and audit guarantees as separate rule submissions.

**Acceptance Criteria:**

- MCP maps each `(domain label, authored rule alias)` pair to exactly one existing ready `StepInstance`.
- Unknown unit labels, unknown rule aliases, ambiguous labels, duplicate aliases, malformed result objects, and output-schema violations are rejected without guessing by order.
- Valid addressed pairs complete through the existing output validator and event recorder. No combined-result event or second scoring path is introduced.
- A valid partial response completes only addressed pairs. Missing unit/rule pairs remain pending and are returned in the next combined presentation.
- An invalid pair consumes only its existing instance attempt; valid sibling pairs remain complete and are not presented again.
- Dependents and final rule aggregation remain blocked until every non-skipped required instance has completed.
- Replay reconstructs the same completed, rejected, skipped, and pending instances from existing events and renders only pending domain/rule pairs.
- Existing Stop enforcement remains blocked while any required pair is pending because combined presentation completes the ordinary underlying instances rather than introducing a separate completion state.

### US-4: Preserve an extension path for ISP and DRY

As a workflow maintainer, I want ISP and DRY to keep working today without forcing their current per-unit preparation into the combined turn.

**Acceptance Criteria:**

- The experimental combined bundle leaves ISP and DRY outside the combined presentation group.
- Existing ISP and DRY workflows, search operations, source context, outputs, retries, and audit events remain unchanged.
- Combined presentation has no rule-name allowlist or denylist.
- A later file-scoped preparation step may produce typed contexts keyed by stable unit identity; once an ISP or DRY aggregate step no longer requires a distinct prompt per unit, its workflow may opt into the same group contract.

## Technical Requirements

- Parse presentation YAML once at the workflow boundary into a typed enum/declaration. Runtime services do not inspect raw mappings.
- Preserve combined ownership as typed include-group and workflow-instance metadata through qualification, dynamic materialization, snapshot persistence, and replay.
- Extend the existing SPEC-042 batch selection and submission lifecycle. Do not create a second fan-out, validation, event, replay, or scoring engine.
- Ordinary batch identity remains `(included workflow, authored step)`. Combined identity is the enclosing authored presentation group; each item additionally carries its authored child-rule alias.
- The renderer groups typed ready items by rule alias, verifies that each rule has one shared prompt, and lists its applicable domain labels.
- Boundary submission decoding may use JSON mappings. Application logic consumes typed targets representing domain label, rule alias, and internal instance identity.
- Combined presentation is valid only for agent-owned batched child steps. Invalid group shapes fail deterministically during validation or presentation; they do not silently fall back to another mode.

## Connects To

| Direction | Target | Relationship |
|---|---|---|
| Parent | SPEC-010 MCP-Driven Flow Orchestration | Extends model presentation while preserving the flow state machine |
| Upstream | SPEC-037 Conditional Routing and Result Aggregation | Supplies dynamic include materialization, conditions, nested ownership, and ordered results |
| Upstream | SPEC-039 Rule Workflow Discovery and Policy | Remains authoritative for rule selection, scope, and client overrides |
| Upstream | SPEC-042 Batched `for_each` Presentation | Supplies domain labels, partial completion, instance validation, retries, and replay |
| Downstream | SPEC-036 Bundled SOLID Workflows | Enables an experimental single-turn SRP/OCP/LSP comparison |

## Test Plan

- Parse an enclosing combined group and preserve its typed identity through snapshot serialization/reload.
- Qualify a combined group nested under another workflow without changing its authored child-rule aliases.
- Preserve an enclosing combined mode across `rules: all` expansion so future compatible catalog rules use the same capability.
- Reject unknown presentation modes and combined groups containing incompatible non-batched agent work.
- Materialize two child rule workflows over two units and assert four ordinary internal instances remain present.
- Apply different conditions to the two child rules and assert the rendered rule/unit matrix contains only applicable pairs.
- Assert each selected rule prompt/schema occurs once and no source buffer or internal instance identity is rendered.
- Submit every nested unit/rule result and assert existing per-instance completion events, ordered child outputs, and aggregate results.
- Submit a valid subset and assert only missing pairs are rendered after replay.
- Submit one invalid pair and assert only its instance attempt is consumed while valid pairs remain completed.
- Reject unknown unit and rule keys without completing any unrelated instance.
- Update the experimental single-prompt file-review bundle to combine SRP, OCP, and LSP while leaving ISP and DRY unchanged.
- Run all non-live, non-E2E tests after focused integration coverage passes.

## Definition of Done

- [x] Combined presentation is an explicit typed group-level workflow capability.
- [x] Existing applicability and policy determine the actual rule/unit matrix.
- [x] Each applicable rule prompt/schema is rendered once in a single model turn.
- [x] Nested domain/rule outputs map to existing instances and preserve validation, partial completion, retries, events, replay, aggregation, and scoring.
- [x] ISP and DRY remain unchanged and can opt in later without an engine redesign.
- [x] The experimental bundle and all non-live, non-E2E tests pass.
