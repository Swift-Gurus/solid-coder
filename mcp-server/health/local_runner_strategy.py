"""
solid-description: Creates health check runners from local configuration.
solid-category: service
solid-tags: [hook]
"""

from hc_checker import ClaudeRunning
from hc_llama_runner import make_llama_server_runner
from runner_strategy_base import RunnerStrategyBase


class LocalRunnerStrategy(RunnerStrategyBase):
    """Runs health checks via a local llama-server instance."""

    def __init__(self, host: str, model: str) -> None:
        self._host = host
        self._model = model

    def make_runner(
        self,
        mcp_config: str,
        allowed_tools: str,
        session_id: str = "",
        file_path: str = "",
        cwd: str = "",
    ) -> ClaudeRunning:
        return make_llama_server_runner(
            host=self._host,
            model=self._model,
            session_id=session_id,
            file_path=file_path,
        )
