"""
solid-description: Provides LLM runners adapted to the configured backend.
solid-category: service
solid-tags: [hook]
"""

import sys
from collections.abc import Callable
from pathlib import Path

_HEALTH_DIR = Path(__file__).resolve().parent
_MCP_DIR = _HEALTH_DIR.parent
for _d in (
    _MCP_DIR,
    _HEALTH_DIR,
    _HEALTH_DIR / "config",
    _HEALTH_DIR / "llm",
    _HEALTH_DIR / "codex",
):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import hc_config
from claude_runner_strategy import ClaudeRunnerStrategy
from codex_runner_strategy import CodexRunnerStrategy
from hc_checker import ClaudeRunning
from local_runner_strategy import LocalRunnerStrategy
from runner_strategy_base import RunnerStrategyBase
from utils.debug_logger import Observing

_MODEL_PLACEHOLDERS = {"", "claude", "local", "codex"}


def _resolved_model(raw_model: str) -> str:
    return raw_model if raw_model not in _MODEL_PLACEHOLDERS else ""


def _make_local_strategy(llm) -> RunnerStrategyBase:
    return LocalRunnerStrategy(host=llm.host, model=llm.model)


def _make_codex_strategy(llm) -> RunnerStrategyBase:
    raw_model = llm.model
    if raw_model.startswith("claude-"):
        raise ValueError(
            f"Model '{raw_model}' is a Claude model and cannot be used with backend='codex'. "
            f"Set an OpenAI-compatible model (e.g. 'gpt-4o') or leave model unset "
            f"to use Codex's default."
        )
    return CodexRunnerStrategy(
        model=_resolved_model(raw_model),
        timeout=llm.timeout,
    )


def _make_claude_strategy(llm) -> RunnerStrategyBase:
    return ClaudeRunnerStrategy(model=_resolved_model(llm.model))


_STRATEGY_FACTORIES = {
    "local": _make_local_strategy,
    "codex": _make_codex_strategy,
}


def select_strategy(config_loader: Callable | None = None) -> RunnerStrategyBase:
    """Return the configured RunnerStrategy based on [llm] backend in solid-coder-local.toml.

    config_loader defaults to the configuration loader's load method, resolved at call time so
    tests can patch the loader or inject a fake loading operation directly.
    """
    loader = config_loader or hc_config.SolidCoderConfigLoader().load
    llm = loader().llm
    factory = _STRATEGY_FACTORIES.get(llm.backend.lower(), _make_claude_strategy)
    return factory(llm)


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
        mcp_config=mcp_config,
        allowed_tools=allowed_tools,
        session_id=session_id,
        file_path=file_path,
        cwd=cwd,
    )
