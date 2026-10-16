"""Applies effective project scoring bands to executable rule scopes."""

from dataclasses import replace
from typing import Protocol

from harness.flow_def import FlowDef
from harness.review_policy_resolution import ReviewPolicyResolution
from harness.step_def import StepDef


"""
solid-name: EffectiveMetricScoringApplying
solid-category: abstraction
solid-spec: [SPEC-039, SPEC-053]
solid-description: Contract for applying resolved metric scoring to executable workflows.
"""
class EffectiveMetricScoringApplying(Protocol):
    def apply(self, flow: FlowDef, policy: ReviewPolicyResolution) -> FlowDef: ...


"""
solid-name: EffectiveMetricScoringApplier
solid-category: service
solid-spec: [SPEC-039, SPEC-053, SPEC-057]
solid-description: Selects owned rule scopes and delegates effective scoring without mixing metric reconstruction into workflow traversal.
"""
class EffectiveMetricScoringApplier(EffectiveMetricScoringApplying):
    def __init__(self, scope_applier: EffectiveMetricScoringApplying) -> None:
        self._scope_applier = scope_applier

    def apply(self, flow: FlowDef, policy: ReviewPolicyResolution) -> FlowDef:
        rewritten_steps = list(flow.steps)
        included_rule_step_ids = {
            member_id
            for group in flow.alias_groups if group.rule_workflow is not None
            for member_id in group.member_ids
        }
        if flow.rule is not None:
            rewritten_steps = self._rewrite_scope(
                flow.workflow_id, rewritten_steps,
                [step.id for step in rewritten_steps if step.id not in included_rule_step_ids],
                policy,
            )
        for group in flow.alias_groups:
            if group.rule_workflow is not None:
                rewritten_steps = self._rewrite_scope(
                    group.rule_workflow.workflow_id, rewritten_steps, group.member_ids, policy,
                )
        return replace(flow, steps=rewritten_steps)

    def _rewrite_scope(
        self,
        workflow_id: str,
        steps: list[StepDef],
        member_ids: list[str],
        policy: ReviewPolicyResolution,
    ) -> list[StepDef]:
        member_id_set = set(member_ids)
        scope = FlowDef(
            id=workflow_id, name=workflow_id, max_turns=1,
            steps=[step for step in steps if step.id in member_id_set],
        )
        rewritten = self._scope_applier.apply(scope, policy)
        return [
            next((replacement for replacement in rewritten.steps if replacement.id == step.id), step)
            for step in steps
        ]
