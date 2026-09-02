"""Tests model-facing MCP result formatting."""

import sys
import unittest
from pathlib import Path

_MCP_SERVER = Path(__file__).resolve().parents[2] / "mcp-server"
if str(_MCP_SERVER) not in sys.path:
    sys.path.insert(0, str(_MCP_SERVER))

from tool_result_formatter import ToolResultFormatter  # noqa: E402


"""
solid-name: TestToolResultFormatter
solid-category: unit-test
solid-description: Verifies MCP results remain internal tool content and never instruct the model to echo them to the user.
"""
class TestToolResultFormatter(unittest.TestCase):

    def test_returns_plain_internal_text_without_display_instruction(self) -> None:
        result = ToolResultFormatter().format("id: verb_count-1")

        self.assertEqual(
            result,
            {
                "content": [{"type": "text", "text": "id: verb_count-1"}],
                "isError": False,
            },
        )

    def test_preserves_error_classification_without_display_instruction(self) -> None:
        result = ToolResultFormatter().format("** invalid output")

        self.assertEqual(
            result,
            {
                "content": [{"type": "text", "text": "** invalid output"}],
                "isError": True,
            },
        )


if __name__ == "__main__":
    unittest.main()
