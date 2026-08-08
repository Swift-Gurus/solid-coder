"""
solid-name: StepOutputValidator
solid-category: service
solid-spec: [SPEC-031]
solid-description: Validates step output values against their declared specifications.
"""

from __future__ import annotations

from harness.models import FlowDef, OutputSpec, StepInstance
from harness.schema_validator import SchemaValidator
from harness.step_output_validating import StepOutputValidating


class StepOutputValidator:

    def __init__(self, schema_validator: SchemaValidator) -> None:
        self._schema_validator = schema_validator

    def validate(
        self,
        ready: list[StepInstance],
        outputs: dict,
        flow_def: FlowDef,
    ) -> list[str]:
        errors: list[str] = list(self._shape_errors(ready, outputs))
        for output_spec, value in self._pairs(ready, outputs, flow_def):
            result = self._schema_validator.validate(output_spec, value)
            if not result.ok:
                errors.extend(result.errors)
        return errors

    def _shape_errors(self, ready: list[StepInstance], outputs: dict) -> list[str]:
        errors: list[str] = []
        for instance in ready:
            instance_outputs = outputs.get(instance.instance_id, {})
            if not isinstance(instance_outputs, dict):
                errors.append(
                    f"outputs for '{instance.instance_id}' must be an object mapping output "
                    f"names to values, got {type(instance_outputs).__name__}"
                )
        return errors

    def _pairs(
        self,
        ready: list[StepInstance],
        outputs: dict,
        flow_def: FlowDef,
    ) -> list[tuple[OutputSpec, object]]:
        step_map = {s.id: s for s in flow_def.steps}
        pairs: list[tuple[OutputSpec, object]] = []
        for instance in ready:
            step_def = step_map.get(instance.step_id)
            if step_def is None:
                continue
            instance_outputs = outputs.get(instance.instance_id, {})
            if not isinstance(instance_outputs, dict):
                continue
            for spec in step_def.outputs:
                pairs.append((spec, instance_outputs.get(spec.name)))
        return pairs