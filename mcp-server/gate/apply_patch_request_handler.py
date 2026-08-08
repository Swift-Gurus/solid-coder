"""Handles one parsed apply_patch gate request."""

from apply_patch_reviewing import ApplyPatchReviewing
from gate_handling import GateHandling


"""
solid-name: ApplyPatchRequestHandler
solid-category: service
solid-description: Reviews an entire patch and emits its single aggregated gate response.
solid-tags: [hook]
"""
class ApplyPatchRequestHandler:
    def __init__(
        self,
        reviewer: ApplyPatchReviewing,
        gate: GateHandling,
    ) -> None:
        self._reviewer = reviewer
        self._gate = gate

    def handle(self, parsed: tuple) -> None:
        _, tool_input, _, session_id, cwd = parsed
        decision = self._reviewer.review(tool_input, session_id, cwd)
        if decision.allow:
            self._gate.allow(decision.additional_context or "")
            return
        self._gate.block(
            decision.reason or "Patch review failed.",
            decision.additional_context or "",
        )
