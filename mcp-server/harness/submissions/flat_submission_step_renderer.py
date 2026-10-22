"""Renders addressed results without nested item/rule/step envelopes."""

from harness.aggregate_step_schema_building import AggregateStepSchemaBuilding
from harness.authored_step_coordinate import AuthoredStepCoordinate
from harness.batch_step_rendering import BatchStepRendering
from harness.step_result import StepResult
from json_serializer import JsonSerializing


"""
solid-name: FlatSubmissionStepRenderer
solid-category: service
solid-spec: [SPEC-068]
solid-description: Presents deduplicated authored instructions and original result schemas with flat pending assignment addresses.
"""
class FlatSubmissionStepRenderer(BatchStepRendering):
    def __init__(self, schema_builder: AggregateStepSchemaBuilding, serializer: JsonSerializing) -> None:
        self._schema_builder = schema_builder
        self._serializer = serializer

    def render(self, steps: list[StepResult]) -> str:
        instructions: list[AuthoredStepCoordinate] = []
        sections: list[str] = []
        assignments: list[str] = []
        for step in steps:
            authored = step.authored_step
            if authored is None or step.submission_id is None:
                raise ValueError("Flat presentation requires an authored output contract and a persisted submission ID")
            matching = next((index for index, entry in enumerate(instructions)
                             if entry.workflow_id == authored.workflow_id
                             and entry.step_id == authored.step_id), None)
            if matching is None:
                matching = len(instructions)
                instructions.append(authored)
                schema = self._schema_builder.build(authored)
                sections.append(
                    f"Instruction {matching + 1}: {authored.workflow_id} / {authored.step_id}\n"
                    f"{authored.prompt}\nResult schema:\n"
                    f"{self._serializer.serialize(schema.model_dump(by_alias=True))}"
                )
            target = step.batch.label if step.batch is not None else step.instance_id
            assignment = f"{step.submission_id}: target {target}; instruction {matching + 1}"
            if step.rejection_reason is not None:
                assignment += f"\nRejected: {step.rejection_reason}"
            assignments.append(assignment)
        return (
            "Follow the authored instructions for every pending assignment below.\n\n"
            + "\n\n".join(sections)
            + "\n\nPending assignments:\n" + "\n".join(assignments)
            + '\n\nCall flow_next with outputs: {"submissions": [{"id": "<assignment ID>", "result": {"<named output>": "<value>"}}]}. '
            "Each result must match its instruction's result schema. Use each ID at most once. "
            "Accepted assignments are already saved; do not resend them. "
            "For a rejected or omitted assignment, send its complete result, not a field-level patch. "
            "You may submit a subset; all remaining assignments stay pending."
        )
