"""
solid-name: StepFormatter
solid-category: service
solid-spec: [SPEC-013]
solid-description: Transforms step information into formatted text for the calling agent.
"""

from __future__ import annotations

from harness.step_formatting import StepFormatting


class StepFormatter(StepFormatting):

    def format(self, instance_id: str, body: str, rejection_reason: str | None) -> str:
        header = f"id: {instance_id}"
        if rejection_reason is not None:
            header = f"{header}\nRejected: {rejection_reason}. Try again."
        return f"{header}\n\n{body}"