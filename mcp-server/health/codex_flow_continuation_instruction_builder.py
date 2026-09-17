"""Builds flow-continuation guidance for Codex deferred MCP tools."""

from flow_continuation_instruction_building import (
    FlowContinuationInstructionBuilding,
)


_FLOW_NEXT_TOOL = "tools.mcp__solid_coder_flow_engine__flow_next"


"""
solid-name: CodexFlowContinuationInstructionBuilder
solid-category: service
solid-spec: [SPEC-047, SPEC-052]
solid-description: Produces deferred flow-continuation guidance for model sessions.
"""
class CodexFlowContinuationInstructionBuilder(
    FlowContinuationInstructionBuilding,
):
    def build(self, run_id: str) -> str:
        return (
            "Inside functions.exec, construct the requested outputs incrementally "
            "with this generic JavaScript scaffold:\n\n"
            "const outputs = {};\n"
            "const assign = (path, value) => {\n"
            "  let cursor = outputs;\n"
            "  for (let index = 0; index < path.length - 1; index += 1) {\n"
            "    cursor[path[index]] ??= {};\n"
            "    cursor = cursor[path[index]];\n"
            "  }\n"
            "  cursor[path[path.length - 1]] = value;\n"
            "};\n\n"
            "// Add one assign call for every required schema leaf, using the "
            "exact path rendered by the current instruction.\n"
            "// assign([\"exact\", \"schema\", \"path\"], value);\n\n"
            f"const result = await {_FLOW_NEXT_TOOL}({{\n"
            f'  run_id: "{run_id}", outputs\n'
            "});\n"
            "text(result);\n\n"
            "Do not inline the complete nested object in the flow_next call. "
            "Call flow_next once after every required assignment has been added. "
            "Do not inspect ALL_TOOLS. Do not search for tools.\n\n"
            "If functions.exec reports a JavaScript or script error, the submission "
            "did not reach flow_next. Stay in the same model session, keep the same "
            "run_id, reuse the completed analysis, reconstruct the complete outputs "
            "object from an empty object with the scaffold, and Call flow_next once. "
            "Do not call flow_start and do not split one requested submission across "
            "multiple flow_next calls.\n\n"
            "If flow_next returns a validation rejection, follow the returned "
            "recovery contract. When it says accepted assignments are already saved, "
            "construct and submit only the pending or rejected subset described by "
            "the returned schema. Follow each returned instruction with this same "
            "flow_next tool until it reports completion or failure."
        )
