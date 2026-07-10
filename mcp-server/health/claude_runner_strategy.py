"""
solid-description: Strategy for creating Claude-based runners.
solid-category: service
solid-tags: [hook]
"""

from hc_checker import ClaudeRunner, ClaudeRunning
from hook_utils import run_claude_bare
from runner_strategy_base import RunnerStrategyBase


class ClaudeRunnerStrategy(RunnerStrategyBase):
    """Runs health checks via claude -p bare sessions."""

    def __init__(self, model: str = "") -> None:
        self._model = model

    def make_runner(
        self,
        mcp_config: str,
        allowed_tools: str,
        session_id: str = "",
        file_path: str = "",
        cwd: str = "",
    ) -> ClaudeRunning:
        return ClaudeRunner(
            mcp_config=mcp_config,
            allowed_tools=allowed_tools,
            fn=run_claude_bare,
            model=self._model,
            cwd=cwd,
        )
