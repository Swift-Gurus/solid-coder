"""Applies typed conditions after workflow-step instance expansion."""

from __future__ import annotations

from typing import Any

from harness.condition_decision_evaluating import ConditionDecisionEvaluating
from harness.models import RunState, StepDef, StepInstance
from harness.step_instance_expanding import StepInstanceExpanding
from harness.step_skip import StepSkip


"""
solid-name: ConditionalStepInstanceExpander
solid-category: service
solid-spec: [SPEC-037]
solid-description: Applies a step condition independently to each expanded workflow instance.
"""
class ConditionalStepInstanceExpander(StepInstanceExpanding):
    def __init__(
        self,
        instance_expander: StepInstanceExpanding,
        condition_evaluator: ConditionDecisionEvaluating,
    ) -> None:
        self._instance_expander = instance_expander
        self._condition_evaluator = condition_evaluator

    def expand(
        self,
        step: StepDef,
        context: dict[str, Any],
        run_state: RunState,
    ) -> list[StepInstance]:
        instances = self._instance_expander.expand(step, context, run_state)
        if step.condition is None:
            return instances
        return [
            self._apply_condition(step, instance, context)
            for instance in instances
        ]

    def _apply_condition(
        self,
        step: StepDef,
        instance: StepInstance,
        context: dict[str, Any],
    ) -> StepInstance:
        if instance.automatic_outputs is not None:
            return instance
        condition = step.condition
        if condition is None or self._condition_evaluator.evaluate(
            condition,
            {**context, "item": instance.item},
        ):
            return instance
        return StepInstance(
            step_id=instance.step_id,
            instance_id=instance.instance_id,
            item=instance.item,
            prompt=instance.prompt,
            iteration_index=instance.iteration_index,
            automatic_outputs=instance.automatic_outputs,
            skip=StepSkip(
                step_id=instance.step_id,
                instance_id=instance.instance_id,
                condition=condition,
                item=instance.item,
                iteration_index=instance.iteration_index,
            ),
        )
