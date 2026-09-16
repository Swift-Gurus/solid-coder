"""Collects aggregate assignments from original ready step results."""

from typing import cast

from harness.aggregate_assignment import AggregateAssignment
from harness.aggregate_assignment_collecting import AggregateAssignmentCollecting
from harness.aggregate_assignment_presentation import AggregateAssignmentPresentation
from harness.aggregate_step_rejection import AggregateStepRejection
from harness.step_result import StepResult


"""
solid-name: AggregateAssignmentCollector
solid-category: service
solid-spec: [SPEC-045, SPEC-052]
solid-description: Groups original aggregate step results by opaque item label and workflow alias.
"""
class AggregateAssignmentCollector(AggregateAssignmentCollecting):
    def collect(self, steps: list[StepResult]) -> list[AggregateAssignment]:
        assignments: list[AggregateAssignment] = []
        for step in steps:
            presentation = cast(AggregateAssignmentPresentation, step.batch)
            rejections: list[AggregateStepRejection] = []
            if step.rejection_reason is not None:
                rejections.append(
                    AggregateStepRejection(
                        step_id=presentation.authored_step.step_id,
                        reason=step.rejection_reason,
                    )
                )
            matching_index = next(
                (
                    index
                    for index, assignment in enumerate(assignments)
                    if assignment.item_label == presentation.label
                    and assignment.workflow_alias == presentation.workflow_alias
                ),
                None,
            )
            if matching_index is None:
                assignments.append(
                    AggregateAssignment(
                        item_label=presentation.label,
                        workflow_alias=presentation.workflow_alias,
                        instance_id=step.instance_id,
                        steps=[presentation.authored_step],
                        rejections=rejections,
                    )
                )
                continue
            assignment = assignments[matching_index]
            assignments[matching_index] = AggregateAssignment(
                item_label=assignment.item_label,
                workflow_alias=assignment.workflow_alias,
                instance_id=assignment.instance_id,
                steps=[*assignment.steps, presentation.authored_step],
                rejections=[*assignment.rejections, *rejections],
            )
        return assignments
