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
    FLOW_START_TOOL: ClassVar[str] = "mcp__pipeline__flow_start"

    def live_session_runner(self) -> LiveSessionRunning:
        return CodexLiveSessionRunner()
