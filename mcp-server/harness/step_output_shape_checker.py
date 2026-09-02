"""Checks submitted workflow instance output container shapes."""

from harness.step_instance import StepInstance
from harness.step_output_shape_checking import StepOutputShapeChecking


"""
solid-name: StepOutputShapeChecker
solid-category: service
solid-spec: [SPEC-031, SPEC-039]
solid-description: Reports workflow instance outputs that are not object maps keyed by output name.
"""
class StepOutputShapeChecker(StepOutputShapeChecking):
    def errors(
        self,
        ready: list[StepInstance],
        outputs: dict,
    ) -> list[str]:
        errors: list[str] = []
        for instance in ready:
            instance_outputs = outputs.get(instance.instance_id, {})
            if not isinstance(instance_outputs, dict):
                errors.append(
                    "submitted outputs must be an object mapping output "
                    f"names to values, got {type(instance_outputs).__name__}"
                )
        return errors
