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

from claude_live_session_runner import ClaudeLiveSessionRunner  # noqa: E402
from claude_test_base import ClaudeTestBase  # noqa: E402
from codex_live_session_runner import CodexLiveSessionRunner  # noqa: E402
from codex_test_base import CodexTestBase  # noqa: E402
from flow_engine.flow_engine_e2e_live_base import FlowEngineE2ELiveBase  # noqa: E402
from local_test_base import LocalTestBase  # noqa: E402


class TestModelProfileTestBases(unittest.TestCase):

    def test_codex_base_selects_profile_and_runner(self) -> None:
        base = CodexTestBase()

        self.assertEqual(base.MODEL_PROFILE, "codex")
        self.assertIsInstance(base.live_session_runner(), CodexLiveSessionRunner)

    def test_claude_base_selects_profile_and_runner(self) -> None:
        base = ClaudeTestBase()

        self.assertEqual(base.MODEL_PROFILE, "claude")
        self.assertIsInstance(base.live_session_runner(), ClaudeLiveSessionRunner)

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
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(RuntimeError):
                CodexTestBase().parent_session_id

    def test_flow_base_requires_parent_session_provider(self) -> None:
        with self.assertRaises(TypeError):
            FlowEngineE2ELiveBase()

    def test_local_base_selects_profile(self) -> None:
        self.assertEqual(LocalTestBase.MODEL_PROFILE, "local")


if __name__ == "__main__":
    unittest.main()
