"""Applies effective project scoring bands to executable rule metrics."""

from __future__ import annotations

from dataclasses import replace
from typing import Protocol

from harness.effective_metric_plan_entry import EffectiveMetricPlanEntry
from harness.effective_metric_plan_resolving import EffectiveMetricPlanResolving
from harness.flow_def import FlowDef
from harness.metric_declaration import MetricDeclaration
from harness.review_policy_resolution import ReviewPolicyResolution
from harness.rule_assessment_declaration import RuleAssessmentDeclaration
from harness.step_def import StepDef


"""
solid-name: EffectiveMetricScoringApplying
solid-category: abstraction
solid-spec: [SPEC-039, SPEC-053]
solid-description: Contract for applying resolved metric scoring to executable workflows.
"""
class EffectiveMetricScoringApplying(Protocol):
    def apply(
        self,
        flow: FlowDef,
        policy: ReviewPolicyResolution,
    ) -> FlowDef: ...


"""
solid-name: EffectiveMetricScoringApplier
solid-category: service
solid-spec: [SPEC-039, SPEC-053]
solid-description: Applies resolved metric scoring to executable workflows.
"""
class EffectiveMetricScoringApplier(EffectiveMetricScoringApplying):
    def __init__(
        self,
        plan_resolver: EffectiveMetricPlanResolving,
    ) -> None:
        self._plan_resolver = plan_resolver

    def apply(
        self,
        flow: FlowDef,
        policy: ReviewPolicyResolution,
    ) -> FlowDef:
        rewritten_steps = list(flow.steps)
        included_rule_step_ids = {
            member_id
            for group in flow.alias_groups
            if group.rule_workflow is not None
            for member_id in group.member_ids
        }

        if flow.rule is not None:
            rewritten_steps = self._rewrite_scope(
                flow.workflow_id,
                rewritten_steps,
                [
                    step.id
                    for step in rewritten_steps
                    if step.id not in included_rule_step_ids
                ],
                policy,
            )

        for group in flow.alias_groups:
            if group.rule_workflow is None:
                continue
            rewritten_steps = self._rewrite_scope(
                group.rule_workflow.workflow_id,
                rewritten_steps,
                group.member_ids,
                policy,
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
        scope_steps = [step for step in steps if step.id in member_id_set]
        plans = self._plan_resolver.resolve(
            FlowDef(
                id=workflow_id,
                name=workflow_id,
                max_turns=1,
                steps=scope_steps,
            ),
            policy,
        )
        return [
            self._rewrite_step(step, plans)
            if step.id in member_id_set
            else step
            for step in steps
        ]

    def _rewrite_step(
        self,
        step: StepDef,
        plans: list[EffectiveMetricPlanEntry],
    ) -> StepDef:
        metric = (
            self._rewrite_metric(step.metric, plans)
            if step.metric is not None
            else None
        )
        assessment = step.assessment
        if assessment is not None:
            assessment = RuleAssessmentDeclaration(
                supporting_outputs=assessment.supporting_outputs,
                metrics=[
                    self._rewrite_metric(declaration, plans)
                    for declaration in assessment.metrics
                ],
                exception_observation_id=assessment.exception_observation_id,
            )
        return replace(
            step,
            metric=metric,
            assessment=assessment,
        )

    def _rewrite_metric(
        self,
        metric: MetricDeclaration,
        plans: list[EffectiveMetricPlanEntry],
    ) -> MetricDeclaration:
        plan = next(
            entry
            for entry in plans
            if entry.metric_id == metric.metric_id
            and entry.observation_id == metric.observation_id
        )
        return MetricDeclaration(
            metric_id=metric.metric_id,
            observation_id=metric.observation_id,
            value=metric.value,
            scoring=plan.effective_scoring,
        )
