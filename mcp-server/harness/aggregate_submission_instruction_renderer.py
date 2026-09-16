"""Renders the submission contract for an aggregate model turn."""

from harness.aggregate_assignment_recovery_reading import (
    AggregateAssignmentRecoveryReading,
)


"""
solid-name: AggregateSubmissionInstructionRenderer
solid-category: service
solid-spec: [SPEC-052]
solid-description: Explains how the model submits or corrects aggregate results.
"""
class AggregateSubmissionInstructionRenderer:
    def render(
        self,
        assignments: list[AggregateAssignmentRecoveryReading],
    ) -> str:
        corrections = [
            f"- Item: {assignment.item_label}\n"
            f"  Workflow: {assignment.workflow_alias}\n"
            f"  Step: {rejection.step_id}\n"
            f"  Error: {rejection.reason}"
            for assignment in assignments
            for rejection in assignment.rejections
        ]
        if not corrections:
            return (
                "Call flow_next with one JSON object matching this schema. "
                "Do not include undeclared keys:"
            )

        correction_text = "\n".join(corrections)
        return (
            "Some assignments were rejected. Accepted assignments are already "
            "saved; do not resend them.\n"
            "Correct the following assignments:\n"
            f"{correction_text}\n"
            "Submit one JSON object containing only the pending or rejected "
            "assignments shown below. Match this schema exactly and do not "
            "include undeclared keys:"
        )
