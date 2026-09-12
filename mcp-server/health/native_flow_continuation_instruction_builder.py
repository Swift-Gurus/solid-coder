"""Builds flow-continuation guidance for native MCP tool callers."""

from flow_continuation_instruction_building import (
    FlowContinuationInstructionBuilding,
)


"""
solid-name: NativeFlowContinuationInstructionBuilder
solid-category: service
solid-spec: [SPEC-047]
solid-description: Directs a native MCP caller to continue one existing isolated flow run.
"""
class NativeFlowContinuationInstructionBuilder(
    FlowContinuationInstructionBuilding,
):
    def build(self, run_id: str) -> str:
        return (
            "Submit the requested outputs with flow_next and "
            f'run_id="{run_id}". Follow each returned instruction and continue '
            "with flow_next until it reports completion or failure."
        )
