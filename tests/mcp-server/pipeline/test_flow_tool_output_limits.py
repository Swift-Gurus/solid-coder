"""Verifies complete-response limits for model-facing flow tools."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

MCP_ROOT = Path(__file__).resolve().parents[3] / "mcp-server"
if str(MCP_ROOT) not in sys.path:
    sys.path.insert(0, str(MCP_ROOT))

from common.mcp_meta import COMPLETE_FLOW_OUTPUT  # noqa: E402
from pipeline.server import ApplicationBootstrapper  # noqa: E402


class TestFlowToolOutputLimits(unittest.TestCase):

    def test_start_and_next_preserve_one_complete_large_response(self) -> None:
        registry = Mock()
        flow_callables = Mock()
        flow_callables.build.return_value = {
            "flow_start": Mock(),
            "flow_next": Mock(),
            "flow_status": Mock(),
            "flow_clear_lock": Mock(),
        }
        bootstrapper = ApplicationBootstrapper(
            server=Mock(),
            registry=registry,
            tool_callables=Mock(),
            flow_callables=flow_callables,
        )

        bootstrapper._register_flow_tools()

        registrations = {
            call.args[0]: call
            for call in registry.register.call_args_list
        }
        self.assertEqual(
            registrations["flow_start"].kwargs["meta"],
            COMPLETE_FLOW_OUTPUT,
        )
        self.assertEqual(
            registrations["flow_next"].kwargs["meta"],
            COMPLETE_FLOW_OUTPUT,
        )


if __name__ == "__main__":
    unittest.main()
