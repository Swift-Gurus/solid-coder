"""Declares the Claude model profile for reusable integration-test contracts."""

from typing import ClassVar

from claude_live_session_runner import ClaudeLiveSessionRunner
from live_session_running import LiveSessionRunning
from live_test_base import LiveTestBase


"""
solid-name: ClaudeTestBase
solid-category: test-support
solid-description: Supplies the Claude model-profile selection shared by live flow-engine and principle health-check integration tests.
"""
class ClaudeTestBase(LiveTestBase):

    MODEL_PROFILE: ClassVar[str] = "claude"
    FLOW_START_TOOL: ClassVar[str] = "flow_start"

    def live_session_runner(self) -> LiveSessionRunning:
        return ClaudeLiveSessionRunner()
