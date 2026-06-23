"""
solid-description: Provides LLM backends for health-check sessions.
solid-category: service
solid-tags: [hook]
"""

import os
import sys
from pathlib import Path
from typing import Protocol

_HEALTH_DIR = Path(__file__).resolve().parent
_MCP_DIR = _HEALTH_DIR.parent
for _d in (_MCP_DIR, _HEALTH_DIR, _HEALTH_DIR / 'config', _HEALTH_DIR / 'llm', _HEALTH_DIR / 'codex'):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from hc_checker import ClaudeRunner, ClaudeRunning
from hc_llama_runner import make_llama_server_runner  # noqa: F401 — must be module-level for test patching
from hc_config import llm_backend, llm_host, llm_model, bare_session_timeout, codex_home
from hook_utils import run_claude_bare

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
    ) -> ClaudeRunning: ...


class RunnerStrategyBase:
    """Shared session-type constant and environment setup for all runner strategies."""

    session_type: str = "health_check"

    def apply_env(self) -> None:
        os.environ["SOLID_CODER_SESSION_TYPE"] = self.session_type


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
    ) -> ClaudeRunning:
        return ClaudeRunner(
            mcp_config=mcp_config,
            allowed_tools=allowed_tools,
            fn=run_claude_bare,
            model=self._model,
        )


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
    ) -> ClaudeRunning:
        return make_llama_server_runner(
            host=self._host,
            model=self._model,
            session_id=session_id,
            file_path=file_path,
        )


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
    ) -> ClaudeRunning:
        from hc_codex_runner import make_codex_runner  # noqa: PLC0415
        return make_codex_runner(
            model=self._model,
            timeout=self._timeout,
            codex_home=self._codex_home,
        )


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


def make_llm_runner(
    mcp_config: str,
    allowed_tools: str,
    session_id: str = "",
    file_path: str = "",
) -> ClaudeRunning:
    """Backward-compatible shim — delegates to select_strategy().make_runner()."""
    return select_strategy().make_runner(
        mcp_config=mcp_config,
        allowed_tools=allowed_tools,
        session_id=session_id,
        file_path=file_path,
    )
