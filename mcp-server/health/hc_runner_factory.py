"""
solid-description: Provides LLM runners adapted to the configured backend.
solid-category: service
solid-tags: [hook]
"""

import sys
from pathlib import Path
from typing import Protocol

_HEALTH_DIR = Path(__file__).resolve().parent
_MCP_DIR = _HEALTH_DIR.parent
for _d in (_MCP_DIR, _HEALTH_DIR, _HEALTH_DIR / 'config', _HEALTH_DIR / 'llm', _HEALTH_DIR / 'codex'):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from hc_checker import ClaudeRunning
from hc_config import llm_backend, llm_host, llm_model, bare_session_timeout, codex_home
from utils.debug_logger import Observing
from runner_strategy_base import RunnerStrategyBase
from claude_runner_strategy import ClaudeRunnerStrategy
from local_runner_strategy import LocalRunnerStrategy
from codex_runner_strategy import CodexRunnerStrategy

_MODEL_PLACEHOLDERS = {"", "claude", "local", "codex"}


class RunnerStrategy(Protocol):
    """Encapsulates runner creation and session-environment setup for one LLM backend."""

    @property
    def session_type(self) -> str: ...

    def apply_env(self) -> None: ...

    def make_runner(
        self,
        mcp_config: str,
        allowed_tools: str,
        session_id: str = "",
        file_path: str = "",
        cwd: str = "",
    ) -> ClaudeRunning: ...


def select_strategy() -> RunnerStrategyBase:
    """Return the configured RunnerStrategy based on [llm] backend in solid-coder-local.toml."""
    backend = llm_backend().lower()
    raw_model = llm_model()
    model = raw_model if raw_model not in _MODEL_PLACEHOLDERS else ""

    if backend == "local":
        return LocalRunnerStrategy(host=llm_host(), model=raw_model)

    if backend == "codex":
        if raw_model.startswith("claude-"):
            raise ValueError(
                f"Model '{raw_model}' is a Claude model and cannot be used with backend='codex'. "
                f"Set an OpenAI-compatible model (e.g. 'gpt-4o') or leave model unset "
                f"to use Codex's default."
            )
        return CodexRunnerStrategy(
            model=model,
            timeout=bare_session_timeout(),
            codex_home_dir=codex_home(),
        )

    return ClaudeRunnerStrategy(model=model)


@Observing("runner.make_llm_runner")
def make_llm_runner(
    mcp_config: str,
    allowed_tools: str,
    session_id: str = "",
    file_path: str = "",
    cwd: str = "",
) -> ClaudeRunning:
    """Backward-compatible shim — delegates to select_strategy().make_runner()."""
    return select_strategy().make_runner(
        mcp_config=mcp_config, allowed_tools=allowed_tools, session_id=session_id, file_path=file_path, cwd=cwd,
    )
