"""Builds flow-continuation guidance for Codex deferred MCP tools."""

from flow_continuation_instruction_building import (
    FlowContinuationInstructionBuilding,
)


_FLOW_NEXT_TOOL = "tools.mcp__solid_coder_flow_engine__flow_next"


"""
solid-name: CodexFlowContinuationInstructionBuilder
solid-category: service
solid-spec: [SPEC-047]
solid-description: Produces deferred MCP flow-continuation guidance for Codex sessions.
"""
class CodexFlowContinuationInstructionBuilder(
    FlowContinuationInstructionBuilding,
):
    def build(self, run_id: str) -> str:
        return (
            "Inside functions.exec, directly await "
            f'{_FLOW_NEXT_TOOL}({{run_id: "{run_id}", outputs: '
            '{"<returned-step-id>": <JSON output>}}). '
            "Do not inspect ALL_TOOLS. Do not search for tools. Follow each "
            "returned instruction and continue with the same flow_next tool until "
            "it reports completion or failure."
        )
