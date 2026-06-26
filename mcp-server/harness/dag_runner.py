"""
solid-description: Determines which workflow steps are ready to execute based on their dependencies and run state.
solid-category: service
"""

from __future__ import annotations

import re
from typing import Any

from harness.dag_running import DAGRunning
from harness.expression_evaluating import ExpressionEvaluating
from harness.interpolator import TemplateRendering
from harness.models import FlowDef, RunState, StepDef, StepInstance

_SINGLE_EXPR = re.compile(r"^\{\{([^}]+)\}\}$")


class DAGRunner:
    """
    solid-description: Determines which workflow steps are ready to execute based on their dependencies and run state.
    solid-category: service
    """

    def __init__(self, renderer: TemplateRendering, evaluator: ExpressionEvaluating) -> None:
        self._renderer = renderer
        self._evaluator = evaluator

    def ready_steps(self, flow_def: FlowDef, run_state: RunState, context: dict[str, Any]) -> list[StepInstance]:
        if run_state.turn_count >= flow_def.max_turns:
            return []
        return [
            instance
            for step in flow_def.steps
            if not self._is_done_or_running(step.id, run_state)
            and self._dependencies_met(step, run_state)
            for instance in self._expand(step, context)
        ]

    def _is_done_or_running(self, step_id: str, run_state: RunState) -> bool:
        return step_id in run_state.completed or step_id in run_state.running

    def _dependencies_met(self, step: StepDef, run_state: RunState) -> bool:
        return all(dep in run_state.completed for dep in step.depends_on)

    def _expand(self, step: StepDef, context: dict[str, Any]) -> list[StepInstance]:
        if step.for_each is None:
            prompt = self._renderer.render(step.prompt, context)
            return [StepInstance(step_id=step.id, instance_id=f"{step.id}-1", item=None, prompt=prompt)]

        m = _SINGLE_EXPR.match(step.for_each.strip())
        expr = m.group(1).strip() if m else step.for_each.strip()
        value = self._evaluator.evaluate(expr, context)
        items = value if isinstance(value, list) else [value]

        return [
            StepInstance(
                step_id=step.id,
                instance_id=f"{step.id}-{i + 1}",
                item=item,
                prompt=self._renderer.render(step.prompt, {**context, "item": item}),
            )
            for i, item in enumerate(items)
        ]
