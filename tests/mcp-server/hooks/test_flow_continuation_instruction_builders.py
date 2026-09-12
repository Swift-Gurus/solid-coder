"""Tests backend-specific flow continuation guidance."""

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path


ensure_on_path(
    Path(__file__).resolve().parents[3] / "mcp-server",
    Path(__file__).resolve().parent,
)

from codex_flow_continuation_instruction_builder import (  # noqa: E402
    CodexFlowContinuationInstructionBuilder,
)
from native_flow_continuation_instruction_builder import (  # noqa: E402
    NativeFlowContinuationInstructionBuilder,
)


"""
solid-name: TestFlowContinuationInstructionBuilders
solid-category: unit-test
solid-spec: [SPEC-047]
solid-description: Verifies isolated child sessions receive directly callable backend-specific flow guidance.
"""
class TestFlowContinuationInstructionBuilders(unittest.TestCase):
    def test_codex_instruction_uses_deferred_tool_without_discovery(self) -> None:
        instruction = CodexFlowContinuationInstructionBuilder().build("gate-run")

        self.assertIn(
            "tools.mcp__solid_coder_flow_engine__flow_next",
            instruction,
        )
        self.assertIn('run_id: "gate-run"', instruction)
        self.assertIn("Do not inspect ALL_TOOLS", instruction)
        self.assertIn("Do not search for tools", instruction)

    def test_native_instruction_uses_registered_flow_next_tool(self) -> None:
        instruction = NativeFlowContinuationInstructionBuilder().build("gate-run")

        self.assertIn("flow_next", instruction)
        self.assertIn('run_id="gate-run"', instruction)
        self.assertNotIn("functions.exec", instruction)


if __name__ == "__main__":
    unittest.main()
