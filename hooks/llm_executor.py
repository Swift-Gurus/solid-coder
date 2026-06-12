"""
solid-description: Invokes the LLM session and returns the raw result, logging and re-raising on error.
solid-category: service
solid-tags: [hook, llm]
"""

from pathlib import Path
from typing import Optional, Protocol

from hook_utils import Logging
from claude_runner import ClaudeRunning


class LLMExecuting(Protocol):
    def execute(self, prompt: str, path: str) -> Optional[str]: ...


class LLMExecutor:
    """Invokes the LLM session and returns the raw result. Logs and re-raises on exception."""

    def __init__(self, runner: ClaudeRunning, logger: Logging, timeout: int = 300) -> None:
        self._runner = runner
        self._logger = logger
        self._timeout = timeout

    def execute(self, prompt: str, path: str) -> Optional[str]:
        try:
            return self._runner.run(prompt, timeout=self._timeout)
        except Exception as exc:
            self._logger.log(f"HEALTH_ERR {Path(path).name}: {type(exc).__name__}: {exc}")
            raise
