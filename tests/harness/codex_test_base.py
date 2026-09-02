"""Declares the Codex model profile for reusable integration-test contracts."""

from typing import ClassVar

from codex_live_session_runner import CodexLiveSessionRunner
from live_session_running import LiveSessionRunning
from live_test_base import LiveTestBase


"""
solid-name: CodexTestBase
solid-category: test-support
solid-description: Supplies the Codex model-profile selection shared by live flow-engine and principle health-check integration tests.
"""
class CodexTestBase(LiveTestBase):

    MODEL_PROFILE: ClassVar[str] = "codex"
    FLOW_START_TOOL: ClassVar[str] = (
        "mcp__solid_coder_flow_engine__flow_start"
    )
    FLOW_NEXT_TOOL: ClassVar[str] = (
        "mcp__solid_coder_flow_engine__flow_next"
    )
    ALLOWED_FLOW_TOOLS: ClassVar[str] = (
        "mcp__solid-coder-flow-engine__flow_start,"
        "mcp__solid-coder-flow-engine__flow_next"
    )

    def flow_execution_instruction(
        self,
        workflow_id: str,
        parameters_json: str,
    ) -> str:
        return (
            "Inside functions.exec, directly await "
            f"tools.{self.FLOW_START_TOOL}({{flow: {workflow_id!r}, params: "
            f"{parameters_json}}}). Do not inspect ALL_TOOLS or search for tools. "
            "For each returned step, produce the requested JSON output and directly "
            f"call tools.{self.FLOW_NEXT_TOOL}({{outputs: "
            "{\"<returned-step-id>\": <JSON output>}}). Use that exact argument "
            "shape, replacing the placeholder key with the returned step_id. "
            "Continue until the flow reaches done, failed, or timed out. Do not "
            "edit files."
        )

    def live_session_runner(self) -> LiveSessionRunning:
        return CodexLiveSessionRunner()
