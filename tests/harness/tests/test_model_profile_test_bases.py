"""
solid-name: test_model_profile_test_bases
solid-category: unit-test
solid-description: Verifies reusable backend test bases select the expected model profiles and live-session adapters.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from claude_live_session_runner import ClaudeLiveSessionRunner
from claude_test_base import ClaudeTestBase
from codex_live_session_runner import CodexLiveSessionRunner
from codex_test_base import CodexTestBase
from flow_engine.flow_engine_e2e_live_base import FlowEngineE2ELiveBase
from live_test_base import LiveTestBase
from local_test_base import LocalTestBase


class TestModelProfileTestBases(unittest.TestCase):
    def test_live_backends_use_callable_flow_lifecycle_names(self) -> None:
        self.assertEqual(
            CodexTestBase.FLOW_START_TOOL,
            "flow_start",
        )
        self.assertEqual(
            CodexTestBase.FLOW_NEXT_TOOL,
            "flow_next",
        )
        self.assertEqual(ClaudeTestBase.FLOW_START_TOOL, "flow_start")
        self.assertEqual(ClaudeTestBase.FLOW_NEXT_TOOL, "flow_next")
        self.assertEqual(
            CodexTestBase.ALLOWED_FLOW_TOOLS,
            (
                "mcp__solid-coder-flow-engine__flow_start,"
                "mcp__solid-coder-flow-engine__flow_next"
            ),
        )
        self.assertEqual(
            ClaudeTestBase.ALLOWED_FLOW_TOOLS,
            (
                "mcp__plugin_solid-coder_flow-engine__flow_start,"
                "mcp__plugin_solid-coder_flow-engine__flow_next"
            ),
        )

    def test_codex_base_selects_profile_and_runner(self) -> None:
        base = CodexTestBase()

        self.assertEqual(base.MODEL_PROFILE, "codex")
        self.assertIsInstance(base.live_session_runner(), CodexLiveSessionRunner)

    def test_codex_flow_request_uses_shared_bootstrap_and_mcp_instructions(
        self,
    ) -> None:
        instruction = CodexTestBase().flow_execution_instruction(
            workflow_id="solid-review",
            parameters_json='{"target":{"kind":"file","path":"/project/A.swift"}}',
        )

        self.assertIn(
            "Call flow_start with flow='solid-review' and params equal to this JSON: "
            '{"target":{"kind":"file","path":"/project/A.swift"}}.',
            instruction,
        )
        self.assertIn(
            "Follow the instructions and submission schema returned by MCP",
            instruction,
        )
        self.assertNotIn("functions.exec", instruction)
        self.assertNotIn("<returned-step-id>", instruction)
        self.assertNotIn("ALL_TOOLS", instruction)

    def test_backends_inherit_the_same_workflow_request(self) -> None:
        self.assertIs(
            CodexTestBase.flow_execution_instruction,
            LiveTestBase.flow_execution_instruction,
        )
        self.assertIs(
            ClaudeTestBase.flow_execution_instruction,
            LiveTestBase.flow_execution_instruction,
        )

    def test_backend_requests_do_not_duplicate_recovery_policy(self) -> None:
        instruction = CodexTestBase().flow_execution_instruction("fixture", "{}")

        self.assertEqual(
            instruction,
            ClaudeTestBase().flow_execution_instruction("fixture", "{}"),
        )
        self.assertNotIn("retry", instruction.lower())
        self.assertNotIn("outputs:", instruction)

    def test_claude_base_selects_profile_and_runner(self) -> None:
        base = ClaudeTestBase()

        self.assertEqual(base.MODEL_PROFILE, "claude")
        self.assertIsInstance(base.live_session_runner(), ClaudeLiveSessionRunner)

    def test_claude_flow_instruction_uses_native_tool_names(self) -> None:
        instruction = ClaudeTestBase().flow_execution_instruction(
            workflow_id="solid-review",
            parameters_json='{"target":{"kind":"file","path":"/project/A.swift"}}',
        )

        self.assertIn("Call flow_start", instruction)
        self.assertIn("using flow_next", instruction)

    def test_live_base_prefers_claude_parent_session(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "CLAUDE_CODE_SESSION_ID": "claude-parent",
                "CODEX_THREAD_ID": "codex-parent",
            },
            clear=True,
        ):
            self.assertEqual(CodexTestBase().parent_session_id, "claude-parent")

    def test_live_base_falls_back_to_codex_parent_thread(self) -> None:
        with patch.dict(
            "os.environ",
            {"CODEX_THREAD_ID": "codex-parent"},
            clear=True,
        ):
            self.assertEqual(ClaudeTestBase().parent_session_id, "codex-parent")

    def test_live_base_rejects_missing_parent_session(self) -> None:
        with (
            patch.dict("os.environ", {}, clear=True),
            self.assertRaises(RuntimeError),
        ):
            _ = CodexTestBase().parent_session_id

    def test_flow_base_requires_parent_session_provider(self) -> None:
        with self.assertRaises(TypeError):
            FlowEngineE2ELiveBase()

    def test_local_base_selects_profile(self) -> None:
        self.assertEqual(LocalTestBase.MODEL_PROFILE, "local")


if __name__ == "__main__":
    unittest.main()
