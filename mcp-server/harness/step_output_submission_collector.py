"""Collects named step-output values for schema validation."""

from harness.flow_def import FlowDef
from harness.step_instance import StepInstance
from harness.step_output_submission import StepOutputSubmission
from harness.step_output_submission_collecting import StepOutputSubmissionCollecting


"""
solid-name: StepOutputSubmissionCollector
solid-category: service
solid-spec: [SPEC-031, SPEC-039]
solid-description: Collects typed output specification and value records from ready workflow instances.
"""
class StepOutputSubmissionCollector(StepOutputSubmissionCollecting):
    def collect(
        self,
        ready: list[StepInstance],
        outputs: dict,
        flow_def: FlowDef,
    ) -> list[StepOutputSubmission]:
        step_map = {step.id: step for step in flow_def.steps}
        submissions: list[StepOutputSubmission] = []
        for instance in ready:
            step_def = step_map.get(instance.step_id)
            if step_def is None:
                continue
            instance_outputs = outputs.get(instance.instance_id, {})
            if not isinstance(instance_outputs, dict):
                continue
            submissions.extend(
                StepOutputSubmission(
                    instance_id=instance.instance_id,
                    specification=specification,
                    value=instance_outputs.get(specification.name),
                )
                for specification in step_def.outputs
            )
        return submissions
