"""
solid-description: Runner strategy that creates health-check runners for local execution.
solid-category: service
solid-tags: [hook]
"""

from hc_checker import ClaudeRunning
from runner_strategy_base import RunnerStrategyBase


class CodexRunnerStrategy(RunnerStrategyBase):
    """Runs health checks via a local Codex agent session."""

    def __init__(self, model: str, timeout: int, codex_home_dir: str) -> None:
        self._model = model
        self._timeout = timeout
        self._codex_home = codex_home_dir

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
            codex_home=self._codex_home,
            cwd=cwd,
        )