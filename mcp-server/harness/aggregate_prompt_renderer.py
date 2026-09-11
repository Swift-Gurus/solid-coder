"""Renders compact aggregate instructions and applicability."""

from harness.aggregate_assignment import AggregateAssignment
from harness.aggregate_item_assignment import AggregateItemAssignment
from harness.aggregate_prompt_rendering import AggregatePromptRendering
from harness.authored_step_coordinate import AuthoredStepCoordinate


"""
solid-name: AggregatePromptRenderer
solid-category: service
solid-spec: [SPEC-045]
solid-description: Renders unique authored step instructions and opaque aggregate item assignments.
"""
class AggregatePromptRenderer(AggregatePromptRendering):
    def render(self, assignments: list[AggregateAssignment]) -> str:
        authored_steps: list[AuthoredStepCoordinate] = []
        item_assignments: list[AggregateItemAssignment] = []

        for assignment in assignments:
            item = next(
                (
                    candidate
                    for candidate in item_assignments
                    if candidate.label == assignment.item_label
                ),
                None,
            )
            if item is None:
                item = AggregateItemAssignment(label=assignment.item_label)
                item_assignments.append(item)
            if assignment.workflow_alias not in item.workflow_aliases:
                item.workflow_aliases.append(assignment.workflow_alias)

            for step in assignment.steps:
                already_present = any(
                    candidate.workflow_id == step.workflow_id
                    and candidate.step_id == step.step_id
                    for candidate in authored_steps
                )
                if not already_present:
                    authored_steps.append(step)

        instruction_text = "\n\n".join(
            f"Workflow: {step.workflow_id}\nStep: {step.step_id}\n{step.prompt}"
            for step in authored_steps
        )
        assignment_text = "\n".join(
            f"{item.label}: {', '.join(item.workflow_aliases)}"
            for item in item_assignments
        )
        return (
            "Follow each authored step below in order.\n\n"
            f"{instruction_text}\n\n"
            "Assignments:\n"
            f"{assignment_text}"
        )
