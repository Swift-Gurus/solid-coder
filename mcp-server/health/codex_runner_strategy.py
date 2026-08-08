"""
solid-description: Runner strategy that creates health-check runners for local execution.
solid-category: service
solid-tags: [hook]
"""

from hc_checker import ClaudeRunning
from runner_strategy_base import RunnerStrategyBase


"""
solid-name: CodexRunnerStrategy
solid-category: service
solid-description: Creates health-check runners for local Codex execution.
solid-tags: [hook, llm]
"""
class CodexRunnerStrategy(RunnerStrategyBase):
    """Runs health checks via a local Codex agent session."""

    def __init__(self, model: str, timeout: int) -> None:
        self._model = model
        self._timeout = timeout

    def make_runner(
        self,
        mcp_config: str,
        allowed_tools: str,
        session_id: str = "",
        file_path: str = "",
        cwd: str = "",
    ) -> ClaudeRunning:
        from hc_codex_runner import make_codex_runner  # noqa: PLC0415
        return make_codex_runner(
            model=self._model,
            timeout=self._timeout,
            cwd=cwd,
            mcp_config=mcp_config,
        )
