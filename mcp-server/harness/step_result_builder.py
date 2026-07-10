"""
solid-name: StepResultBuilder
solid-category: service
solid-spec: [SPEC-013]
solid-description: Converts step instances to step results with resolved execution intent.
"""

from __future__ import annotations

from harness.execution_intent_resolving import ExecutionIntentResolving
from harness.models import FlowDef, StepInstance
from harness.step_result import StepResult
from harness.step_result_building import StepResultBuilding


class StepResultBuilder:

    def __init__(self, intent_resolver: ExecutionIntentResolving) -> None:
        self._intent_resolver = intent_resolver

    def build(self, instances: list[StepInstance], flow_def: FlowDef, detected_env: str) -> list[StepResult]:
        step_map = {s.id: s for s in flow_def.steps}
        results = []
        for instance in instances:
            step_def = step_map.get(instance.step_id)
            intent = step_def.execution.intent if (step_def and step_def.execution) else "inline"
            results.append(StepResult(
                step_id=instance.step_id,
                instance_id=instance.instance_id,
                prompt=instance.prompt,
                execution=self._intent_resolver.resolve(intent, detected_env),
            ))
        return results